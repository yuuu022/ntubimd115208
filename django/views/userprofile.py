from datetime import timedelta

from django.shortcuts import render, redirect
from django.utils import timezone

from core.models import BabyInformation, BabyRecord, PregnancyCase, PregnancyRecord
from views.pregnancy_records import records_for_case
from views.pregnancycase import (
    get_lmp_date,
    is_pregnancy_ongoing,
    resolve_active_baby,
    resolve_active_pregnancy_case,
    sync_active_selection_from_request,
)
from views.session_utils import get_current_user_profile


def _format_number(value):
    if value is None:
        return '-'
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _latest_weight_for_selection(request, user):
    has_baby = bool(request.session.get('active_baby_id') or request.GET.get('baby_id'))
    baby = resolve_active_baby(request, user, fallback=has_baby)
    if baby and baby.birthdaytime:
        record = (
            BabyRecord.objects.filter(baby=baby)
            .exclude(weight__isnull=True)
            .order_by('-date', '-babyrecord_id')
            .first()
        )
        if record and record.weight is not None:
            return record.weight

    case = resolve_active_pregnancy_case(request, user)
    if case:
        record = (
            records_for_case(case)
            .exclude(weight__isnull=True)
            .order_by('-check_date', '-pregnancyrecord_id')
            .first()
        )
        if record and record.weight is not None:
            return record.weight

    return '-'


def _build_selected_child_info(request, current_user):
    sync_active_selection_from_request(request, current_user)
    today = timezone.now().date()
    active_baby_id = request.session.get('active_baby_id')

    if active_baby_id:
        baby = resolve_active_baby(request, current_user, fallback=True)
        if baby and baby.baby_id == active_baby_id:
            birth_date = baby.birthdaytime.date() if baby.birthdaytime else None
            age_text = '-'
            age_percent = 0
            if birth_date:
                age_days = max(0, (today - birth_date).days)
                age_weeks = age_days // 7
                age_days_remainder = age_days % 7
                age_text = f'第 {age_weeks} 週 {age_days_remainder} 天'
                age_percent = min(100, int((age_days / 364) * 100))

            return {
                'type': 'baby',
                'name': baby.name,
                'icon': 'face',
                'subtitle': baby.pregnancycase.code if baby.pregnancycase else '嬰兒資訊',
                'age_text': age_text,
                'age_percent': age_percent,
                'birth_date': birth_date.strftime('%Y / %m / %d') if birth_date else '-',
                'birth_height': _format_number(baby.baby_height),
                'birth_weight': _format_number(baby.baby_weight),
                'birth_head_circumference': _format_number(baby.babyheadcircumference),
            }

    case = resolve_active_pregnancy_case(request, current_user)
    if case and is_pregnancy_ongoing(case):
        menstruation_date = get_lmp_date(case)
        pregnancy_month_text = '-'
        remaining_days_text = '-'
        progress_percent = 0
        if menstruation_date:
            elapsed_days = max(0, (today - menstruation_date).days)
            pregnancy_month_text = f'第 {elapsed_days // 30 + 1} 個月'
            expected_date = case.expecteddate or (menstruation_date + timedelta(days=280))
            remaining_days = max(0, (expected_date - today).days)
            remaining_days_text = f'剩餘 {remaining_days} 天'
            progress_percent = min(100, int((elapsed_days / 280) * 100))

        return {
            'type': 'pregnancy',
            'name': getattr(case, 'order_name', case.code),
            'icon': 'pregnant_woman',
            'subtitle': case.code,
            'pregnancy_month_text': pregnancy_month_text,
            'remaining_days_text': remaining_days_text,
            'progress_percent': progress_percent,
            'menstruation_text': menstruation_date.strftime('%Y / %m / %d') if menstruation_date else '-',
            'expecteddate_text': case.expecteddate.strftime('%Y / %m / %d') if case.expecteddate else '-',
        }

    baby = resolve_active_baby(request, current_user)
    if baby and baby.birthdaytime:
        birth_date = baby.birthdaytime.date()
        age_days = max(0, (today - birth_date).days)
        return {
            'type': 'baby',
            'name': baby.name,
            'icon': 'face',
            'subtitle': baby.pregnancycase.code if baby.pregnancycase else '嬰兒資訊',
            'age_text': f'第 {age_days // 7} 週 {age_days % 7} 天',
            'age_percent': min(100, int((age_days / 364) * 100)),
            'birth_date': birth_date.strftime('%Y / %m / %d'),
            'birth_height': _format_number(baby.baby_height),
            'birth_weight': _format_number(baby.baby_weight),
            'birth_head_circumference': _format_number(baby.babyheadcircumference),
        }

    return None


def userprofile(request):
    current_user = get_current_user_profile(request)
    if not current_user:
        return redirect('login')

    latest_weight = _latest_weight_for_selection(request, current_user)
    selected_child_info = _build_selected_child_info(request, current_user)

    return render(request, 'user/userprofile.html', {
        'current_user': current_user,
        'latest_weight': latest_weight,
        'selected_child_info': selected_child_info,
    })


def edit_userprofile(request):
    current_user = get_current_user_profile(request)
    if not current_user:
        return redirect('login')

    return render(request, 'user/edit_userprofile.html', {
        'current_user': current_user,
    })


def edit_family_member(request):
    return render(request, 'user/edit_family_member.html')
