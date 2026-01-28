# Gene-to-Protein (G2P) Multi-Agent System

A comprehensive, AI-powered system for querying and analyzing Genomics 2 Proteins (G2P) data. Built on a transparent multi-agent architecture, it breaks down complex biological queries into specialized sub-tasks managed by domain-expert agents.

The goal of this system is to provide distinct, trustworthy, and transparent analysis of genetic data by "showing its work" every step of the way.

---

## 📖 Key Documentation
- **[Architectural Design](multi_agent_design.md)**: Deep dive into the agent roles, tool definitions, and system prompts.
- **[Frontend Streaming Guide](FRONTEND_STREAMING_GUIDE.md)**: How to consume the transparent SSE stream in your UI.
- **[Enhanced Events Reference](ENHANCED_EVENTS.md)**: Catalog of all event types, payloads, and display modes.

---

## 🏗 System Architecture

### 🧠 The Core Brain (Orchestrator)
The **Router Agent** acts as the central intelligence. It doesn't solve problems directly but understands the *intent* of a query and delegates it to the right specialist.

- **Dynamic Routing**: Parses user questions and selects the best specialist.
- **Context Injection**: Injects approved "Global Lessons" and user-specific preferences into every prompt.
- **Transparency**: Streams its thought process, decisions, and confidence levels using a structured event system.

### 👥 The Specialist Agents

| Agent | Icon | Role | Key Capability |
| :--- | :--- | :--- | :--- |
| **Genetic Discovery Agent** | 🧬 | The Librarian | Identifies genes, retrieves metadata (HGNC, UniProt), and determines disease validity (GenCC). |
| **Structural Biologist Agent** | 🔬 | The Architect | Analyzes protein domains, active sites, and 3D structures (AlphaFold/PDB). |
| **Variant Analyst Agent** | 🩺 | The Clinician | Maps variants to canonical sequences, checks alignments, and determines pathogenicity (ClinVar/gnomAD). |

### 🛠 Key Technologies
- **LangGraph**: Orchestrates the stateful, cyclic workflow between agents.
- **FastAPI**: Serves the application and handles high-performance SSE streaming.
- **Google Vertex AI (Gemini 1.5 Pro)**: Provide the reasoning capability for all agents.

---

## 📡 Transparent Streaming System

We have implemented a robust, frontend-friendly streaming protocol that lifts the veil on AI decision-making. Instead of receiving a black-box response, the user can see exactly *who* is working and *what* they are doing.

### Visibility Levels
The backend sends "visibility hints" with every event, allowing the frontend to easily toggle between modes:
1.  **Minimal**: Shows only the final answer (like standard chat).
2.  **Standard**: Shows active agents and tool execution status (e.g., "🧬 Genetic Discovery Specialist is Analyzing...").
3.  **Advanced**: Shows internal reasoning, decision confidence scores, and raw tool parameters.

### Core Event Lifecycle
1.  **Stream Start**: Sends a manifest with the Stream ID and expected events.
2.  **Thinking**: Emits the router's decision process (e.g., "Delegating to Variant Analyst because query implies a mutation").
3.  **Action**: Emits tool starts and sub-agent delegations.
4.  **Content**: Sends the final, synthesized answer in a single event.
5.  **Meta**: Updates the conversation title or signals the stream end.

---

## 🔬 The Computational Analyst (Analysis Tool)

One of the most critical components of this system is the **Computational Analyst** skill (`run_python_analysis`). This distinguishes the G2P Portal from standard "Chat with your Data" bots.

### Why It Matters
Biological APIs often return **rich but unstructured** data (e.g., an 800-row TSV file of protein domains). A standard LLM cannot "read" this effectively, nor can it accurately perform calculations on it (LLMs are notoriously bad at math).

### How It Works
Instead of trying to interpret raw text, the agent treats the data as a dataset:
1.  **Ingestion**: The agent loads the API response into a **secure pandas DataFrame**.
2.  **Code Generation**: It writes Python code to filter, aggregate, or analyze the data.
3.  **Execution**: The code runs in a sandboxed environment to produce a precise result.

### Example Scenarios
- **"Find pathogenic variants in the binding domain"**:
  - *Standard Bot*: Hallucinates or says "It's too long to read."
  - *Computational Analyst*: Merges the `ClinVar` column with the `Domain` column using `df.loc[]` and outputs the exact intersection.
  
- **"Calculate average hydrophobicity"**:
  - *Standard Bot*: Guesses numbers.
  - *Computational Analyst*: Runs `df['Hydrophobicity'].mean()` to get the mathematically correct answer.

---

## 🔁 Feedback & Learning Loop

The system is designed to improve over time without code changes through a persistent feedback mechanism using `LangGraph Store`.

### 1. Global Lessons (Admin Review)
- Users can suggest improvements (e.g., "Always mention the UniProt ID when introducing a protein").
- These suggestions enter a `pending` state.
- Admins review and **Approve** these lessons.
- Once approved, they are injected into the System Prompt for **all** users, effectively "patching" the agent's behavior globally.

### 2. User Preferences (Personal)
- Users can set personal instructions (e.g., "Explain concepts like I'm a 5th grader").
- These are stored and injected only for that specific user's sessions.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.12+
- Google Cloud Service Account (for Vertex AI access)

### Installation
1.  **Clone and Install**:
    ```bash
    git clone <repo_url>
    cd <repo_name>
    pip install -r requirements.txt
    ```

2.  **Environment Setup**:
    Create a `.env` file:
    ```ini
    GOOGLE_APPLICATION_CREDENTIALS="service-account.json"
    GOOGLE_GEMINI_MODEL="gemini-1.5-pro"
    ```

3.  **Run the Server**:
    ```bash
    uvicorn app.main:app --reload
    ```
    Server runs at `http://0.0.0.0:8000`.

### Testing
Use `curl` to test the streaming endpoint:
```bash
curl -N -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "dev_user", 
    "thread_id": "test_1", 
    "messages": [
      {"role": "user", "content": "What is the function of BRCA1?"}
    ]
  }'
```

---

## 🤝 Extending the System

To add a new specialist agent:

1.  **Define the Agent**: Create the class/function in `app/agents/specialists.py`.
2.  **Add Tools**: Implement the MCP tools in `app/tools/definitions.py`.
3.  **Register Routing**: Add the new agent branch to the graph in `app/agents/orchestrator.py`.
4.  **Update Transparency**: Add the agent's display name and icon to `SUBAGENT_INFO` in `app/services/stream_events.py`.
