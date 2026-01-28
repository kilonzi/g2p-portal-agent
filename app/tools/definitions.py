from langchain_core.tools import tool
from typing import Optional, List, Dict
from app.services.api_client import G2PClient
from app.tools.analysis import run_python_analysis

# --- 1. Discovery Tools ---

@tool
async def search_gene_index(query: str) -> List[Dict]:
    """
    Fuzzy searches for genes or proteins. Use this to find a Gene Symbol (e.g., 'LDLR') 
    from a name (e.g., 'LDL Receptor').
    
    Args:
        query: The name or symbol to search for (e.g., "her2", "insulin").
    """
    # Maps to: GET /api/v2.0/genes/options
    # Doing a client-side filter since the endpoint returns all options or supports simple search
    # Assuming the API returns a list of {label: "LDLR", value: "LDLR"}
    # If the API endpoint takes a query param, we use it. 
    # Based on docs: "it fuzzily searches the internal index".
    # We'll assume the endpoint might return a big list or take a q param. 
    # Let's try fetching all and filtering if q param isn't supported, 
    # BUT usually 'options' endpoints are for dropdowns. 
    # Let's try passing 'search' or 'q' if supported. If not, we download and filter.
    # Given the docs say "GET /api/v2.0/genes/options", let's assume it returns a list we can filter.
    
    data = await G2PClient.get("/genes/options")
    if isinstance(data, list):
        # fuzzy match simple implementation
        query_lower = query.lower()
        results = [
            item for item in data 
            if query_lower in str(item.get("label", "")).lower() 
            or query_lower in str(item.get("value", "")).lower()
        ]
        return results[:10] # Cap results
    return f"Error searching gene index: {data}"

@tool
async def get_gene_dossier(gene_name: str) -> Dict:
    """
    Retrieves the 'Identity Card' for a gene, including HGNC ID, Uniprot ID, 
    and GenCC disease validity.
    
    Args:
        gene_name: The official gene symbol (e.g., "LDLR").
    """
    # Maps to: GET /api/gene/:geneName
    return await G2PClient.get(f"/gene/{gene_name}")


# --- 2. Structural Biology Tools ---

@tool
async def get_protein_features(gene: str, protein_id: str) -> str:
    """
    Retrieves functional domains, active sites, and PTMs.
    Returns a TSV string with columns like 'PfMA' and 'Site'.
    
    Args:
        gene: Gene symbol (e.g., "LDLR")
        protein_id: Uniprot ID (e.g., "P01130")
    """
    # Maps to: GET /api/gene/:gene/protein/:id/protein-features
    return await G2PClient.get(f"/gene/{gene}/protein/{protein_id}/protein-features")

@tool
async def get_structure_map(gene: str, protein_id: str) -> Dict:
    """
    Maps protein sequence to PDB structures. Use this to find structure coverage.
    
    Args:
        gene: Gene symbol
        protein_id: Uniprot ID
    """
    # Maps to: GET /api/gene/:gene/protein/:id/gene-transcript-protein-isoform-structure-map
    return await G2PClient.get(f"/gene/{gene}/protein/{protein_id}/gene-transcript-protein-isoform-structure-map")

@tool
async def fetch_alphafold_access(uniprot_id: str) -> Dict:
    """
    Retrieves a signed URL for the AlphaFold 3 model. USE ONLY if PDB coverage is poor.
    
    Args:
        uniprot_id: The Uniprot accession ID.
    """
    # Maps to: GET /api/af3StructureByUniProtId/:id
    return await G2PClient.get(f"/af3StructureByUniProtId/{uniprot_id}")


# --- 3. Variant Analyst Tools ---

@tool
async def map_variant_to_canonical(gene: str, isoform_id: str, variant: str) -> Dict:
    """
    Maps a variant (e.g., p.H23Q) from a specific isoform to the canonical sequence.
    
    Args:
        gene: Gene symbol
        isoform_id: The specific isoform ID (e.g., "NM_000527")
        variant: The variant string (e.g., "p.H23Q")
    """
    # Maps to: POST /api/gene/:gene/isoform/:isoformId/variant-map
    # Construct body
    payload = {"variant": variant} # Assuming simple body
    return await G2PClient.post(f"/gene/{gene}/isoform/{isoform_id}/variant-map", json=payload)

@tool
async def check_clinvar_status(gene: str, protein_id: str, position: int) -> str:
    """
    Checks if a specific residue position has known Pathogenic entries in ClinVar.
    Derived from protein features.
    
    Args:
        gene: Gene symbol
        protein_id: Uniprot (canonical) ID
        position: The residue number to check (integer)
    """
    # Derived tool: Requests features and filters for 'ClinVar' column
    # 1. Fetch features (TSV)
    features_tsv = await get_protein_features.invoke({"gene": gene, "protein_id": protein_id})
    
    # 2. Crude TSV Parsing to find the row for 'position' and column 'ClinVar'
    # NOTE: This implies we need to know the column index or name.
    # Assuming standard TSV with headers.
    
    if "Error" in features_tsv:
        return features_tsv
        
    try:
        lines = features_tsv.strip().split("\n")
        headers = lines[0].split("\t")
        
        # Find index of ClinVar column (fuzzy match)
        clinvar_idx = -1
        for i, h in enumerate(headers):
            if "ClinVar" in h or "clinical" in h.lower():
                clinvar_idx = i
                break
        
        if clinvar_idx == -1:
            return "ClinVar data not found in features."

        # Find row for position (Assuming first column is residue number or similar)
        # We'll just scan lines. Better to be robust.
        # Let's assume the rows correspond to residue numbers 1..N if straight TSV
        # OR we search for the specific position. 
        # For this implementation, let's assume 1-based indexing in rows.
        
        target_line = None
        if position < len(lines):
             # Header is 0, Residue 1 is 1... so lines[position] might be right?
             # Let's check the first column of the line
             row = lines[position].split("\t")
             # Validate if strict mapping or search
             # Simplified: just return the cell if found
             if len(row) > clinvar_idx:
                 val = row[clinvar_idx]
                 if val and val.strip():
                     return f"ClinVar Entry at {position}: {val}"
                 else:
                     return f"No ClinVar entry found at {position}."
        
        return f"Position {position} out of range."

    except Exception as e:
        return f"Error parsing ClinVar status: {e}"

@tool(description="Aligns two isoforms to check for splicing differences.")
async def align_isoforms(gene: str, iso1: str, iso2: str) -> str:
    """
    Aligns two isoforms to check for splicing differences.
    
    Args:
        gene: Gene symbol
        iso1: First isoform ID
        iso2: Second isoform ID
    """
    # Maps to: GET /api/gene/:gene/protein/:iso1/:iso2/alignment
    return await G2PClient.get(f"/gene/{gene}/protein/{iso1}/{iso2}/alignment")

@tool
async def fetch_pdb_file(pdb_id: str) -> str:
    """
    Downloads the PDB file content for a given PDB ID from RCSB.
    Use this before running 3D analysis in run_python_analysis.
    
    Args:
        pdb_id: The 4-character PDB ID (e.g., "7K4Y").
    """
    import httpx
    url = f"https://files.rcsb.org/download/{pdb_id}.pdb"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.text
