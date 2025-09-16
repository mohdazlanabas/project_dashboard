from collections import defaultdict
from datetime import datetime
import re

from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .models import Lorry

# Fixed MVP window and "now"
TRIAL_START = timezone.make_aware(datetime(2025, 1, 1, 0, 0, 0), timezone.utc)
TRIAL_END = timezone.make_aware(datetime(2025, 1, 31, 23, 59, 59), timezone.utc)
NOW = timezone.make_aware(datetime(2025, 1, 25, 16, 0, 0), timezone.utc)


def parse_delivery_time(value):
    """Parse DELIVERY_TIME from Mongo.
    Handles Python datetime, ISO strings, epoch numbers, and {'$date': ...} dicts.
    Returns aware UTC datetime or None.
    """
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        dt = value
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.utc)
        return dt
    if isinstance(value, dict) and '$date' in value:
        value = value['$date']
    if isinstance(value, (int, float)):
        ts = value / 1000.0 if value > 1e12 else float(value)
        try:
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        except Exception:
            return None
    if not isinstance(value, str):
        value = str(value)
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except Exception:
        dt = None
    if dt is None:
        try:
            normalized = re.sub(r"([+-]\d{2}):(\d{2})$", r"\1\2", value)
            dt = datetime.strptime(normalized, '%Y-%m-%dT%H:%M:%S.%f%z')
        except Exception:
            dt = None
    if dt is None:
        try:
            dt = parse_datetime(value)
        except Exception:
            dt = None
    if dt is None:
        for fmt in (
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S%z',
        ):
            try:
                dt = datetime.strptime(value, fmt)
                break
            except Exception:
                continue
    if dt is None:
        return None
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.utc)
    return dt


def get_period_key(dt, period):
    if period == 'hourly':
        return dt.replace(minute=0, second=0, microsecond=0)
    elif period == 'weekly':
        return f"{dt.isocalendar()[0]}-W{dt.isocalendar()[1]:02d}"
    elif period == 'monthly':
        return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:  # daily
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def python_aggregate(transactions, period):
    lorry_lookup = {l.lorry_id: l for l in Lorry.objects.all()}
    agg = defaultdict(lambda: defaultdict(float))
    for tx in transactions:
        dt = parse_delivery_time(tx.delivery_time)
        if dt is None:
            continue
        key = get_period_key(dt, period)
        lorry = lorry_lookup.get(tx.lorry_id)
        lorry_type = lorry.types_id if lorry else 'Unknown'
        try:
            weight_val = float(tx.weight)
        except Exception:
            continue
        agg[key][lorry_type] += weight_val
    rows = []
    for period_val, lorry_dict in agg.items():
        for lorry_type, total_weight in lorry_dict.items():
            rows.append({
                'period': period_val,
                'lorry__lorry_type': lorry_type,
                'total_weight': total_weight,
            })
    rows.sort(key=lambda r: str(r['period']), reverse=True)
    return rows

