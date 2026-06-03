import calendar
import random
import string
from datetime import datetime, timedelta
from urllib.parse import urlencode

from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from core.models import BabyInformation, PregnancyCase, FamilyMember
from views.session_utils import get_current_user_profile

_CHINESE_NUMS = ["", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]


# --- Pregnancy status (gestation, ongoing vs born) ---
#經期推算
def get_lmp_date(case):
    """Last menstrual period date, or estimated from expected due date."""
    if case.menstruation:
        return case.menstruation
    if case.expecteddate:
        return case.expecteddate - timedelta(days=280)
    return None

#懷孕進度
def get_gestation_parts(case, on_date=None):
    """Weeks, days, and 40-week progress percent since LMP."""
    on_date = on_date or timezone.now().date()
    lmp = get_lmp_date(case)
    if not lmp:
        return None
    delta = on_date - lmp
    if delta.days < 0:
        return None
    weeks = delta.days // 7 + 1  # 懷孕週數從第1週開始
    days = delta.days % 7
    progress_percent = min(100, max(0, round(delta.days / 280 * 100)))
    return {
        'weeks': weeks,
        'days': days,
        'total_days': delta.days,
        'progress_percent': progress_percent,
    }


def get_gestation_text(case, on_date=None):
    """Weeks + days since LMP for an ongoing pregnancy."""
    parts = get_gestation_parts(case, on_date)
    if not parts:
        return "未知週數"
    return f"{parts['weeks']}w {parts['days']}d"


def is_pregnancy_ongoing(case):
    """
    Ongoing pregnancy: no baby rows yet, or at least one baby without birth datetime.
    """
    babies = list(case.babyinformation_set.all())
    if not babies:
        return True
    return any(b.birthdaytime is None for b in babies)


def get_case_display_baby(case):
    """Baby shown in pregnancy UI: first without birth date, else first baby."""
    babies = list(case.babyinformation_set.all())
    if not babies:
        return None
    for baby in babies:
        if baby.birthdaytime is None:
            return baby
    return babies[0]

#年齡計算
def baby_age_text(birthdaytime, on_date=None):
    if not birthdaytime:
        return ""
    on_date = on_date or timezone.now().date()
    if isinstance(birthdaytime, datetime):
        bday = birthdaytime.date()
    else:
        bday = birthdaytime

    years = on_date.year - bday.year
    months = on_date.month - bday.month
    if on_date.day < bday.day:
        months -= 1
    if months < 0:
        years -= 1
        months += 12
    return f"{years}歲 {months}個月"


def annotate_case_order_names(cases):
    for idx, case in enumerate(cases):
        order = idx + 1
        if 1 <= order <= 10:
            case.order_name = f"第{_CHINESE_NUMS[order]}胎"
        else:
            case.order_name = f"第{order}胎"


def get_case_order_name(case):
    if not case:
        return ""
    cases = list(PregnancyCase.objects.filter(user_id=case.user).order_by('create_time'))
    annotate_case_order_names(cases)
    return getattr(case, 'order_name', '') or next(
        (c.order_name for c in cases if c.pregnancycase_id == case.pregnancycase_id),
        '',
    )


def partition_pregnancy_cases(cases, on_date=None):
    """Split cases into ongoing pregnancies and born babies."""
    on_date = on_date or timezone.now().date()
    ongoing_cases = []
    born_babies = []

    for case in cases:
        if is_pregnancy_ongoing(case):
            case.gestation_text = get_gestation_text(case, on_date)
            case.display_baby = get_case_display_baby(case)
            ongoing_cases.append(case)
            continue

        for baby in case.babyinformation_set.all():
            if not baby.birthdaytime:
                continue
            baby.age_text = baby_age_text(baby.birthdaytime, on_date)
            baby.birthday_str = (
                baby.birthdaytime.date()
                if isinstance(baby.birthdaytime, datetime)
                else baby.birthdaytime
            )
            if hasattr(baby.birthday_str, "strftime"):
                baby.birthday_str = baby.birthday_str.strftime("%Y-%m-%d")
            baby.case_order_name = getattr(case, "order_name", "")
            born_babies.append(baby)

    return ongoing_cases, born_babies


# --- Active selection & header switcher ---


def sync_active_selection_from_request(request, user=None):
    """Apply ?case_id= / ?baby_id= to session (must run in views before reading session)."""
    baby_id_param = request.GET.get('baby_id')
    case_id_param = request.GET.get('case_id')
    changed = False

    if baby_id_param:
        try:
            baby_qs = BabyInformation.objects.select_related('pregnancycase').filter(
                baby_id=int(baby_id_param),
            )
            baby_obj = baby_qs.first()
            if baby_obj and baby_obj.pregnancycase_id and (not user or baby_obj.pregnancycase.user == user or FamilyMember.objects.filter(pregnancycase_id=baby_obj.pregnancycase, user_id=user).exists()):
                request.session['active_baby_id'] = baby_obj.baby_id
                request.session['active_case_id'] = baby_obj.pregnancycase_id
                changed = True
        except (ValueError, TypeError):
            pass

    if case_id_param:
        try:
            case_id = int(case_id_param)
            case_qs = PregnancyCase.objects.filter(pregnancycase_id=case_id)
            case_obj = case_qs.first()
            if case_obj and (not user or case_obj.user == user or FamilyMember.objects.filter(pregnancycase_id=case_obj, user_id=user).exists()):
                request.session['active_case_id'] = case_id
                request.session.pop('active_baby_id', None)
                changed = True
        except (ValueError, TypeError):
            pass

    if changed:
        request.session.modified = True


def _case_for_user(user, case_id):
    return PregnancyCase.objects.filter(pregnancycase_id=case_id, user=user).first()


def resolve_active_pregnancy_case(request, user):
    """Active胎次: honors ?case_id= / ?baby_id=, then session."""
    if not user:
        return None

    def _get_all_cases():
        own_cases = list(PregnancyCase.objects.filter(user=user))
        shared = [m.pregnancycase for m in FamilyMember.objects.filter(user_id=user).select_related('pregnancycase') if m.pregnancycase]
        cases_dict = {c.pregnancycase_id: c for c in own_cases + shared}
        return sorted(cases_dict.values(), key=lambda c: c.create_time)

    def _case_for_user_ext(case_id):
        case = PregnancyCase.objects.filter(pregnancycase_id=case_id).first()
        if case and (case.user == user or FamilyMember.objects.filter(pregnancycase_id=case, user_id=user).exists()):
            return case
        return None

    sync_active_selection_from_request(request, user)

    case_id_param = request.GET.get('case_id')
    if case_id_param:
        try:
            case = _case_for_user_ext(int(case_id_param))
            if case:
                return case
        except (ValueError, TypeError):
            pass

    baby_id_param = request.GET.get('baby_id')
    if baby_id_param:
        try:
            baby = BabyInformation.objects.select_related('pregnancycase').filter(
                baby_id=int(baby_id_param),
            ).first()
            if baby and baby.pregnancycase and (baby.pregnancycase.user == user or FamilyMember.objects.filter(pregnancycase_id=baby.pregnancycase, user_id=user).exists()):
                return baby.pregnancycase
        except (ValueError, TypeError):
            pass

    active_case_id = request.session.get('active_case_id')
    if active_case_id:
        case = _case_for_user_ext(active_case_id)
        if case:
            return case

    cases = _get_all_cases()
    for case in cases:
        if is_pregnancy_ongoing(case):
            request.session['active_case_id'] = case.pregnancycase_id
            request.session.pop('active_baby_id', None)
            return case

    if cases:
        case = cases[-1]
        request.session['active_case_id'] = case.pregnancycase_id
        return case

    return None


def resolve_active_baby(request, user, *, fallback=True):
    """Active嬰幼兒: honors ?baby_id=, then session; optional first-baby fallback."""
    if not user:
        return None

    sync_active_selection_from_request(request, user)

    for param in ('baby_id', 'id'):
        raw = request.GET.get(param) or request.POST.get(param)
        if raw:
            try:
                baby = BabyInformation.objects.select_related('pregnancycase').filter(
                    baby_id=int(raw),
                ).first()
                if baby and baby.pregnancycase and (baby.pregnancycase.user == user or FamilyMember.objects.filter(pregnancycase_id=baby.pregnancycase, user_id=user).exists()):
                    request.session['active_baby_id'] = baby.baby_id
                    if baby.pregnancycase_id:
                        request.session['active_case_id'] = baby.pregnancycase_id
                    request.session.modified = True
                    return baby
            except (ValueError, TypeError):
                pass

    active_baby_id = request.session.get('active_baby_id')
    if active_baby_id:
        baby = BabyInformation.objects.select_related('pregnancycase').filter(
            baby_id=active_baby_id,
        ).first()
        if baby and baby.pregnancycase and (baby.pregnancycase.user == user or FamilyMember.objects.filter(pregnancycase_id=baby.pregnancycase, user_id=user).exists()):
            return baby

    if not fallback:
        return None

    case = resolve_active_pregnancy_case(request, user)
    if case:
        baby = BabyInformation.objects.select_related('pregnancycase').filter(
            pregnancycase=case
        ).order_by('baby_id').first()
    else:
        baby = None
    if baby:
        request.session['active_baby_id'] = baby.baby_id
        if baby.pregnancycase_id:
            request.session['active_case_id'] = baby.pregnancycase_id
        request.session.modified = True
    return baby


def build_active_selection_query(request):
    """Query string fragment to keep the current child/case across pages."""
    if request.session.get('active_baby_id'):
        return urlencode({'baby_id': request.session['active_baby_id']})
    if request.session.get('active_case_id'):
        return urlencode({'case_id': request.session['active_case_id']})
    return ''


def url_with_active_selection(request, path, extra_params=None):
    """Build path + active baby/case (+ optional date etc.)."""
    params = {}
    if request.session.get('active_baby_id'):
        params['baby_id'] = request.session['active_baby_id']
    elif request.session.get('active_case_id'):
        params['case_id'] = request.session['active_case_id']
    if extra_params:
        params.update(extra_params)
    if not params:
        return path
    joiner = '&' if '?' in path else '?'
    return f'{path}{joiner}{urlencode(params)}'


def build_switcher_target_url(request, item):
    """Preserve current path and date filter; switch active case or baby."""
    params = {}
    for key in ('date',):
        value = request.GET.get(key)
        if value:
            params[key] = value

    if item.get('is_baby'):
        params['baby_id'] = item['baby_id']
    else:
        params['case_id'] = item['case_id']

    query = urlencode(params)
    path = request.path or '/'
    return f'{path}?{query}' if query else path


def build_pregnancy_progress(case, on_date=None):
    """Progress card payload for the index page."""
    if not case:
        return {'show_card': False, 'is_ongoing': False}

    order_name = getattr(case, 'order_name', None) or get_case_order_name(case)
    display_baby = get_case_display_baby(case)

    if is_pregnancy_ongoing(case):
        parts = get_gestation_parts(case, on_date)
        if not parts:
            return {
                'show_card': True,
                'is_ongoing': True,
                'order_name': order_name,
                'baby_name': display_baby.name if display_baby else '',
                'weeks': None,
                'days': None,
                'progress_percent': 0,
                'status_note': '請填寫最後月經或預產期以顯示週數',
            }

        return {
            'show_card': True,
            'is_ongoing': True,
            'order_name': order_name,
            'baby_name': display_baby.name if display_baby else '',
            'weeks': parts['weeks'],
            'days': parts['days'],
            'progress_percent': parts['progress_percent'],
            'status_note': '',
        }

    baby = display_baby
    if baby and baby.birthdaytime:
        # 計算寶寶月齡相對3歲（36個月）的進度
        if isinstance(baby.birthdaytime, datetime):
            bday = baby.birthdaytime.date()
        else:
            bday = baby.birthdaytime
        on_date_val = on_date or timezone.now().date()
        
        # 計算月齡
        years = on_date_val.year - bday.year
        months = on_date_val.month - bday.month
        days_remainder = on_date_val.day - bday.day
        if days_remainder < 0:
            months -= 1
            # 計算上個月的天數
            prev_month = on_date_val.replace(day=1) - timedelta(days=1)
            days_in_prev_month = (on_date_val.replace(day=1) - timedelta(days=1)).day
            days_remainder += days_in_prev_month
        if months < 0:
            years -= 1
            months += 12
        total_months = years * 12 + months
        
        # 計算 0-3 歲進度 (36 個月)
        baby_progress_percent = min(100, max(0, round(total_months / 36 * 100)))
        
        return {
            'show_card': True,
            'is_ongoing': False,
            'order_name': order_name,
            'baby_name': baby.name,
            'status_note': f'已出生 · {baby_age_text(baby.birthdaytime, on_date)}',
            'weeks': total_months,  # 改用月齡顯示
            'days': max(0, days_remainder),  # 當月剩餘天數
            'progress_percent': baby_progress_percent,
        }

    return {
        'show_card': True,
        'is_ongoing': False,
        'order_name': order_name,
        'baby_name': '',
        'status_note': '此胎次已完成',
        'weeks': None,
        'days': None,
        'progress_percent': 100,
    }


def baby_switcher(request):
    """Context processor: baby/pregnancy switcher in base.html."""
    user = get_current_user_profile(request)
    if not user:
        return {}

    sync_active_selection_from_request(request, user)

    cases_own = list(PregnancyCase.objects.filter(user=user))
    shared = [m.pregnancycase for m in FamilyMember.objects.filter(user_id=user).select_related('pregnancycase') if m.pregnancycase]
    cases_dict = {c.pregnancycase_id: c for c in cases_own + shared}
    cases = sorted(cases_dict.values(), key=lambda c: c.create_time)
    annotate_case_order_names(cases)

    switcher_items = []
    current_date = timezone.now().date()

    for case in cases:
        if is_pregnancy_ongoing(case):
            gestation = get_gestation_text(case, current_date)
            gestation_text = (
                f"懷孕中 ({gestation.split()[0]})"
                if gestation != "未知週數"
                else "懷孕中"
            )
            item = {
                'is_baby': False,
                'name': case.order_name,
                'desc': gestation_text,
                'icon': 'pregnant_woman',
                'case_id': case.pregnancycase_id,
            }
            item['url'] = build_switcher_target_url(request, item)
            switcher_items.append(item)
        else:
            for baby in case.babyinformation_set.all():
                if baby.birthdaytime:
                    item = {
                        'is_baby': True,
                        'name': baby.name,
                        'desc': case.order_name,
                        'icon': 'face',
                        'baby_id': baby.baby_id,
                        'case_id': case.pregnancycase_id,
                    }
                    item['url'] = build_switcher_target_url(request, item)
                    switcher_items.append(item)

    active_baby_id = request.session.get('active_baby_id')
    active_case_id = request.session.get('active_case_id')

    if '/pregnancyrecord' in request.path:
        switcher_items = [item for item in switcher_items if not item['is_baby']]

    active_item = None
    if active_baby_id:
        active_item = next(
            (item for item in switcher_items if item.get('is_baby') and item.get('baby_id') == active_baby_id),
            None,
        )
    if not active_item and active_case_id:
        active_item = next(
            (item for item in switcher_items if item.get('case_id') == active_case_id),
            None,
        )
    if not active_item and switcher_items:
        active_item = switcher_items[0]

    return {
        'switcher_items': switcher_items,
        'switcher_active_item': active_item,
        'active_case_id': active_case_id,
        'active_baby_id': active_baby_id,
        'active_selection_query': build_active_selection_query(request),
    }


# --- Pregnancy case CRUD views ---


def _calculate_expected_date(menstruation):
    """EDD from LMP: Naegele's rule (month −3, day +7, year +1), same as +280 days."""
    if not menstruation:
        return None
    year = menstruation.year + 1
    month = menstruation.month - 3
    if month <= 0:
        month += 12
        year -= 1
    day = min(menstruation.day, calendar.monthrange(year, month)[1])
    due = menstruation.replace(year=year, month=month, day=day) + timedelta(days=7)
    return due


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
    delete_id = request.GET.get('delete_id')
    if delete_id:
        case = get_object_or_404(PregnancyCase, pregnancycase_id=delete_id)
        case.delete()
        return redirect('pregnancy_case')

    user = get_current_user_profile(request)
    if not user:
        return redirect('login')

    cases_own = list(PregnancyCase.objects.filter(user=user))
    shared = [m.pregnancycase for m in FamilyMember.objects.filter(user_id=user).select_related('pregnancycase') if m.pregnancycase]
    cases_dict = {c.pregnancycase_id: c for c in cases_own + shared}
    cases_list = sorted(cases_dict.values(), key=lambda c: c.create_time)
    annotate_case_order_names(cases_list)
    active_cases, born_babies = partition_pregnancy_cases(cases_list)

    return render(request, 'pregnancycase/pregnancycase.html', {
        'active_cases': active_cases,
        'born_babies': born_babies,
    })


def add_pregnancy_case(request):
    if request.method == 'POST':
        user = get_current_user_profile(request)
        if not user:
            return redirect('login')
        menstruation_str = request.POST.get('menstruation')
        expecteddate_str = request.POST.get('expecteddate')
        code = request.POST.get('code')

        menstruation = datetime.strptime(menstruation_str, '%Y-%m-%d').date() if menstruation_str else None
        expecteddate = datetime.strptime(expecteddate_str, '%Y-%m-%d').date() if expecteddate_str else None
        if menstruation and not expecteddate:
            expecteddate = _calculate_expected_date(menstruation)

        case = PregnancyCase.objects.create(
            user=user,
            menstruation=menstruation,
            expecteddate=expecteddate,
            code=code or _generate_unique_code(),
            create_time=timezone.now(),
        )

        baby_name = request.POST.get('baby_name')
        birthdaytime_str = request.POST.get('birthdaytime')
        birthdaytime = (
            timezone.make_aware(datetime.strptime(birthdaytime_str, '%Y-%m-%dT%H:%M'))
            if birthdaytime_str
            else None
        )

        BabyInformation.objects.create(
            pregnancycase=case,
            name=baby_name or "小寶",
            birthdaytime=birthdaytime,
            baby_height=_parse_float(request.POST.get('baby_height')),
            baby_weight=_parse_float(request.POST.get('baby_weight')),
            babyheadcircumference=_parse_float(request.POST.get('baby_head')),
            chestcircumference=_parse_float(request.POST.get('baby_chest')),
            production_method=request.POST.get('production_method'),
        )

        return redirect('pregnancy_case')

    code = _generate_unique_code()
    return render(request, 'pregnancycase/add_pregnancy_case.html', {'generated_code': code})


def edit_pregnancy_case(request):
    case_id = request.GET.get('id')
    if not case_id:
        return redirect('pregnancy_case')

    case = get_object_or_404(PregnancyCase, pregnancycase_id=case_id)
    current_user = get_current_user_profile(request)
    if not current_user or case.user != current_user.user_id:
        return redirect('login')
    baby = case.babyinformation_set.first()

    if request.method == 'POST':
        menstruation_str = request.POST.get('menstruation')
        expecteddate_str = request.POST.get('expecteddate')

        case.menstruation = datetime.strptime(menstruation_str, '%Y-%m-%d').date() if menstruation_str else None
        case.expecteddate = datetime.strptime(expecteddate_str, '%Y-%m-%d').date() if expecteddate_str else None
        if case.menstruation and not case.expecteddate:
            case.expecteddate = _calculate_expected_date(case.menstruation)
        case.save()

        baby_name = request.POST.get('baby_name')
        if baby_name:
            if baby:
                baby.name = baby_name
                baby.save()
            else:
                BabyInformation.objects.create(pregnancycase=case, name=baby_name)

        return redirect('pregnancy_case')

    return render(request, 'pregnancycase/edit_pregnancy_case.html', {
        'case': case,
        'menstruation_str': case.menstruation.strftime('%Y-%m-%d') if case.menstruation else "",
        'expecteddate_str': case.expecteddate.strftime('%Y-%m-%d') if case.expecteddate else "",
        'baby_name': baby.name if baby else "",
    })
