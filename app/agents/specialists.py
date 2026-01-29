from .prompts import DISCOVERY_AGENT_PROMPT, STRUCTURE_AGENT_PROMPT, VARIANT_AGENT_PROMPT
from app.tools.definitions import (
    search_gene_index, get_gene_dossier,
    get_protein_features, get_structure_map, fetch_alphafold_access,
    map_variant_to_canonical, check_clinvar_status, align_isoforms,
    run_python_analysis, fetch_pdb_file, lookup_gene_by_pdb
)
from app.tools.feedback import (
    record_user_preference, suggest_global_improvement, get_user_preferences
)

# Define sub-agents
genetic_discovery_agent = {
    "name": "genetic-discovery-agent",
    "description": "Responsible for identifying valid genes, retrieving metadata, and understanding disease associations.",
    "system_prompt": DISCOVERY_AGENT_PROMPT,
    "tools": [search_gene_index, get_gene_dossier, lookup_gene_by_pdb, run_python_analysis],
}

structural_biology_agent = {
    "name": "structural-biology-agent",
    "description": "Expert in protein structure, domains, and PTMs. Uses PDB and AlphaFold models.",
    "system_prompt": STRUCTURE_AGENT_PROMPT,
    "tools": [get_protein_features, get_structure_map, fetch_alphafold_access, run_python_analysis, fetch_pdb_file],
}

variant_analyst_agent = {
    "name": "variant-analyst-agent",
    "description": "Analyzes specific mutations (e.g., p.H23Q), mapping them to structure and clinical significance.",
    "system_prompt": VARIANT_AGENT_PROMPT,
    "tools": [map_variant_to_canonical, check_clinvar_status, align_isoforms, run_python_analysis],
}
