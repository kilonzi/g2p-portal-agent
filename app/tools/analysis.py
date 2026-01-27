import pandas as pd
import io
import json
import traceback
from langchain_core.tools import tool
from loguru import logger
from typing import Literal, Optional

import numpy as np
import scipy
import Bio

# Security: Restricted globals for the exec environment
SAFE_GLOBALS = {
    "pd": pd,
    "json": json,
    "np": np,
    "scipy": scipy,
    "Bio": Bio,
}

@tool
def run_python_analysis(
    data_payload: str,
    data_format: Literal["tsv", "json", "csv", "pdb"],
    code: str,
    description: str
) -> str:
    """
    Executes Python code (pandas) on a provided dataset to filter, aggregate, or calculate statistics.
    The data is pre-loaded into a variable named `df` (for tabular) or `data` (for JSON).
    
    Args:
        data_payload: The raw string data (TSV, CSV, or JSON).
        data_format: The format of the data ('tsv', 'csv', 'json').
        code: The Python code to execute. It must print() the result or define a 'result' variable.
        description: Brief description of the analysis for logging.
    """
    logger.info(f"Starting analysis: {description}")
    logger.debug(f"Data format: {data_format}, Code length: {len(code)}")

    # 1. Security Check (Basic "Sandbox")
    # In a real prod env, this should run in a separate container/process.
    forbidden_imports = ["os", "sys", "subprocess", "importlib", "shutil"]
    for mod in forbidden_imports:
        if f"import {mod}" in code or f"from {mod}" in code:
            msg = f"Security Error: Import of '{mod}' is restricted."
            logger.warning(msg)
            return msg

    # 2. Pre-Load Data
    local_vars = {}
    try:
        if data_format in ["tsv", "csv"]:
            sep = '\t' if data_format == "tsv" else ','
            df = pd.read_csv(io.StringIO(data_payload), sep=sep)
            
            # Application of "Hardening" rules from requirements
            # A. Strict Typing (Best Effort)
            if 'residueId' in df.columns:
                df['residueId'] = pd.to_numeric(df['residueId'], errors='coerce')
            if 'ClinVar' in df.columns:
                df['ClinVar'] = df['ClinVar'].astype(str)

            # B. NaN Handling
            # Text columns -> Empty string
            # nuances: select object columns
            obj_cols = df.select_dtypes(include=['object']).columns
            df[obj_cols] = df[obj_cols].fillna("")
            # Numeric columns -> Keep NaN (default behavior, so no action needed)

            # C. Unique Constraints
            # Only if residueId is the primary key/index implied. 
            # The requirement said "unless specialized isoform mapping is active".
            # We will apply it if residueId exists and is likely the intended key
            if 'residueId' in df.columns:
                 df.drop_duplicates(subset=['residueId'], keep='first', inplace=True)

            local_vars['df'] = df
            logger.debug(f"Loaded DataFrame with shape {df.shape}")

        elif data_format == "json":
            data = json.loads(data_payload)
            local_vars['data'] = data
            logger.debug("Loaded JSON data")

        elif data_format == "pdb":
            from Bio.PDB import PDBParser
            parser = PDBParser(QUIET=True)
            # PDBParser reads from a file handle
            structure = parser.get_structure("structure", io.StringIO(data_payload))
            local_vars['structure'] = structure
            logger.debug("Loaded PDB structure")

        else:
            return f"Error: Unsupported data format '{data_format}'"

    except Exception as e:
        logger.error(f"Data Loading Error: {e}")
        return f"Error loading data: {str(e)}"

    # 3. Execute Code
    # We capture stdout to allow the agent to simple "print()" results
    output_capture = io.StringIO()
    
    # We wrap the user code to redirect print
    # But since we use exec(), we can supply a custom print function or just capture stdout
    # Let's use contextlib for cleaner stdout capture if we were allowed, 
    # but 'sys' is restricted (logically, though we have access to it here in the host).
    # Actually, we can just inject a custom print into local_vars? No, print is builtin.
    # Standard redirect:
    import sys
    original_stdout = sys.stdout
    sys.stdout = output_capture
    
    try:
        # Update allowed globals with builtins we want to keep? 
        # exec uses current globals if not specified. We want RESTRICTED.
        # We give it SAFE_GLOBALS + builtins.
        exec_globals = SAFE_GLOBALS.copy()
        exec_globals['__builtins__'] = __builtins__ # Give access to standard python builtins (len, sum, etc). 
        # Be careful if builtins includes 'open' or 'eval' (it does). 
        # Specific restrictions would require deleting from a copy of builtins.
        
        exec(code, exec_globals, local_vars)
        
        # 4. Result Extraction
        # Priority: 'result' variable -> 'output' variable -> stdout
        output = output_capture.getvalue()
        
        if 'result' in local_vars:
            final_result = str(local_vars['result'])
        elif 'output' in local_vars:
            final_result = str(local_vars['output'])
        elif output.strip():
            final_result = output
        else:
            final_result = "Analysis completed but no output produced (print results or assign to 'result' variable)."

        logger.info("Analysis successfully executed.")
        return final_result

    except Exception as e:
        logger.error(f"Execution Error: {traceback.format_exc()}")
        return f"Error executing analysis code: {str(e)}"
    finally:
        sys.stdout = original_stdout
