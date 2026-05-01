# Support Triage Agent

A terminal-based support triage agent for HackerRank, Claude, and Visa tickets.

## Architecture

```
corpus.py      — loads 774 markdown docs from data/, tags each with domain + category
retrieval.py   — BM25 index (rank-bm25) for keyword search; one index per domain + cross-domain fallback
agent.py       — Groq llama-3.3-70b-versatile with JSON mode; returns all 5 output fields
main.py        — reads support_tickets/support_tickets.csv, runs the pipeline, writes output.csv
```

**Retrieval**: BM25 over the full corpus. Per-ticket query = subject + issue text. Domain-aware: if `Company` is set, only that domain's index is searched; otherwise all 3 are searched together.

**Classification**: A single Groq API call per ticket (llama-3.3-70b-versatile, free tier). Retrieved docs are injected into the prompt. JSON mode enforces valid output for all 5 fields. Escalation rules are baked into the system prompt (fraud, outages, admin-only actions, insufficient corpus coverage).

## Setup

```bash
cd code/

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure API key
# Get a free key at https://console.groq.com (no credit card required)
cp .env.example .env
# Edit .env and set: GROQ_API_KEY=gsk_...
```

## Running

```bash
# From inside code/ with venv active
python main.py
```

Output is written to `../support_tickets/output.csv`.

To validate against the sample tickets first:

```bash
python test_sample.py
```

## Dependencies

| Package       | Purpose                                       |
|---------------|-----------------------------------------------|
| groq          | Groq API client — llama-3.3-70b (free tier)  |
| rank-bm25     | BM25 retrieval over the corpus                |
| python-dotenv | Load GROQ_API_KEY from .env                   |
