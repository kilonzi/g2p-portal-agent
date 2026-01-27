# New Skill: The Computational Analyst

**Tool Name**: `run_python_analysis`
**Agent Owner**: Can be used by *all* agents, but primarily the **Structural Biologist** and **Variant Analyst** when they encounter large datasets.

## 1. Description & Purpose
The G2P Portal returns data that is **rich but unstructured** (e.g., 800+ row TSV files, nested JSON). A "Chat" interface cannot simply read this text row-by-row.
The `run_python_analysis` tool acts as a **Jupyter Notebook-in-a-box**. It allows the agent to write and execute Python code (`pandas`, `numpy`) to filter, aggregate, and calculate statistics on the data strictly returned by the other API tools.

## 2. Tool Definition (Schema)

```typescript
type RunPythonAnalysisParams = {
  // The raw data string returned by a previous tool (e.g., the full TSV string)
  data_payload: string;

  // The format of the data so the tool knows how to load it
  data_format: "tsv" | "json" | "csv";

  // The Python code to execute. The dataset will be pre-loaded as a variable named `df` (for tabular) or `data` (for JSON).
  code: string;

  // A brief explanation of what we are calculating (for logging/debugging)
  description: string;
};
```

## 3. How it Connects to G2P Data
This tool is specifically optimized for the **Protein Features TSV** we analyzed.

### Pre-Loading Logic (The "Magic")
When the tool runs, it shouldn't just run the code blank. It should **inject** the data based on the `data_format`.
*   **If `data_format="tsv"`**: The tool automatically runs `df = pd.read_csv(io.StringIO(data_payload), sep='\t')` before the user's code.
*   **If `data_format="json"`**: The tool runs `data = json.loads(data_payload)`.

## 4. Use Case Scenarios (The Scientific "Why")

### Scenario A: "Find Pathogenic variants in the Binding Domain"
*   **Problem**: The user asks for this intersection. The `protein-features` TSV has a `ClinVar` column and a `Pfam_Domain` column.
*   **Agent Action**:
    1. Call `get_protein_features` -> Gets giant TSV.
    2. Call `run_python_analysis`:
       ```python
       # Filter for rows where Domain is not empty AND ClinVar says 'Pathogenic'
       hits = df[
           (df['Pfam Output'].notna()) &
           (df['ClinVar'].str.contains('Pathogenic', na=False))
       ]
       # Return just the position and the change
       print(hits[['residueId', 'AA', 'Mutation', 'ClinVar']].to_string())
       ```
*   **Result**: The tool returns a clean 5-line table, instead of the agent trying to mentally merge 800 lines.

### Scenario B: "What is the average hydrophobicity of the Active Site?"
*   **Problem**: Requires math. "Active Site" is a flag in one column. "Hydrophobicity" is a number in another.
*   **Agent Action**:
    1. Call `get_protein_features`.
    2. Call `run_python_analysis`:
       ```python
       # Filter for Active Site rows
       active_sites = df[df['Site'].str.contains('Active', na=False)]
       # Calculate mean of Hydrophobicity column
       avg_hydro = active_sites['Hydrophobicity'].mean()
       print(f"Average Kyte-Doolittle Score: {avg_hydro}")
       ```

### Scenario C: "Summarize the GnomAD Allele Frequencies"
*   **Problem**: There are hundreds of variants. The user wants a distribution.
*   **Agent Action**:
    1. Call `get_protein_features`.
    2. Call `run_python_analysis`:
       ```python
       # GnomAD AF is a column.
       # Calculate simple stats
       stats = df['gnomAD_AF'].describe()
       print(stats)
       ```

## 5. Security & Safety
1.  **Sandboxed**: The tool runs in a restricted container. No network access allowed. It can only process the `data_payload` provided.

## 6. Hardening & Scientific Validation (Production Requirements)

Since this is a scientific application, "close enough" is failing. The tool implementation MUST enforce the following rigors:

### A. Data Type Enforcement (Strict Typing)
*   **Problem**: Pandas often misinterprets "123" as an Integer and "123A" as a String, causing merge errors.
*   **Solution**: The tool must strictly cast critical columns upon loading:
    ```python
    df['residueId'] = pd.to_numeric(df['residueId'], errors='coerce') # Ensure Residues are numbers
    df['ClinVar'] = df['ClinVar'].astype(str) # Ensure Text is Text
    ```

### B. Missing Value (NaN) Handling
*   **Problem**: G2P data is sparse. A blank cell means "No Feature", but pandas sees `NaN`. Queries like `df[df['Domain'].str.contains('Kinase')]` often crash on NaNs.
*   **Solution**: The auto-loader MUST fill NaNs with safe defaults before the agent sees the data.
    *   Text Columns -> Fill with `""` (Empty String).
    *   Numeric Columns -> Keep as `NaN` (so averages don't treat missing data as 0).

### C. Unique Constraint Verification
*   **Problem**: Duplicate rows in the input TSV can skew counts (e.g., counting the same pathogenic variant twice).
*   **Solution**: The tool must run `df.drop_duplicates(subset=['residueId'])` unless specialized isoform mapping is active.

### D. Input Sanitization
*   **Problem**: Malicious or accidental code injection.
*   **Solution**:
    *   **Block imports**: [os](file:///Users/johnkitonyo/PycharmProjects/Genomics2Proteins_portal/shared/utils/feature-data-parse-utils.js#1979-1983), `sys`, `subprocess` must be blacklisted.
    *   **Resource Limits**: Set a timeout (e.g., 5s) to prevent infinite loops.
    *   **Memory Limit**: restrict RAM usage (e.g., 512MB) to prevent crashing the server with a massive join.
