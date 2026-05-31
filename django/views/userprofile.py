from datetime import timedelta

from django.shortcuts import render, redirect
from django.utils import timezone

from core.models import BabyInformation, PregnancyCase, PregnancyRecord
from views.session_utils import get_current_user_profile


def _format_number(value):
    if value is None:
        return '-'
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _build_selected_child_info(request, current_user):
    active_baby_id = request.session.get('active_baby_id')
    active_case_id = request.session.get('active_case_id')
    today = timezone.now().date()

    if active_baby_id:
        baby = (
            BabyInformation.objects
            .select_related('pregnancycase')
            .filter(baby_id=active_baby_id, pregnancycase__user=current_user)
            .first()
        )
        if baby:
            birth_date = baby.birthdaytime.date() if baby.birthdaytime else None
            age_text = '-'
            if birth_date:
                age_days = max(0, (today - birth_date).days)
                age_weeks = age_days // 7
                age_days_remainder = age_days % 7
                age_text = f'第 {age_weeks} 週 {age_days_remainder} 天'
                age_percent = min(100, int((age_days / 364) * 100)) if age_days >= 0 else 0
            else:
                age_percent = 0

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

    if active_case_id:
        case = (
            PregnancyCase.objects
            .filter(pregnancycase_id=active_case_id, user=current_user)
            .first()
        )
        if case:
            menstruation_date = case.menstruation
            if not menstruation_date and case.expecteddate:
                menstruation_date = case.expecteddate - timedelta(days=280)

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
                'name': case.code,
                'icon': 'pregnant_woman',
                'subtitle': '懷孕中',
                'pregnancy_month_text': pregnancy_month_text,
                'remaining_days_text': remaining_days_text,
                'progress_percent': progress_percent,
                'menstruation_text': menstruation_date.strftime('%Y / %m / %d') if menstruation_date else '-',
                'expecteddate_text': case.expecteddate.strftime('%Y / %m / %d') if case.expecteddate else '-',
            }

    return None

def userprofile(request):
    current_user = get_current_user_profile(request)
    if not current_user:
        return redirect('login')

    latest_record = (
        PregnancyRecord.objects
        .filter(pregnancycase__user=current_user)
        .order_by('-check_date', '-pregnancyrecord_id')
        .first()
    )

    latest_weight = latest_record.weight if latest_record and latest_record.weight is not None else '-'
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
