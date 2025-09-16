"""Very small rule-based NLQ layer for MVP.

Maps common questions to tools that query Mongo-backed data via the ORM and
PyMongo (for schema/collections).
"""

import html
import re
from typing import Dict, List

from django.utils.html import escape

from .ai_tools import list_collections, describe_collection, totals, by_period, by_lorry_type


def _fmt_num(n: float, decimals: int = 0) -> str:
    if decimals:
        return f"{n:,.{decimals}f}"
    return f"{int(round(n)):,}"


def _period_from(text: str) -> str:
    text = text.lower()
    if any(k in text for k in ["hour", "hourly"]):
        return "hourly"
    if any(k in text for k in ["week", "weekly"]):
        return "weekly"
    if any(k in text for k in ["month", "monthly"]):
        return "monthly"
    return "daily"


def _answer_collections() -> str:
    cols = list_collections()
    items = "".join(f"<li class='list-disc ml-5'>{escape(c)}</li>" for c in cols)
    return f"<div><strong>Collections</strong><ul>{items}</ul></div>"


def _answer_describe(collection: str) -> str:
    d = describe_collection(collection, sample=100)
    rows = []
    for field, types in sorted(d.get("fields", {}).items()):
        types_str = ", ".join(f"{escape(t)}: {cnt}" for t, cnt in sorted(types.items()))
        rows.append(f"<tr><td class='px-2 py-1'>{escape(field)}</td><td class='px-2 py-1'>{types_str}</td></tr>")
    body = "".join(rows) or "<tr><td colspan='2' class='px-2 py-1 text-gray-500'>No sample found.</td></tr>"
    return f"""
    <div>
      <strong>Schema for {escape(collection)}</strong>
      <table class='min-w-full border mt-1'><thead><tr><th class='text-left px-2 py-1'>Field</th><th class='text-left px-2 py-1'>Types (sample)</th></tr></thead>
      <tbody>{body}</tbody></table>
    </div>
    """


def _answer_totals(period: str) -> str:
    t = totals(period)
    return f"""
    <div>
      <strong>Totals ({escape(period.title())})</strong><br/>
      Deliveries: {_fmt_num(t['deliveries'])}<br/>
      Weight (Kg): {_fmt_num(t['weight_kg'])}<br/>
      Weight (Tons): {_fmt_num(t['weight_tons'], 2)}<br/>
      Unique Lorries: {_fmt_num(t['unique_lorries'])}
    </div>
    """


def _answer_by_period(period: str) -> str:
    data = by_period(period)
    head = "<tr><th class='text-left px-2 py-1'>Period</th><th class='text-left px-2 py-1'>Lorry Type</th><th class='text-left px-2 py-1'>Total Weight</th></tr>"
    rows = []
    for r in data[:100]:
        rows.append(
            f"<tr><td class='px-2 py-1'>{escape(str(r.get('period_display', r.get('period'))))}</td>"
            f"<td class='px-2 py-1'>{escape(str(r['lorry__lorry_type']))}</td>"
            f"<td class='px-2 py-1'>{_fmt_num(float(r['total_weight']))}</td></tr>"
        )
    body = "".join(rows) or "<tr><td colspan='3' class='px-2 py-1 text-gray-500'>No data.</td></tr>"
    return f"<div><strong>By Period ({escape(period.title())})</strong><table class='min-w-full border mt-1'><thead>{head}</thead><tbody>{body}</tbody></table></div>"


def _answer_by_type(period: str) -> str:
    data = by_lorry_type(period)
    rows = []
    for t, w in data:
        rows.append(f"<tr><td class='px-2 py-1'>{escape(t)}</td><td class='px-2 py-1'>{_fmt_num(float(w))}</td></tr>")
    body = "".join(rows) or "<tr><td colspan='2' class='px-2 py-1 text-gray-500'>No data.</td></tr>"
    return f"<div><strong>By Lorry Type ({escape(period.title())})</strong><table class='min-w-full border mt-1'><thead><tr><th class='text-left px-2 py-1'>Lorry Type</th><th class='text-left px-2 py-1'>Total Weight</th></tr></thead><tbody>{body}</tbody></table></div>"


def answer_question(text: str) -> str:
    """Route a question to tools and return an HTML answer."""
    q = text.strip()
    if not q:
        return "<span class='text-gray-600'>Please ask a question.</span>"
    lo = q.lower()

    # Collections & schema
    if "collection" in lo and ("list" in lo or "what" in lo):
        return _answer_collections()
    m = re.search(r"describe|schema|fields?\s+(?:of\s+)?(deliveries|lorries)", lo)
    if m:
        return _answer_describe(m.group(1))

    # Totals/KPIs
    if any(k in lo for k in ["total weight", "weight total", "kpis", "totals"]):
        p = _period_from(lo)
        return _answer_totals(p)

    # By period / timeseries (table answer for chat)
    if "by day" in lo or "daily" in lo or "by week" in lo or "weekly" in lo or "by month" in lo or "monthly" in lo or "hourly" in lo:
        p = _period_from(lo)
        return _answer_by_period(p)

    # By type
    if "lorry type" in lo or ("type" in lo and "lorry" in lo):
        p = _period_from(lo)
        return _answer_by_type(p)

    # Deliveries count
    if "deliveries" in lo and ("count" in lo or "how many" in lo):
        p = _period_from(lo)
        t = totals(p)
        return f"<div><strong>Deliveries ({p.title()}):</strong> {_fmt_num(t['deliveries'])}</div>"

    # Fallback
    cols = _answer_collections()
    return (
        f"<div>I'm not sure yet. Try asking about totals, collections, schema, "
        f"'by lorry type', or 'daily/weekly/monthly' breakdowns. </div>" + cols
    )

