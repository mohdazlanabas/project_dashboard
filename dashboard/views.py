from django.shortcuts import render, redirect
from .models import Transaction
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import Trunc
from django.http import HttpResponse
from django.template.loader import render_to_string
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Lorry, Transaction
from .serializers import LorrySerializer, TransactionSerializer
from django.views.decorators.csrf import csrf_exempt
from django.utils.html import escape
import itertools
from collections import defaultdict
from datetime import datetime
from django.utils.dateparse import parse_datetime
import re

TRIAL_START = timezone.make_aware(datetime(2025, 1, 1, 0, 0, 0), timezone.utc)
TRIAL_END = timezone.make_aware(datetime(2025, 1, 31, 23, 59, 59), timezone.utc)
# Fixed "today" for MVP scenarios; adjust in production
NOW = timezone.make_aware(datetime(2025, 1, 25, 16, 0, 0), timezone.utc)

def get_window(period: str):
    """Return (since, until) bounds based on the selected period.
    - hourly: start of "today" to NOW
    - daily/weekly/monthly: from TRIAL_START to NOW (capped by TRIAL_END)
    """
    end = min(NOW, TRIAL_END)
    if period == 'hourly':
        start = end.replace(hour=0, minute=0, second=0, microsecond=0)
        return start, end
    # default to month-to-date for other granularities
    return TRIAL_START, end

def parse_delivery_time(value):
    """Parse DELIVERY_TIME coming from MongoDB.
    Handles Python datetime, ISO strings, epoch numbers, and {'$date': ...} dicts.
    Returns timezone-aware UTC datetime or None.
    """
    if value is None or value == "":
        return None
    # Already a datetime
    if isinstance(value, datetime):
        dt = value
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.utc)
        return dt
    # Djongo/pymongo can sometimes give {'$date': ...}
    if isinstance(value, dict) and '$date' in value:
        value = value['$date']
    # Epoch seconds or milliseconds
    if isinstance(value, (int, float)):
        # Heuristic: if too large, assume ms
        ts = value / 1000.0 if value > 1e12 else float(value)
        try:
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        except Exception:
            return None
    # Coerce to string for the parsers below
    if not isinstance(value, str):
        value = str(value)
    # Fast path: Python's ISO 8601 parser (supports '+HH:MM' offsets and milliseconds)
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except Exception:
        dt = None
    # Normalize timezone like +HH:MM -> +HHMM and retry if needed
    if dt is None:
        try:
            normalized = re.sub(r"([+-]\d{2}):(\d{2})$", r"\1\2", value)
            dt = datetime.strptime(normalized, '%Y-%m-%dT%H:%M:%S.%f%z')
        except Exception:
            dt = None
    # Try Django's parser
    if dt is None:
        try:
            dt = parse_datetime(value)
        except Exception:
            dt = None
    # Try a few explicit formats
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
        # ISO week: (year, week number)
        return f"{dt.isocalendar()[0]}-W{dt.isocalendar()[1]:02d}"
    elif period == 'monthly':
        return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:  # daily
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)

def python_aggregate(transactions, period):
    from .models import Lorry
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
        # Build a human-readable label for the period
        period_display = None
        try:
            if isinstance(period_val, datetime):
                if period == 'hourly':
                    period_display = period_val.strftime('%Y-%m-%d %H:00')
                elif period == 'monthly':
                    period_display = period_val.strftime('%Y-%m')
                else:  # daily
                    period_display = period_val.strftime('%Y-%m-%d')
            else:
                # weekly keys are strings like YYYY-Www
                period_display = str(period_val)
        except Exception:
            period_display = str(period_val)
        for lorry_type in sorted(lorry_dict.keys()):
            total_weight = lorry_dict[lorry_type]
            rows.append({
                'period': period_val,
                'period_display': period_display,
                'lorry__lorry_type': lorry_type,
                'total_weight': total_weight,
            })
    # Sort rows by period (desc), then lorry type (asc)
    rows.sort(key=lambda r: (str(r['period']), r['lorry__lorry_type']))
    rows.reverse()
    # Assign more-visible banding and a stronger border at the start of each group
    band_flag = False
    last_period_label = None
    for r in rows:
        is_new_group = r['period_display'] != last_period_label
        if is_new_group:
            band_flag = not band_flag
            last_period_label = r['period_display']
        r['band'] = 'bg-blue-100' if band_flag else 'bg-white'
        # Inline style fallback to ensure visibility even if CSS lacks the class
        r['band_style'] = 'background-color: #DBEAFE;' if band_flag else ''
        r['group_border'] = 'border-t-4 border-blue-300' if is_new_group else ''
    return rows

def dashboard_view(request):
    period = request.GET.get('period', 'daily')  # default granularity
    since, until = get_window(period)
    qs = Transaction.objects.all()
    # Filter in Python due to string dates
    txs = []
    for tx in qs:
        dt = parse_delivery_time(tx.delivery_time)
        if dt and since <= dt <= until:
            txs.append(tx)
    aggregated = python_aggregate(txs, period)
    latest_transactions = sorted(
        txs, key=lambda t: parse_delivery_time(t.delivery_time) or TRIAL_START, reverse=True
    )[:20]
    # Enrich latest transactions with lorry type via lookup (no DB FK)
    lorry_lookup = {l.lorry_id: l for l in Lorry.objects.all()}
    enriched_latest = []
    for t in latest_transactions:
        l = lorry_lookup.get(t.lorry_id)
        enriched_latest.append({
            'transaction_id': t.transaction_id,
            'lorry_id': t.lorry_id,
            'lorry_types_id': getattr(l, 'types_id', 'Unknown') if l else 'Unknown',
            'weight': t.weight,
            'delivery_time': t.delivery_time,
        })
    # KPI calculations (always month-to-date regardless of selected period)
    kpi_since, kpi_until = TRIAL_START, min(NOW, TRIAL_END)
    kpi_txs = []
    for tx in qs:
        dt = parse_delivery_time(tx.delivery_time)
        if dt and kpi_since <= dt <= kpi_until:
            kpi_txs.append(tx)
    total_deliveries = len(kpi_txs)
    total_weight_kg = sum((float(getattr(t, 'weight', 0) or 0) for t in kpi_txs), 0.0)
    unique_lorries = len({t.lorry_id for t in kpi_txs})

    context = {
        'transactions': enriched_latest,
        'aggregated': aggregated,
        'period': period,
        'now': NOW,
        'now_display': NOW.strftime('%d %b %Y, %I:%M %p UTC'),
        # Summary KPIs for the trial month
        'kpi_total_deliveries': total_deliveries,
        'kpi_total_weight_kg': total_weight_kg,
        'kpi_total_weight_tons': total_weight_kg / 1000.0 if total_weight_kg else 0.0,
        'kpi_unique_lorries': unique_lorries,
    }
    return render(request, 'dashboard/index.html', context)

def aggregated_table(request):
    period = request.GET.get('period', 'daily')
    # If this endpoint is opened directly in the browser (not an HTMX request),
    # push users back to the full page with the selected period so layout/scripts load.
    if not request.headers.get('HX-Request'):
        return redirect(f'/?period={period}')
    since, until = get_window(period)
    qs = Transaction.objects.all()
    txs = []
    for tx in qs:
        dt = parse_delivery_time(tx.delivery_time)
        if dt and since <= dt <= until:
            txs.append(tx)
    aggregated = python_aggregate(txs, period)
    html = render_to_string('dashboard/_aggregated_table.html', {'aggregated': aggregated, 'period': period})
    response = HttpResponse(html)
    # Ask HTMX to push the root URL with the period param, not the partial URL
    response["HX-Push-Url"] = f"/?period={period}"
    return response

class LorryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Lorry.objects.all()
    serializer_class = LorrySerializer

class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    # No FK relation on Transaction; use plain queryset
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

class AggregatedDataAPIView(APIView):
    def get(self, request):
        period = request.GET.get('period', 'daily')
        since, until = get_window(period)
        qs = Transaction.objects.all()
        txs = []
        for tx in qs:
            dt = parse_delivery_time(tx.delivery_time)
            if dt and since <= dt <= until:
                txs.append(tx)
        aggregated = python_aggregate(txs, period)
        return Response(aggregated)

@csrf_exempt  # For demo; in production, use proper CSRF handling!
def dashboard_chat(request):
    if request.method == 'POST':
        question = request.POST.get('question', '').strip()
        if not question:
            return HttpResponse('<span class="text-red-600">Please enter a question.</span>')
        # Placeholder for Gemini call
        try:
            from .gemini import ask_gemini
            answer = ask_gemini(question)
        except Exception as e:
            answer = f"[Error contacting AI: {escape(str(e))}]"
        return HttpResponse(f'<strong>Q:</strong> {escape(question)}<br><strong>A:</strong> {escape(answer)}')
    return HttpResponse('<span class="text-red-600">Invalid request.</span>')
