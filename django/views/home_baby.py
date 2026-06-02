import datetime
from datetime import timedelta
from zoneinfo import ZoneInfo

from django.shortcuts import render, redirect
from core.models import CareRecord, BabyInformation, BabyRecord, PregnancyCase
from views.pregnancycase import resolve_active_pregnancy_case, sync_active_selection_from_request
from views.session_utils import get_current_user_profile

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

    # ── 照顧紀錄（代辦清單） ─────────────────────────────────
    care_queryset = (
        CareRecord.objects
        .select_related('carestatus')
        .filter(user=current_user)
        .order_by('recordtime', 'carerecord_id')
    )

    window_start_dt, _ = _day_bounds_in_taiwan(window_start)
    _, window_end_exclusive = _day_bounds_in_taiwan(window_end)
    window_records = list(
        care_queryset.filter(recordtime__gte=window_start_dt, recordtime__lt=window_end_exclusive)
    )

    record_days = set()
    completion_by_day = {}
    for rec in window_records:
        d = rec.recordtime.date() if isinstance(rec.recordtime, datetime.datetime) else rec.recordtime
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
        care_queryset
        .filter(recordtime__gte=selected_start_dt, recordtime__lt=selected_end_dt)
        .order_by('recordtime', 'carerecord_id')
    )
    selected_day_total = len(selected_day_records)
    selected_day_done = sum(1 for r in selected_day_records if r.state)

    # ── 以胎數為主軸取嬰幼兒 ───────────────────────────────────
    sync_active_selection_from_request(request, current_user)
    case = resolve_active_pregnancy_case(request, current_user)

    # 該胎數下的所有嬰幼兒
    babies = list(BabyInformation.objects.filter(pregnancycase=case).order_by('baby_id')) if case else []

    # URL ?baby_id=X 切換；預設選第一筆
    url_baby_id = request.GET.get('baby_id')
    selected_baby = None
    if url_baby_id:
        selected_baby = next((b for b in babies if str(b.baby_id) == str(url_baby_id)), None)
    if selected_baby is None and babies:
        selected_baby = babies[0]

    # ── 計算進度與圖表資料 ────────────────────────────────────
    baby_weeks = 0
    baby_days = 0
    baby_percent = 0
    baby_chart_data = []

    if selected_baby and selected_baby.birthdaytime:
        birth_date = (
            selected_baby.birthdaytime.date()
            if isinstance(selected_baby.birthdaytime, datetime.datetime)
            else selected_baby.birthdaytime
        )
        days_total = (today - birth_date).days
        
        # 計算月齡 (0-3 歲進度)
        years = today.year - birth_date.year
        months = today.month - birth_date.month
        days_remainder = today.day - birth_date.day
        if days_remainder < 0:
            months -= 1
            # 計算上個月的天數
            prev_month = today.replace(day=1) - timedelta(days=1)
            days_in_prev_month = prev_month.day
            days_remainder += days_in_prev_month
        if months < 0:
            years -= 1
            months += 12
        total_months = years * 12 + months
        
        baby_weeks = total_months  # 用月齡代替週數顯示
        baby_days = max(0, days_remainder)  # 當月剩餘天數
        baby_percent = min(100, max(0, round(total_months / 36 * 100)))  # 0-36 個月進度

        # BabyRecord 根據選中的嬰幼兒（屬於目前胎數）
        baby_records = (
            BabyRecord.objects
            .filter(baby=selected_baby)
            .order_by('date')
        )
        for r in baby_records:
            if r.weight is not None or r.height is not None:
                r_date = r.date.date() if isinstance(r.date, datetime.datetime) else r.date
                delta_days = (r_date - birth_date).days
                week = max(0, delta_days // 7)
                baby_chart_data.append({
                    'week': week,
                    'weight': float(r.weight) if r.weight is not None else None,
                    'height': float(r.height) if r.height is not None else None,
                })

    elif case:
        # 胎數存在但尚無出生資料 → 顯示懷孕週數
        menstruation_date = case.menstruation
        if not menstruation_date and case.expecteddate:
            menstruation_date = case.expecteddate - timedelta(days=280)
        if menstruation_date:
            delta = today - menstruation_date
            baby_weeks = max(1, delta.days // 7 + 1)  # 懷孕週數從第 1 週開始
            baby_days = max(0, delta.days % 7)
            baby_percent = min(100, int((delta.days / 280) * 100)) if delta.days >= 0 else 0

    # 判斷是否為懷孕狀態
    is_pregnancy_view = selected_baby is None or selected_baby.birthdaytime is None

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

        'case': case,
        'babies': babies,               # 該胎數下所有嬰幼兒
        'baby': selected_baby,          # 目前選中的嬰幼兒
        'baby_weeks': baby_weeks,
        'baby_days': baby_days,
        'baby_percent': baby_percent,
        'baby_chart_data': baby_chart_data,
        'is_pregnancy_view': is_pregnancy_view,
    }
    return render(request, 'home_baby.html', context)
