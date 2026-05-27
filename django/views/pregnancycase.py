import random
import string
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from core.models import UserProfile, PregnancyCase, BabyInformation

def _get_default_user():
    """Fetch the default UserProfile for testing/fallback, aligning with codebase conventions."""
    user = UserProfile.objects.filter(user_id='test_user_001').first()
    if not user:
        user = UserProfile.objects.first()
    if not user:
        user = UserProfile.objects.create(
            user_id='test_user_001',
            line_name='測試媽媽',
            avatar='avatar.jpg',
            email='test@example.com',
            password='test123'
        )
    return user

def _generate_unique_code():
    """Generate a unique 6-character alphanumeric join code."""
    while True:
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not PregnancyCase.objects.filter(code=code).exists():
            return code

def _parse_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

def pregnancy_case(request):
    # Support deletion of pregnancy case via GET query parameter
    delete_id = request.GET.get('delete_id')
    if delete_id:
        case = get_object_or_404(PregnancyCase, pregnancycase_id=delete_id)
        # Note: cascade delete is handled by database/Django ORM
        case.delete()
        return redirect('pregnancy_case')

    user = _get_default_user()
    # Retrieve all pregnancy cases for this user, ordered by creation time ascending
    cases = PregnancyCase.objects.filter(user=user).order_by('create_time')
    cases_list = list(cases)

    # Calculate ordinal names (e.g., 第一胎, 第二胎, 第三胎)
    CHINESE_NUMS = ["", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
    for idx, case in enumerate(cases_list):
        order = idx + 1
        if 1 <= order <= 10:
            case.order_name = f"第{CHINESE_NUMS[order]}胎"
        else:
            case.order_name = f"第{order}胎"

    active_cases = []
    born_babies = []
    current_date = timezone.now().date()

    for case in cases_list:
        babies = list(case.babies.all())
        # If there are no babies or if any baby has no birth date, consider it active (pregnancy in progress)
        is_active = False
        if not babies:
            is_active = True
        else:
            if any(b.birthdaytime is None for b in babies):
                is_active = True

        if is_active:
            # Calculate gestation age (weeks + days)
            menstruation_date = case.menstruation
            if not menstruation_date and case.expecteddate:
                # Estimate menstruation date if expecteddate is present
                menstruation_date = case.expecteddate - timezone.timedelta(days=280)

            if menstruation_date:
                delta = current_date - menstruation_date
                weeks = delta.days // 7
                days = delta.days % 7
                case.gestation_text = f"{weeks}w {days}d"
            else:
                case.gestation_text = "未知週數"

            active_cases.append(case)
        else:
            # Born babies listing
            for baby in babies:
                if baby.birthdaytime:
                    bday = baby.birthdaytime.date()
                    delta_years = current_date.year - bday.year
                    delta_months = current_date.month - bday.month
                    if delta_months < 0:
                        delta_years -= 1
                        delta_months += 12
                    baby.age_text = f"{delta_years}歲 {delta_months}個月"
                    baby.birthday_str = bday.strftime('%Y-%m-%d')
                    baby.case_order_name = case.order_name
                    born_babies.append(baby)

    context = {
        'active_cases': active_cases,
        'born_babies': born_babies,
    }
    return render(request, 'pregnancycase/pregnancycase.html', context)

def add_pregnancy_case(request):
    if request.method == 'POST':
        user = _get_default_user()
        menstruation_str = request.POST.get('menstruation')
        expecteddate_str = request.POST.get('expecteddate')
        code = request.POST.get('code')

        menstruation = datetime.strptime(menstruation_str, '%Y-%m-%d').date() if menstruation_str else None
        expecteddate = datetime.strptime(expecteddate_str, '%Y-%m-%d').date() if expecteddate_str else None

        case = PregnancyCase.objects.create(
            user=user,
            menstruation=menstruation,
            expecteddate=expecteddate,
            code=code or _generate_unique_code(),
            create_time=timezone.now()
        )

        baby_name = request.POST.get('baby_name')
        birthdaytime_str = request.POST.get('birthdaytime')
        birthdaytime = timezone.make_aware(datetime.strptime(birthdaytime_str, '%Y-%m-%dT%H:%M')) if birthdaytime_str else None

        BabyInformation.objects.create(
            pregnancycase=case,
            name=baby_name or "小寶",
            birthdaytime=birthdaytime,
            baby_height=_parse_float(request.POST.get('baby_height')),
            baby_weight=_parse_float(request.POST.get('baby_weight')),
            babyheadcircumference=_parse_float(request.POST.get('baby_head')),
            chestcircumference=_parse_float(request.POST.get('baby_chest')),
            production_method=request.POST.get('production_method')
        )

        return redirect('pregnancy_case')

    code = _generate_unique_code()
    return render(request, 'pregnancycase/add_pregnancy_case.html', {'generated_code': code})

def edit_pregnancy_case(request):
    case_id = request.GET.get('id')
    if not case_id:
        return redirect('pregnancy_case')

    case = get_object_or_404(PregnancyCase, pregnancycase_id=case_id)
    baby = case.babies.first()

    if request.method == 'POST':
        menstruation_str = request.POST.get('menstruation')
        expecteddate_str = request.POST.get('expecteddate')

        case.menstruation = datetime.strptime(menstruation_str, '%Y-%m-%d').date() if menstruation_str else None
        case.expecteddate = datetime.strptime(expecteddate_str, '%Y-%m-%d').date() if expecteddate_str else None
        case.save()

        baby_name = request.POST.get('baby_name')
        if baby_name:
            if baby:
                baby.name = baby_name
                baby.save()
            else:
                BabyInformation.objects.create(
                    pregnancycase=case,
                    name=baby_name
                )

        return redirect('pregnancy_case')

    menstruation_str = case.menstruation.strftime('%Y-%m-%d') if case.menstruation else ""
    expecteddate_str = case.expecteddate.strftime('%Y-%m-%d') if case.expecteddate else ""
    baby_name = baby.name if baby else ""

    context = {
        'case': case,
        'menstruation_str': menstruation_str,
        'expecteddate_str': expecteddate_str,
        'baby_name': baby_name,
    }
    return render(request, 'pregnancycase/edit_pregnancy_case.html', context)
