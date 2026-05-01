"""
Groq-powered triage agent: retrieves relevant docs and classifies each ticket.
Uses llama-3.3-70b-versatile via Groq's free tier with JSON mode.
"""

import json
import os

from groq import Groq

from corpus import Document

SYSTEM_PROMPT = """You are a support triage agent for three products: HackerRank, Claude, and Visa.

For each support ticket you receive, respond with a single JSON object containing exactly these fields:
- "status": "replied" or "escalated"
- "product_area": the category label of the most relevant retrieved document (see PRODUCT AREA RULES)
- "response": a user-facing answer grounded ONLY in the provided support documents
- "justification": a concise internal explanation of your routing/answering decision
- "request_type": one of "product_issue", "feature_request", "bug", "invalid"

PRODUCT AREA RULES:
- Each retrieved document has a label in the format "use_as_product_area: <label>". Copy that label exactly from the MOST relevant document.
- Do NOT invent a new label. Only use a label that appears in the retrieved documents.
- For Visa tickets, override the label based on content:
  - Travel-related (cheques, forex, travel card, travel insurance) → "travel_support"
  - Lost/stolen card, card reporting, emergency contacts → "general_support"
  - Fraud, disputed transactions, unauthorized charges → "fraud"
  - Merchant or business queries → "merchant_support"
- For escalated tickets, set product_area to "".
- For tickets with request_type="invalid" and no identifiable product domain (e.g. pure off-topic, simple thank-you), set product_area to "".

ESCALATION RULES — set status="escalated", response="Escalate to a human", product_area="" when:
- The ticket requests an action that ONLY an admin or account owner can perform (e.g. restoring removed seats, reversing charges, unlocking an account by force).
- The issue is a platform-wide outage or complete service disruption ("site is down", "none of the pages are accessible").
- The ticket involves a billing dispute, refund request, or payment reversal requiring human review.
- The ticket contains threats, abuse, or legal demands.
- The provided documents contain NO information relevant to the issue (truly unresolvable from the corpus).

REPLY RULES — set status="replied" when:
- The question is a how-to, FAQ, or product information request and the corpus has relevant content.
- The ticket reports a lost/stolen card, traveller's cheque, or similar — if the corpus provides emergency contact numbers or steps, reply with that information.
- The ticket is out of scope or irrelevant (e.g. general trivia, unrelated product) — reply politely that it is out of scope, set request_type="invalid".
- The ticket is a simple acknowledgement (e.g. "thank you") — reply briefly, set request_type="invalid".
- When relevant corpus documents exist, prefer replying over escalating.

GROUNDING RULES:
- Your response MUST be based ONLY on the support documents provided in the user message.
- Do not invent policies, steps, phone numbers, or URLs not present in those documents.
- Only escalate for a grounding reason when the documents have NO useful information at all.

Output only the JSON object — no markdown, no extra text."""


def _format_docs(docs: list[Document]) -> str:
    parts = []
    for i, doc in enumerate(docs, 1):
        parts.append(
            f"--- Document {i}: [{doc.domain}] {doc.title} | use_as_product_area: {doc.product_area} ---\n{doc.content[:1200]}"
        )
    return "\n\n".join(parts)


FALLBACK = {
    "status": "escalated",
    "product_area": "unknown",
    "response": "Escalate to a human",
    "justification": "Agent failed to produce a structured response.",
    "request_type": "product_issue",
}


class TriageAgent:
    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY is not set")
        self._client = Groq(api_key=api_key)

    def triage(
        self,
        issue: str,
        subject: str,
        company: str,
        docs: list[Document],
    ) -> dict:
        doc_block = _format_docs(docs) if docs else "No relevant documents found."

        user_message = f"""Company: {company}
Subject: {subject or "(none)"}
Issue: {issue}

Relevant support documents:
{doc_block}"""

        response = self._client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=1024,
        )

        raw = response.choices[0].message.content
        try:
            result = json.loads(raw)
            for key in ("status", "product_area", "response", "justification", "request_type"):
                if key not in result:
                    return FALLBACK
            return result
        except (json.JSONDecodeError, TypeError):
            return FALLBACK
