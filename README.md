# Gene-to-Protein (G2P) Multi-Agent System

A multi-agent AI system designed to query and analyze data from the Genomics 2 Proteins (G2P) portal. It uses a graph of specialized agents to discover genes, analyze protein usage, and interpret variants.

## System Architecture

The system is orchestrating by a **Main Router Agent** that delegates tasks to three specialists:

1.  **Genetic Discovery Agent**: The librarian. Identifies genes, retrieves metadata (HGNC, UniProt), and determines disease validity (GenCC).
2.  **Structural Biologist Agent**: The architect. Analyzes protein domains, active sites, and 3D structures (AlphaFold/PDB).
3.  **Variant Analyst Agent**: The clinician. Maps variants to canonical sequences and checks pathogenicity (ClinVar/gnomAD).

## Prerequisities

- Python 3.12+
- Google Cloud Service Account (for Vertex AI / Gemini access)

## Setup

1.  **Clone the repository** and install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Environment Configuration**:
    Create a `.env` file in the root directory:
    ```ini
    # Google Vertex AI Credentials (JSON key file path)
    GOOGLE_APPLICATION_CREDENTIALS="service-account.json"
    
    # Model Configuration
    GOOGLE_GEMINI_MODEL="gemini-1.5-pro"
    ```

3.  **Service Account**:
    Ensure your `service-account.json` is present in the project root or the path specified above.

## Running the Application

You can start the server using `uvicorn`:

```bash
uvicorn app.main:app --reload
```

The server will start at `http://0.0.0.0:8000`.

## API Usage

### Health Check

```bash
curl http://localhost:8000/status
```

### Stream Chat

Stream a conversation with the multi-agent system using Server-Sent Events (SSE).

**Example Request:**
```bash
curl -N -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user", 
    "thread_id": "thread_1", 
    "messages": [
      {"role": "user", "content": "What is LDLR and does it have any variants?"}
    ]
  }'
```

The response will be streamed token-by-token as the agents reason and generate the answer.
