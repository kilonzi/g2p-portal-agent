# G2P Portal MCP Tools Reference

This document provides a comprehensive technical specification for the Model Context Protocol (MCP) tools available to the multi-agent system. It is designed to bridge the gap between raw API outputs and scientific interpretation.

---

## 1. Discovery Tools
**Primary User:** 🧬 `Genetic Discovery Agent`

### `search_gene_index`
*   **Description**: The entry point for the portal. It fuzzily searches the internal index of Genes and Proteins.
*   **Endpoint**: `GET /api/v2.0/genes/options`
*   **Why use it?**: To validate if a gene symbol exists in G2P or to find a gene based on a protein name (e.g., "LDL Receptor" -> "LDLR").
*   **scientific Interpretation**:
    *   **"label"**: The HGNC Symbol (e.g., `LDLR`). This is the *Identifier* you must use for all subsequent calls.
    *   **"value"**: The internal ID (usually matching label).
    *   *Note*: If a user queries a synonym (e.g., "HER2"), this tool resolves it to the official symbol (`ERBB2`).

### `get_gene_dossier`
*   **Description**: Retrieves the "Identity Card" for a gene.
*   **Endpoint**: `GET /api/gene/:geneName`
*   **Why use it?**: To establish the **Canonical Isoform** and check **Disease Validity**.
*   **Scientific Interpretation**:
    *   **`uniprot_id`**: The canonical protein accession (e.g., `P01130`). *Crucial*: All positions (e.g., "Residue 123") in literature usually refer to this specific sequence.
    *   **`gencc_classification`**: The strength of evidence linking this gene to a disease (e.g., "Definitive", "Strong", "Limited").
        *   *Scientist Note*: If validity is "Limited", advise the user to interpret variants with caution, as the gene-disease link is not fully proven.

---

## 2. Structural Biology Visualizer Tools
**Primary User:** 🧬 `Structural Biologist Agent`

### `get_protein_features`
*   **Description**: The "Heavy Lifter". Returns the complete, aggregated JSON of functional annotations used by the Protein Feature Viewer.
*   **Endpoint**: `GET /api/gene/:gene/protein/:id/protein-features`
*   **Why use it?**: To identify domains, active sites, PTMs, and structural regions.
*   **Scientific Interpretation**:
    *   **Data Structure**: **Returns a TSV (Tab Separated Values) string**, not JSON.
        *   **Rows**: Residues (1, 2, 3...)
        *   **Columns**: Feature names (e.g., `PfMA: LDL-receptor class B`, `Site: Active site`, `ClinVar: Pathogenic`).
    *   **`pfam_domain`**: High-confidence functional blocks. *Example*: "Residues 50-100 form a PHD zinc finger."
    *   **`active_site`**: Critical residues for catalysis. *Example*: "Asp102 is the catalytic triad nucleophile."
    *   **`disulfide_bond`**: Cysteine pairs (e.g., "Cys45-Cys90"). *Crucial*: Mutating either Cys usually destabilizes the protein.
    *   **`structure_coverage`**: If column `7k4y_A` has data, it means PDB structure `7K4Y` chain `A` covers this region.

### `get_structure_map`
*   **Description**: Maps the linear protein sequence to available 3D experimental structures (PDB).
*   **Endpoint**: `GET /api/gene/:gene/protein/:id/gene-transcript-protein-isoform-structure-map`
*   **Why use it?**: To find *which* PDB file serves as the best template for modeling a mutation.
*   **Scientific Interpretation**:
    *   **`coverage`**: The % of the protein covered by the structure. Prefer high coverage (>80%).
    *   **`resolution`**: Angstroms (Å). Lower is better (e.g., 1.5Å > 3.0Å).
    *   **`method`**: "X-ray" vs "NMR" vs "EM".
    *   *Advice*: If PDB coverage is poor, the agent should recommend fetching the AlphaFold model instead.

### `fetch_alphafold_access`
*   **Description**: **[Auth Required]** Generates a signed URL to download the full AlphaFold 3 (AF3) prediction model (CIF format).
*   **Endpoint**: `GET /api/af3StructureByUniProtId/:uniprotId`
*   **Why use it?**: When no experimental PDB structure exists, or to see "disordered" regions (low pLDDT).
*   **Scientific Interpretation**:
    *   **`pLDDT`**: Confidence score (0-100).
        *   **>90**: Very high confidence (like a crystal structure).
        *   **<50**: Disordered/Unstructured. *Crucial*: Variants in disordered regions often have less structural impact unless they create aggregation.

---

## 3. Variant Analysis Tools
**Primary User:** 🩺 `Variant Analyst Agent`

### `map_variant_to_canonical`
*   **Description**: Maps a variant from a specific transcript/isoform to the canonical reference sequence.
*   **Endpoint**: `POST /api/gene/:gene/isoform/:isoformId/variant-map`
*   **Why use it?**: Users often submit variants based on an "old paper" or a specific isoform. This normalizes everything to the portal's master coordinate system.
*   **Scientific Interpretation**:
    *   **Input**: `HGVSp` (e.g., `p.H23Q`) or Genomic coordinates.
    *   **Output**: The resulting position on the Canonical Isoform.
    *   *Warning*: If the variant falls in an intron or UTR instructions, the tool will flag it as "Non-coding".

### `check_clinvar_status`
*   **Description**: Checks if a specific position has known pathogenic entries in ClinVar.
*   **Endpoint**: (Derived from `get_protein_features` data source `ClinVar`)
*   **Why use it?**: To provide clinical precedence. "Has this exact mutation been seen in patients before?"
*   **Scientific Interpretation**:
    *   **`Pathogenic` / `Likely Pathogenic`**: Clinical evidence supports disease causation.
    *   **`VUS` (Variant of Uncertain Significance)**: Found in patients, but not proven to cause disease.
    *   **`Benign`**: Common in healthy populations or proven harmless.

### `align_isoforms`
*   **Description**: Aligns the sequence of two different isoforms.
*   **Endpoint**: `GET /api/gene/:gene/protein/:iso1/:iso2/alignment`
*   **Why use it?**: To see if a critical exon (and its variants) is spliced out in a different tissue-specific isoform.
*   **Scientific Interpretation**:
    *   **Gap (`-`)**: The sequence is missing in one isoform.
    *   *Insight*: "The mutation H23Q exists in the Brain isoform but is spliced out in the Heart isoform, suggesting tissue-specific pathology."
