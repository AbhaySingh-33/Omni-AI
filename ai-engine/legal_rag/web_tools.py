from typing import Dict

from ddgs import DDGS


def search_legal_act(act_name: str) -> Dict[str, str]:
    query = f"{act_name} legal definition official"
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=3))

    if not results:
        return {"name": act_name, "description": "", "source_url": ""}

    top = results[0]
    body = (top.get("body") or "").strip()
    title = (top.get("title") or "").strip()
    summary = body if body else title
    return {
        "name": act_name,
        "description": summary,
        "source_url": (top.get("href") or "").strip(),
    }
