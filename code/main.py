"""
Entry point: reads support_tickets/support_tickets.csv, runs triage agent,
writes results to support_tickets/output.csv.
"""

import csv
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the code/ directory (or repo root as fallback)
load_dotenv(Path(__file__).parent / ".env")
load_dotenv(Path(__file__).parent.parent / ".env")

from corpus import load_corpus
from retrieval import Retriever
from agent import TriageAgent

REPO_ROOT = Path(__file__).parent.parent
INPUT_CSV = REPO_ROOT / "support_tickets" / "support_tickets.csv"
OUTPUT_CSV = REPO_ROOT / "support_tickets" / "output.csv"

OUTPUT_FIELDS = ["Issue", "Subject", "Company", "Response", "Product Area", "Status", "Request Type"]


def build_retrievers(all_docs):
    """Build one retriever per domain plus a cross-domain fallback."""
    domain_docs = {}
    for doc in all_docs:
        domain_docs.setdefault(doc.domain, []).append(doc)

    retrievers = {domain: Retriever(docs) for domain, docs in domain_docs.items()}
    retrievers["all"] = Retriever(all_docs)
    return retrievers


def get_docs(retrievers, company: str, query: str, top_k: int = 5):
    company = company.strip()
    if company in retrievers:
        return retrievers[company].search(query, top_k=top_k)
    return retrievers["all"].search(query, top_k=top_k)


def main():
    print("Loading corpus...", flush=True)
    all_docs = load_corpus()
    print(f"  Loaded {len(all_docs)} documents", flush=True)

    retrievers = build_retrievers(all_docs)
    agent = TriageAgent()

    rows = []
    with open(INPUT_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Processing {len(rows)} tickets...\n", flush=True)

    results = []
    for i, row in enumerate(rows, 1):
        issue = row.get("Issue", "").strip()
        subject = row.get("Subject", "").strip()
        company = row.get("Company", "None").strip()

        query = f"{subject} {issue}".strip()
        docs = get_docs(retrievers, company, query, top_k=5)

        print(f"[{i}/{len(rows)}] {company}: {subject or issue[:60]!r}", flush=True)

        result = agent.triage(issue=issue, subject=subject, company=company, docs=docs)

        results.append({
            "Issue": issue,
            "Subject": subject,
            "Company": company,
            "Response": result["response"],
            "Product Area": result["product_area"],
            "Status": result["status"].capitalize(),
            "Request Type": result["request_type"],
        })

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(results)

    print(f"\nDone. Output written to {OUTPUT_CSV}", flush=True)


if __name__ == "__main__":
    main()
