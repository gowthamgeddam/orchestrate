"""
Run the triage agent on sample_support_tickets.csv and compare with expected output.
"""

import csv
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
load_dotenv(Path(__file__).parent.parent / ".env")

from corpus import load_corpus
from retrieval import Retriever
from agent import TriageAgent

REPO_ROOT = Path(__file__).parent.parent
SAMPLE_CSV = REPO_ROOT / "support_tickets" / "sample_support_tickets.csv"

COMPARE_FIELDS = ["Status", "Product Area", "Request Type"]


def main():
    print("Loading corpus...", flush=True)
    all_docs = load_corpus()
    domain_docs = {}
    for doc in all_docs:
        domain_docs.setdefault(doc.domain, []).append(doc)
    retrievers = {d: Retriever(docs) for d, docs in domain_docs.items()}
    retrievers["all"] = Retriever(all_docs)

    agent = TriageAgent()

    with open(SAMPLE_CSV, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    correct = {f: 0 for f in COMPARE_FIELDS}
    total = len(rows)

    for i, row in enumerate(rows, 1):
        issue = row["Issue"].strip()
        subject = row["Subject"].strip()
        company = row["Company"].strip()
        query = f"{subject} {issue}".strip()

        retriever = retrievers.get(company, retrievers["all"])
        docs = retriever.search(query, top_k=5)

        result = agent.triage(issue=issue, subject=subject, company=company, docs=docs)

        got_status = result["status"].capitalize()
        got_area = result["product_area"]
        got_type = result["request_type"]

        exp_status = row["Status"].strip()
        exp_area = row["Product Area"].strip()
        exp_type = row["Request Type"].strip()

        match_status = got_status.lower() == exp_status.lower()
        match_area = got_area.lower() == exp_area.lower()
        match_type = got_type.lower() == exp_type.lower()

        if match_status: correct["Status"] += 1
        if match_area: correct["Product Area"] += 1
        if match_type: correct["Request Type"] += 1

        status_icon = "✓" if match_status else "✗"
        area_icon = "✓" if match_area else "✗"
        type_icon = "✓" if match_type else "✗"

        print(f"\n[{i}/{total}] {company}: {(subject or issue[:50])!r}")
        print(f"  Status:       {status_icon} got={got_status!r:12} exp={exp_status!r}")
        print(f"  Product Area: {area_icon} got={got_area!r:20} exp={exp_area!r}")
        print(f"  Request Type: {type_icon} got={got_type!r:20} exp={exp_type!r}")
        print(f"  Response:     {result['response'][:120]}")

    print(f"\n{'='*60}")
    print("ACCURACY SUMMARY")
    print(f"{'='*60}")
    for field in COMPARE_FIELDS:
        pct = correct[field] / total * 100
        print(f"  {field:15} {correct[field]}/{total}  ({pct:.0f}%)")


if __name__ == "__main__":
    main()
