# Metagenomic protein database connector

Read access to the clustered metagenomic protein collection — the same data
the census drew 198,290 clusters from (paper). Use it for neighborhood
extraction, cluster membership, and biosample context. All queries are
read-only from a session.

## Schema

| Table | Key contents |
| --- | --- |
| `clusters` | cluster_id, representative protein_id, member count, size stats |
| `proteins` | protein_id, cluster_id, contig_id, aa sequence, length |
| `contigs` | contig_id, biosample_id, length, circular flag |
| `coordinates` | protein_id, contig_id, start, end, strand |
| `biosamples` | biosample_id, biome/sample metadata, study id |
| `pfam` | protein_id, pfam_id, pfam_name, evalue, envelope coords |

GAP: table/column names are our reconstruction — the paper describes the
connector's role, not its schema.

## Core queries

- Cluster membership: `SELECT protein_id FROM proteins WHERE cluster_id = ?`
  — always expand through `proteins`, never assume the representative stands
  for all members.
- Locus proteins: join `coordinates` to `proteins` on contig_id, ordered by
  start — this is the input to neighborhood analysis.
- Biosample of a locus: `contigs.biosample_id -> biosamples` — needed for
  the independence count.
- Pfam for a protein set: one batched query on `pfam` by protein_id list;
  do not query per protein in a loop.

## Neighborhood extraction

1. Locate the RT protein's contig and coordinates.
2. Pull all proteins on that contig within the requested flank (default the
   figure window: 10 kb each side, GAP).
3. Attach strand, cluster_id, and Pfam hits to each neighbor in one pass.
4. Respect the circular flag: wrap the window across the origin when set.

## Pitfalls

- Cluster ids are the unit of independence, not protein ids; count loci via
  distinct contig_id, never via protein_id.
- Coordinates are 1-based inclusive. GAP: confirm against a known locus
  before bulk extraction — an off-by-one corrupts every distance downstream.
- Some proteins lack Pfam rows; a missing row means "no hit recorded", not
  "searched and negative" — say which in the report.
