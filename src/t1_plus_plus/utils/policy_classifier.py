"""
LLM-based domain classifier for policy selection.

Given a user query (or a domain hint), classifies which policy domains are
relevant and returns the full text of those policy files.

Supported domains map 1-to-1 with files in the policies/ directory.
"""

import json
import os
from typing import Optional

from openai import OpenAI

_DOMAIN_TO_FILE = {
    "attraction": "attraction_policy.md",
    "bar": "bar_policy.md",
    "cafe": "cafe_policy.md",
    "cruise": "cruise_policy.md",
    "dessert": "dessert_policy.md",
    "flight": "flight_policy.md",
    "food_and_dining": "food_and_dining_policy.md",
    "hotel": "hotel_policy.md",
    "kayak_rental": "kayak_rental_policy.md",
    "live_show": "live_show_policy.md",
    "vehicle_rental": "vehicle_rental_policy.md",
}

_CLASSIFIER_SYSTEM_PROMPT = """\
You are a domain classifier for a travel and hospitality assistant.

Given a query or context, identify which policy domains are relevant.
Return ONLY a JSON array of domain names from the allowed list — nothing else.

Allowed domains:
- attraction
- bar
- cafe
- cruise
- dessert
- flight
- food_and_dining
- hotel
- kayak_rental
- live_show
- vehicle_rental

Examples:
  CHAT HISTORY: ["I want to book a hotel"]
  Query: "I want to book a flight from NYC to LA"
  → ["flight", "hotel"]

  CHAT HISTORY: []
  Query: "I need a hotel and a rental car in Miami"
  → ["hotel", "vehicle_rental"]

  CHAT HISTORY: []
  Query: "Find me a restaurant and a live show for tonight"
  → ["food_and_dining", "live_show"]

  CHAT HISTORY: []
  Query: "Bar Assistant"
  → ["bar"]

Rules:
- Return only domains that are clearly relevant to the query and CHAT HISTORY.
- Return at least one domain.
- Never include a domain not on the allowed list.
- Output ONLY the JSON array, no explanation.
"""


def classify_domains(
    query: str,
    chat_history: Optional[list[dict]] = None,
    client: Optional[OpenAI] = None,
    model: str = "",
) -> list[str]:
    """
    Use an LLM to classify which domains are relevant for *query*.

    Optionally accepts *chat_history* — a list of {"role": ..., "content": ...}
    dicts — to provide additional context for classification when available.

    Returns a list of domain name strings (e.g. ["flight", "hotel"]).
    Falls back to keyword matching then a single default if the LLM call fails.
    """
    if client is None:
        client = OpenAI(
            base_url=os.getenv("LLM_BASE_URL"),
            api_key=os.getenv("LLM_API_KEY", "unused"),
        )

    # Build the user message: prepend condensed history if provided
    if chat_history:
        history_lines = []
        for msg in chat_history:
            role = msg.get("role", "")
            content = msg.get("content") or ""
            # Skip tool result messages and empty content to keep context tight
            if role == "tool" or not content.strip():
                continue
            history_lines.append(f"{role.upper()}: {content.strip()}")
        if history_lines:
            history_block = "\n".join(history_lines)
            user_message = f"CHAT HISTORY:\n{history_block}\n\nLATEST QUERY: {query}"
        else:
            user_message = query
    else:
        user_message = query

    print(f"  [CLASSIFIER] Classifying domain for query: {query!r}")
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _CLASSIFIER_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=1.0,
        )
        raw = resp.choices[0].message.content.strip()
        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        domains = json.loads(raw)
        if isinstance(domains, list) and domains:
            # Filter to only known domains
            valid = [d for d in domains if d in _DOMAIN_TO_FILE]
            if valid:
                return valid
    except Exception as e:
        print(f"  [CLASSIFIER] Classification failed: {e}")

    return None


def load_all_policies(policies_dir: str) -> dict[str, str]:
    """
    Read every known policy file up front and return a dict mapping
    domain name → policy text.  Missing files are silently skipped.
    """
    cache: dict[str, str] = {}
    for domain, filename in _DOMAIN_TO_FILE.items():
        path = os.path.join(policies_dir, filename)
        if not os.path.exists(path):
            print(f"  [CLASSIFIER] Policy file not found: {path} — skipping.")
            continue
        with open(path, "r", encoding="utf-8") as f:
            cache[domain] = f.read().strip()
    return cache


def load_policies_for_domains(
    domains: list[str],
    policies_dir: str,
    policy_cache: Optional[dict[str, str]] = None,
) -> str:
    """
    Return concatenated policy text for *domains*.

    If *policy_cache* (a dict from :func:`load_all_policies`) is provided the
    files are not re-read from disk; otherwise they are read on demand.

    Returns a single string with all relevant policy content separated by
    a markdown horizontal rule.
    """
    sections = []
    for domain in domains:
        if policy_cache is not None:
            content = policy_cache.get(domain)
            if content is None:
                print(f"  [CLASSIFIER] Domain '{domain}' not in policy cache — skipping.")
            else:
                sections.append(content)
            continue

        filename = _DOMAIN_TO_FILE.get(domain)
        if not filename:
            print(f"  [CLASSIFIER] Unknown domain '{domain}' — skipping.")
            continue
        path = os.path.join(policies_dir, filename)
        if not os.path.exists(path):
            print(f"  [CLASSIFIER] Policy file not found: {path} — skipping.")
            continue
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        sections.append(content)

    if not sections:
        return ""
    return "\n\n---\n\n".join(sections)
