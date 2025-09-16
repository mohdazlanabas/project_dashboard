"""
AI integration entrypoints.

For MVP, we use a lightweight NLQ parser + local tools to answer common
questions about the dataset (collections, schema, aggregations, KPIs).

If Vertex AI credentials are provided later, we can route questions through
Gemini and allow it to call the same tools for grounded answers.
"""

from typing import Optional, Any, Dict
import os

from django.utils.html import escape

from . import ai_tools

def _vertex_available() -> bool:
    return (
        os.getenv("GOOGLE_CLOUD_PROJECT")
        and os.getenv("GEMINI_LOCATION")
    ) is not None


def _vertex_call(question: str) -> Optional[str]:
    """Attempt a single-turn Gemini call with function calling.

    If the SDK or credentials are missing, return None to fall back to local NLQ.
    """
    try:
        from vertexai import init as vertex_init
        from vertexai.generative_models import (
            GenerativeModel,
            FunctionDeclaration,
            Tool,
        )

        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        location = os.getenv("GEMINI_LOCATION", "us-central1")
        vertex_init(project=project, location=location)

        # Define tool functions Gemini can call
        f_list = FunctionDeclaration(
            name="list_collections",
            description="List available MongoDB collections.",
        )
        f_describe = FunctionDeclaration(
            name="describe_collection",
            description="Describe a collection's fields and types from a small sample.",
            parameters={
                "type": "object",
                "properties": {"collection": {"type": "string"}},
                "required": ["collection"],
            },
        )
        f_totals = FunctionDeclaration(
            name="totals",
            description="Return deliveries, weight (kg/tons), and unique lorries for a period.",
            parameters={
                "type": "object",
                "properties": {"period": {"type": "string", "enum": ["hourly", "daily", "weekly", "monthly"]}},
                "required": ["period"],
            },
        )
        f_by_period = FunctionDeclaration(
            name="by_period",
            description="Weight totals by period bucket and lorry type.",
            parameters={
                "type": "object",
                "properties": {"period": {"type": "string", "enum": ["hourly", "daily", "weekly", "monthly"]}},
                "required": ["period"],
            },
        )
        f_by_type = FunctionDeclaration(
            name="by_lorry_type",
            description="Weight totals aggregated by lorry type for a period.",
            parameters={
                "type": "object",
                "properties": {"period": {"type": "string", "enum": ["hourly", "daily", "weekly", "monthly"]}},
                "required": ["period"],
            },
        )

        tool = Tool(function_declarations=[f_list, f_describe, f_totals, f_by_period, f_by_type])
        model = GenerativeModel("gemini-1.5-flash")
        resp = model.generate_content(
            [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": (
                                "You are a data assistant for a waste management dashboard. "
                                "Use tools to produce grounded answers. Keep responses concise and in HTML."
                            )
                        }
                    ],
                },
                {"role": "user", "parts": [{"text": question}]},
            ],
            tools=[tool],
        )

        # Inspect tool calls in the response (single-turn handling)
        calls = []
        for cand in getattr(resp, "candidates", []) or []:
            for part in getattr(cand, "content", {}).parts or []:
                fc = getattr(part, "function_call", None)
                if fc and getattr(fc, "name", None):
                    calls.append({"name": fc.name, "args": dict(getattr(fc, "args", {}) or {})})

        if not calls:
            # If the model returned text, use it
            try:
                return escape(resp.text)
            except Exception:
                return None

        # Execute the first function call locally and render a simple HTML answer
        call = calls[0]
        name = call["name"]
        args = call.get("args", {})
        # Map to local tools
        if name == "list_collections":
            cols = ai_tools.list_collections()
            lis = "".join(f"<li class='list-disc ml-5'>{escape(c)}</li>" for c in cols)
            return f"<div><strong>Collections</strong><ul>{lis}</ul></div>"
        if name == "describe_collection":
            col = args.get("collection") or "deliveries"
            d = ai_tools.describe_collection(col)
            rows = []
            for field, types in sorted(d.get("fields", {}).items()):
                tstr = ", ".join(f"{escape(t)}: {cnt}" for t, cnt in sorted(types.items()))
                rows.append(f"<tr><td class='px-2 py-1'>{escape(field)}</td><td class='px-2 py-1'>{tstr}</td></tr>")
            body = "".join(rows) or "<tr><td colspan='2' class='px-2 py-1 text-gray-500'>No sample.</td></tr>"
            return f"<div><strong>Schema for {escape(col)}</strong><table class='min-w-full border mt-1'><thead><tr><th class='text-left px-2 py-1'>Field</th><th class='text-left px-2 py-1'>Types</th></tr></thead><tbody>{body}</tbody></table></div>"
        if name == "totals":
            p = args.get("period", "daily")
            t = ai_tools.totals(p)
            return (
                f"<div><strong>Totals ({p.title()})</strong><br/>Deliveries: {t['deliveries']:,}<br/>"
                f"Weight (Kg): {int(t['weight_kg']):,}<br/>Weight (Tons): {t['weight_tons']:.2f}<br/>"
                f"Unique Lorries: {t['unique_lorries']:,}</div>"
            )
        if name == "by_period":
            p = args.get("period", "daily")
            data = ai_tools.by_period(p)
            head = "<tr><th class='text-left px-2 py-1'>Period</th><th class='text-left px-2 py-1'>Lorry Type</th><th class='text-left px-2 py-1'>Total Weight</th></tr>"
            rows = []
            for r in data[:100]:
                rows.append(
                    f"<tr><td class='px-2 py-1'>{escape(str(r.get('period_display', r.get('period'))))}</td>"
                    f"<td class='px-2 py-1'>{escape(str(r['lorry__lorry_type']))}</td>"
                    f"<td class='px-2 py-1'>{float(r['total_weight']):,.0f}</td></tr>"
                )
            body = "".join(rows) or "<tr><td colspan='3' class='px-2 py-1 text-gray-500'>No data.</td></tr>"
            return f"<div><strong>By Period ({p.title()})</strong><table class='min-w-full border mt-1'><thead>{head}</thead><tbody>{body}</tbody></table></div>"
        if name == "by_lorry_type":
            p = args.get("period", "daily")
            data = ai_tools.by_lorry_type(p)
            rows = []
            for tname, w in data:
                rows.append(f"<tr><td class='px-2 py-1'>{escape(tname)}</td><td class='px-2 py-1'>{w:,.0f}</td></tr>")
            body = "".join(rows) or "<tr><td colspan='2' class='px-2 py-1 text-gray-500'>No data.</td></tr>"
            return f"<div><strong>By Lorry Type ({p.title()})</strong><table class='min-w-full border mt-1'><thead><tr><th class='text-left px-2 py-1'>Type</th><th class='text-left px-2 py-1'>Total Weight</th></tr></thead><tbody>{body}</tbody></table></div>"

        return None
    except Exception:
        return None

def ask_gemini(question: str) -> str:
    """Answer a question using the local NLQ tools.

    Returns HTML suitable for injecting into the chat response div.
    """
    # Try Vertex AI (if configured), otherwise fallback to local NLQ
    html = _vertex_call(question)
    if html:
        return html
    try:
        from .nlq import answer_question
        return answer_question(question)
    except Exception as e:
        return f"<span class='text-red-600'>[AI error: {escape(str(e))}]</span>"
