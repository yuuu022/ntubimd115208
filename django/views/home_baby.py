import datetime
from datetime import timedelta
from zoneinfo import ZoneInfo

from django.shortcuts import render, redirect
from core.models import CareRecord, UserProfile, BabyInformation, BabyRecord, PregnancyCase
from views.pregnancycase import resolve_active_baby, resolve_active_pregnancy_case, sync_active_selection_from_request
from views.session_utils import get_current_user_profile

DEFAULT_USER_ID = 'ab63df64-b61f-480e-a61c-d54b851d2b5e'
TAIWAN_TZ = ZoneInfo('Asia/Taipei')


def _parse_selected_date(raw):
    try:
        return datetime.date.fromisoformat(raw) if raw else datetime.date.today()
    except Exception:
        return datetime.date.today()


def _day_bounds_in_taiwan(date_value):
    start_naive = datetime.datetime.combine(date_value, datetime.time.min)
    end_naive = start_naive + timedelta(days=1)
    return start_naive, end_naive


def home_baby(request):
    selected_date = _parse_selected_date(request.GET.get('date'))
    today = datetime.date.today()
    window_start = selected_date - timedelta(days=7)
    window_end = selected_date + timedelta(days=7)

    current_user = get_current_user_profile(request)
    if not current_user:
        return redirect('login')
    care_queryset = CareRecord.objects.select_related('carestatus').order_by('recordtime', 'carerecord_id')
    care_queryset = care_queryset.filter(user=current_user)

    window_start_dt, _ = _day_bounds_in_taiwan(window_start)
    _, window_end_exclusive = _day_bounds_in_taiwan(window_end)
    window_records = list(
        care_queryset.filter(recordtime__gte=window_start_dt, recordtime__lt=window_end_exclusive)
    )

    record_days = set()
    completion_by_day = {}
    for rec in window_records:
        rec_time = rec.recordtime
        if isinstance(rec_time, datetime.datetime):
            d = rec_time.date()
        else:
            d = rec_time
        record_days.add(d)
        completion_by_day.setdefault(d, {'total': 0, 'done': 0})
        completion_by_day[d]['total'] += 1
        if rec.state:
            completion_by_day[d]['done'] += 1

    care_day_cards = []
    weekday_labels = ['一', '二', '三', '四', '五', '六', '日']
    for offset in range(15):
        d = window_start + timedelta(days=offset)
        day_completion = completion_by_day.get(d)
        total = day_completion['total'] if day_completion else 0
        done = day_completion['done'] if day_completion else 0
        care_day_cards.append({
            'day': d.day,
            'weekday': weekday_labels[d.weekday()],
            'date_iso': d.isoformat(),
            'month_label': f'{d.month}/{d.day}',
            'is_selected': d == selected_date,
            'is_future': d > today,
            'has_record': d in record_days,
            'completion': f'{done}/{total}' if total else '',
            'all_done': bool(total) and done == total,
            'total': total,
            'done': done,
        })

    selected_start_dt, selected_end_dt = _day_bounds_in_taiwan(selected_date)
    selected_day_records = list(
        care_queryset.filter(recordtime__gte=selected_start_dt, recordtime__lt=selected_end_dt).order_by('recordtime', 'carerecord_id')
    )
    selected_day_total = len(selected_day_records)
    selected_day_done = sum(1 for r in selected_day_records if r.state)

    sync_active_selection_from_request(request, current_user)

    baby = None
    case = None
    is_pregnancy_view = False

    if request.session.get('active_baby_id'):
        baby = resolve_active_baby(request, current_user)
        case = baby.pregnancycase if baby else None
    else:
        case = resolve_active_pregnancy_case(request, current_user)
        is_pregnancy_view = bool(case)

    baby_list = BabyInformation.objects.filter(pregnancycase__user=current_user)

    # Calculate data based on selection
    if is_pregnancy_view and case:
        # Pregnancy case data
        menstruation_date = case.menstruation
        if not menstruation_date and case.expecteddate:
            menstruation_date = case.expecteddate - timedelta(days=280)

        if menstruation_date:
            delta = datetime.date.today() - menstruation_date
            weeks = delta.days // 7
            days = delta.days % 7
            baby_weeks = max(0, weeks)
            baby_days = max(0, days)
            # Pregnancy progress (40 weeks = 100%)
            baby_percent = min(100, int((delta.days / 280) * 100)) if delta.days >= 0 else 0
        else:
            baby_weeks = 0
            baby_days = 0
            baby_percent = 0

        baby_chart_data = []
    elif baby and baby.birthdaytime:
        # Born baby data
        birth_date = baby.birthdaytime.date() if isinstance(baby.birthdaytime, datetime.datetime) else baby.birthdaytime
        days_total = (datetime.date.today() - birth_date).days
        baby_weeks = max(0, days_total // 7)
        baby_days = max(0, days_total % 7)
        # First year growth rate (364 days = 100%)
        baby_percent = min(100, int((days_total / 364) * 100)) if days_total >= 0 else 0

        # Baby weight/height history
        baby_records = BabyRecord.objects.filter(baby=baby).order_by('date')
        baby_chart_data = []
        for r in baby_records:
            if r.weight is not None or r.height is not None:
                r_date = r.date.date() if isinstance(r.date, datetime.datetime) else r.date
                delta_days = (r_date - baby.birthdaytime.date()).days if baby and baby.birthdaytime else 0
                week = max(0, delta_days // 7)
                baby_chart_data.append({
                    'week': week,
                    'weight': float(r.weight) if r.weight is not None else None,
                    'height': float(r.height) if r.height is not None else None
                })
    else:
        # Default fallback
        baby_weeks = 24
        baby_days = 4
        baby_percent = 60
        baby_chart_data = []

    context = {
        'selected_date': selected_date,
        'selected_date_iso': selected_date.isoformat(),
        'selected_month_label': f'{selected_date.year}年{selected_date.month}月',
        'selected_day_label': f'{selected_date.month}/{selected_date.day}',
        'window_start_iso': window_start.isoformat(),
        'window_end_iso': window_end.isoformat(),
        'today_iso': today.isoformat(),
        'care_day_cards': care_day_cards,
        'care_records': selected_day_records,
        'care_done_count': selected_day_done,
        'care_total_count': selected_day_total,
        'care_progress_percent': int((selected_day_done / selected_day_total) * 100) if selected_day_total else 0,

        'baby': baby,
        'case': case,
        'is_pregnancy_view': is_pregnancy_view,
        'baby_list': baby_list,
        'baby_weeks': baby_weeks,
        'baby_days': baby_days,
        'baby_percent': baby_percent,
        'baby_chart_data': baby_chart_data,
    }
    return render(request, 'home_baby.html', context)
