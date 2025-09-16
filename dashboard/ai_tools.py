from collections import defaultdict, Counter
from datetime import datetime
from typing import Dict, List, Tuple

from django.conf import settings
from django.utils import timezone

from .models import Lorry, Transaction
from .timeutils import parse_delivery_time, python_aggregate, get_period_key, NOW, TRIAL_START, TRIAL_END

try:
    import pymongo  # type: ignore
except Exception:  # pragma: no cover
    pymongo = None


def list_collections() -> List[str]:
    """List MongoDB collections using PyMongo if available, else fallback."""
    url = settings.DATABASES["default"].get("CLIENT", {}).get("host")
    name = settings.DATABASES["default"].get("NAME")
    if not pymongo or not url or not name:
        # Fallback to common known collections
        return ["deliveries", "lorries"]
    client = pymongo.MongoClient(url)
    db = client[name]
    try:
        cols = sorted(db.list_collection_names())
    finally:
        client.close()
    return cols


def describe_collection(coll: str, sample: int = 50) -> Dict:
    """Return a simple field/type summary for a collection."""
    url = settings.DATABASES["default"].get("CLIENT", {}).get("host")
    name = settings.DATABASES["default"].get("NAME")
    if not pymongo or not url or not name:
        return {"collection": coll, "fields": {}}
    client = pymongo.MongoClient(url)
    db = client[name]
    fields: Dict[str, Counter] = {}
    try:
        for doc in db[coll].find({}, projection=None).limit(sample):
            for k, v in doc.items():
                t = type(v).__name__
                fields.setdefault(k, Counter())[t] += 1
    finally:
        client.close()
    # convert counters to simple dicts
    return {
        "collection": coll,
        "fields": {k: dict(c) for k, c in fields.items()},
        "sampled": sample,
    }


def _window_for(period: str) -> Tuple[datetime, datetime]:
    end = min(NOW, TRIAL_END)
    if period == "hourly":
        start = end.replace(hour=0, minute=0, second=0, microsecond=0)
        return start, end
    return TRIAL_START, end


def totals(period: str) -> Dict:
    since, until = _window_for(period)
    qs = Transaction.objects.all()
    txs = []
    for tx in qs:
        dt = parse_delivery_time(tx.delivery_time)
        if dt and since <= dt <= until:
            txs.append(tx)
    total_deliveries = len(txs)
    total_weight_kg = sum((float(getattr(t, "weight", 0) or 0) for t in txs), 0.0)
    unique_lorries = len({t.lorry_id for t in txs})
    return {
        "since": since,
        "until": until,
        "deliveries": total_deliveries,
        "weight_kg": total_weight_kg,
        "weight_tons": total_weight_kg / 1000.0,
        "unique_lorries": unique_lorries,
    }


def by_period(period: str) -> List[Dict]:
    since, until = _window_for(period)
    qs = Transaction.objects.all()
    txs = []
    for tx in qs:
        dt = parse_delivery_time(tx.delivery_time)
        if dt and since <= dt <= until:
            txs.append(tx)
    return python_aggregate(txs, period)


def by_lorry_type(period: str) -> List[Tuple[str, float]]:
    data = by_period(period)
    acc = defaultdict(float)
    for row in data:
        acc[row["lorry__lorry_type"]] += float(row["total_weight"])
    return sorted(acc.items(), key=lambda x: (-x[1], x[0]))
