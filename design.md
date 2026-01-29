# System Design: G2P Portal Agent

This document outlines the architectural philosophy, agent roles, and systematic thinking behind the G2P Portal Multi-Agent System.

## 1. Architectural Philosophy

### Why Multi-Agent?
In complex biological domains, a single "generalist" LLM often struggles with context pollution—confusing a protein's structural domain with a gene's clinical domain. By splitting the system into specialized agents, we achieve:
*   **Separation of Concerns**: Each agent has a focused prompt and a limited, safe toolset.
*   **Reduced Hallucinations**: A structural agent simply *cannot* invent clinical data because it lacks the tools to query ClinVar.
*   **Modular Scalability**: We can upgrade the "Variant Analyst" without breaking the "Genetic Discovery" logic.

### The Pattern: Orchestrator-Workers
We employ a **Hub-and-Spoke** model:
1.  **Router (Hub)**: Evaluates user intent and routes to a specialist.
2.  **Specialists (Spokes)**: Execute the work using strict protocols and return the result.
3.  **Router**: Synthesizes the final answer (or the specialist answers directly in our streaming model).

---

## 2. Agent Roles & Responsibilities

### 🚦 The Orchestrator (Router Agent)
*   **Role**: The "Front Desk". It does not solve problems; it directs traffic.
*   **Responsibilities**:
    *   Classifying intent (Discovery vs. Structure vs. Clinical).
    *   Handling "Off-topic" queries (e.g., "What is the weather?").
*   **Why it exists**: To prevent the expensive/specialist agents from wasting cycles on irrelevant queries.
*   **Alternatives Considered**:
    *   *Single Giant Prompt*: Rejected. Too hard to maintain and prone to "forgetting" instructions.
    *   *Auto-GPT Loop*: Rejected. Too unpredictable for a scientific tool requiring strict accuracy.

### 🧬 Genetic Discovery Agent (The Librarian)
*   **Role**: Entity Resolution and Metadata Retrieval.
*   **Responsibilities**:
    *   Mapping vague terms ("autism gene") to precise symbols (**SHANK3**).
    *   Providing the "Identity Card" (HGNC, UniProt, GenCC).
    *   **New**: Reverse lookups (PDB/UniProt -> Gene).
*   **Key Tools**:
    *   `search_gene_index`: Fuzzy search (now supports UniProt/Description).
    *   `get_gene_dossier`: Retrieving canonical metadata.
    *   `lookup_gene_by_pdb`: Reverse mapping.
*   **What it CANNOT do**:
    *   It cannot visualize 3D structures.
    *   It cannot interpret variant pathogenicity (it only finds the gene).

### 🏗️ Structural Biologist Agent (The Architect)
*   **Role**: Physical Visualization.
*   **Responsibilities**:
    *   Mapping linear sequence to 3D space (Domains, Active Sites).
    *   Assessing coverage (PDB vs. AlphaFold).
*   **Key Tools**:
    *   `get_protein_features`: Retrieving pre-computed domains.
    *   `get_structure_map`: Check PDB coverage.
    *   `run_python_analysis`: Calculating 3D distances or correlations.
*   **Why `run_python_analysis`?**: LLMs are bad at geometry. We use Python to calculate distances ($$\sqrt{(x_2-x_1)^2...}$$) accurately.
*   **What it CANNOT do**:
    *   It cannot predict *new* folds (it only reads pre-computed AlphaFold/PDB data).
    *   It cannot perform molecular dynamics simulations.

### 🩺 Variant Analyst Agent (The Clinician)
*   **Role**: Impact Assessment.
*   **Responsibilities**:
    *   Mapping user input (p.H23Q) to the Canonical Isoform.
    *   Checking Clinical Significance (ClinVar).
    *   Checking Population Frequency (gnomAD).
*   **Key Tools**:
    *   `map_variant_to_canonical`: Critical constraints. Users often cite variants on the wrong isoform; this tool aligns them to the "Source of Truth" (Canonical).
    *   `check_clinvar_status`: Retrieving known pathogenicity.
*   **What it CANNOT do**:
    *   It cannot *diagnose* a patient. It provides evidence, not medical advice.
    *   It cannot predict pathogenicity for novel variants (unless using a specific predictor tool, which is not yet integrated).

---

## 3. Systematic Thinking & Transparency

### Decision Making
We enforce **Radical Transparency** through our prompt engineering:
*   **Rationale**: Agents must explain *why* they picked a tool ("I chose fuzzy search because exact match failed").
*   **Alternatives**: Agents must state what they *ignored* ("Skipped AlphaFold as PDB data was sufficient").

### The "Computational Analyst" Pattern
We intentionally separate **Data Retrieval** (API calls) from **Data Analysis** (Python).
*   **Problem**: An API might return a 2,000-row TSV of mutations. An LLM's context window gets flooded, leading to "lazy" answers.
*   **Solution**: The Agent treats the data as a *file* and writes Python code (`pandas`) to filter it.
    *   *User*: "Count pathogenic variants."
    *   *Agent*: `df[df['ClinVar'] == 'Pathogenic'].shape[0]`
*   **Benefit**: Deterministic, mathematically correct answers every time.

---

## 4. Future Considerations
*   **Vector Search**: Currently, we use fuzzy text search. Implementing vector embeddings for gene descriptions would allow semantic search (e.g., "Genes involved in lipid metabolism" -> LDLR, APOB).
*   **Real-time Alignment**: The current `align_isoforms` is a static lookup. Integrating a real-time Smith-Waterman aligner would handle custom sequences.

---

## 5. Tools & Endpoints Reference

Below is the definitive list of tools available to the agents and their corresponding backend API endpoints.

| Tool Name | Agent | Description | API Endpoint |
| :--- | :--- | :--- | :--- |
| `search_gene_index` | 🧬 Discovery | Fuzzy searches for genes/proteins (Symbol, Name, UniProt). | `GET /api/v2.0/genes/options` |
| `get_gene_dossier` | 🧬 Discovery | Retrieves canonical metadata (HGNC, UniProt, GenCC). | `GET /api/gene/:geneName` |
| `lookup_gene_by_pdb` | 🧬 Discovery | Reverse lookup: Finds gene/protein for a PDB ID. | `GET /api/genes/pdb/:pdbId` |
| `get_protein_features` | 🏗️ Structure | Retrieves functional domains, active sites, and PTMs. | `GET /api/gene/:gene/protein/:id/protein-features` |
| `get_structure_map` | 🏗️ Structure | Maps sequence residues to PDB structures. | `GET /api/gene/:gene/protein/:id/gene-transcript-protein-isoform-structure-map` |
| `fetch_alphafold_access` | 🏗️ Structure | Gets access token for AlphaFold 3 models. | `GET /api/af3StructureByUniProtId/:id` |
| `map_variant_to_canonical` | 🩺 Variant | Maps isoform-specific variants to the canonical sequence. | `POST /api/gene/:gene/isoform/:isoformId/variant-map` |
| `check_clinvar_status` | 🩺 Variant | Checks for known pathogenic entries at a position. | *(Derived from `get_protein_features`)* |
| `align_isoforms` | 🩺 Variant | Aligns two isoforms to see splicing differences. | `GET /api/gene/:gene/protein/:iso1/:iso2/alignment` |
| `fetch_pdb_file` | 🏗️ Structure | Internally downloads PDB file content for analysis. | `https://files.rcsb.org/download/{pdb_id}.pdb` |
| `run_python_analysis` | *All* | Sandboxed Python environment for data processing. | *(Internal Orchestrator Skill)* |

