import random

import pytest

from artharness import arrays
from artharness.arrays import delimit_array, kmer_scan, mononucleotide_shuffles

REPEAT = "CATGTGTATCGCATGT"  # 16-nt repeat observed by the worker in task t0062
SPACER = 120  # within the paper's 100-450 nt regular-spacing window


def synth_array_window(copies: int = 14, mismatches: int = 1, spacer: int = SPACER,
                       seed: int = 7) -> str:
    rng = random.Random(seed)
    parts = []
    for _i in range(copies):
        seq = list(REPEAT)
        for pos in rng.sample(range(len(REPEAT)), mismatches):
            seq[pos] = rng.choice([b for b in "ACGT" if b != seq[pos]])
        parts.append("".join(seq))
        parts.append("".join(rng.choice("ACGT") for _ in range(spacer)))
    return "".join(parts)


def test_kmer_scan_calls_array_on_synthetic_locus():
    window = synth_array_window()
    call = kmer_scan("L_test", window, random.Random(0))
    assert call.status == "array"
    assert call.R == 14
    assert call.seed is not None and len(call.seed) == 14
    assert len(call.copies) == 14


def test_kmer_scan_rejects_shuffled_window():
    window = synth_array_window()
    shuffled = mononucleotide_shuffles(window, 1, random.Random(1))[0]
    call = kmer_scan("L_shuf", shuffled, random.Random(0))
    assert call.status == "no_array"


def test_short_upstream_is_not_assessed():
    window = synth_array_window(copies=2)  # too few copies to call
    call = kmer_scan("L_short", window[:900], random.Random(0))
    assert call.status == "not_assessed"


def test_homopolymer_and_low_complexity_seeds_excluded():
    from artharness.arrays import _seed_ok

    assert not _seed_ok("AAAAAAAAAAAAAA")
    assert not _seed_ok("ACACACACACACAC")  # only 2 distinct bases
    assert _seed_ok(REPEAT[:14])


def test_delimit_recovers_copies_and_repeat():
    rng = random.Random(2)
    window = synth_array_window(mismatches=1)
    # shrink the shuffle counts for test speed (constants are module-level on purpose)
    orig = (arrays.N_SHUFFLES_DELIMIT, arrays.N_SHUFFLES_DELIMIT_RETEST)
    arrays.N_SHUFFLES_DELIMIT, arrays.N_SHUFFLES_DELIMIT_RETEST = 4, 8
    try:
        arr = delimit_array("L_test", window, rng)
    finally:
        arrays.N_SHUFFLES_DELIMIT, arrays.N_SHUFFLES_DELIMIT_RETEST = orig
    assert arr is not None
    assert len(arr.copy_starts) == 14
    assert all(60 <= s <= 600 for s in arr.spacings)
    # consensus repeat must be a 10-mer close to some 10-mer of the planted repeat
    # (any of the 7 recurring seed offsets, not necessarily offset 0)
    assert len(arr.repeat) == 10
    best_mm = min(sum(a != b for a, b in zip(arr.repeat, REPEAT[o:o + 10], strict=False))
                  for o in range(7))
    assert best_mm <= 1


def test_delimit_rejects_random_window():
    rng = random.Random(3)
    window = "".join(rng.choice("ACGT") for _ in range(6000))
    orig = (arrays.N_SHUFFLES_DELIMIT, arrays.N_SHUFFLES_DELIMIT_RETEST)
    arrays.N_SHUFFLES_DELIMIT, arrays.N_SHUFFLES_DELIMIT_RETEST = 4, 8
    try:
        assert delimit_array("L_rand", window, rng) is None
    finally:
        arrays.N_SHUFFLES_DELIMIT, arrays.N_SHUFFLES_DELIMIT_RETEST = orig


def test_paper_anchor_sequence_is_found():
    # the t0062 worker read a 2,900-nt flank of locus L0050 whose copies carry
    # <=1 mismatch against CATGTGT[AT]TCGCATGT (paper p.30-31, Methods)
    flank = synth_array_window(copies=14, mismatches=1, spacer=117, seed=11)[:2900]
    call = kmer_scan("L0050", flank, random.Random(4))
    assert call.status == "array"
    assert pytest.approx(call.R, abs=2) == 14
