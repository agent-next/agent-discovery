# GPU dispatch (structure prediction queue)

The analysis sandbox has no GPU — 60 CPU cores, 192 GiB RAM (paper).
Structure prediction runs on a separate GPU queue. Submit, continue working,
collect later; a session must never block waiting on a GPU job.

## Model choice

| Job type | When to use | Notes |
| --- | --- | --- |
| `esmfold_v1` | Single-chain screening; hundreds of ORFs; quick fold hypothesis | Fast, no MSA needed; lower confidence on shallow families |
| `colabfold alphafold2_ptm` | Final structure for a claim; partner/domain of interest | 5 models, 3 recycles (GAP: reproduction defaults); needs or builds an MSA |

Rule of thumb: ESMFold for breadth, AF2_ptm for the structures a figure or a
Foldseek conclusion will rest on. GAP: the paper supplies predicted
structures for the benchmark loci (1,131 for 96 loci) but does not publish
the inference settings.

## Hardware targets

- A100: AF2_ptm multimers, long sequences, deep MSAs.
- L4: ESMFold single chains, short AF2_ptm monomers.
- Pick the smallest target that fits; oversized requests queue behind other
  campaigns. GAP: target names/quota.

## Workflow

1. `submit` — FASTA(s) + model tag + target; returns a job id. Record the id
   in the task notes immediately.
2. `status <job_id>` — poll when convenient, never in a wait loop.
3. `collect <job_id>` — fetch PDB/mmCIF plus confidence metrics; check
   pLDDT/PAE before citing the structure.

## Discipline

- Batch submit all ORFs you will need up front; per-gene round trips waste
  queue position.
- While jobs run, do sequence-side work (HMM, neighborhood, arrays). Come
  back for structures.
- If a job fails or the queue is full, report which ORFs lack structures and
  proceed on sequence evidence — do not stall the task on GPU availability.
- In benchmark levels where structures are provided as inputs (L4+), search
  the provided set before submitting anything.
