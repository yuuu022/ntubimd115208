import calendar
import random
import string
from datetime import datetime, timedelta
from urllib.parse import urlencode

from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from core.models import BabyInformation, PregnancyCase, FamilyMember
from views.session_utils import get_current_user_profile


# --- Pregnancy status (gestation, ongoing vs born) ---
# 經期推算
def get_lmp_date(case):
    """Last menstrual period date, or estimated from expected due date."""
    if case.menstruation:
        return case.menstruation
    if case.expecteddate:
        return case.expecteddate - timedelta(days=280)
    return None


# 懷孕進度
def get_gestation_parts(case, on_date=None):
    """以 LMP 為基準計算目前懷孕週數、天數與進度百分比。"""
    on_date = on_date or timezone.now().date()
    lmp = get_lmp_date(case)
    if not lmp:
        return None
    # timezone-aware datetime 傳入時需先轉 date，否則減法會型別錯誤
    if not isinstance(on_date, type(lmp)):
        try:
            on_date = on_date.date() if hasattr(on_date, 'date') else on_date
        except Exception:
            return None
    delta = on_date - lmp
    if delta.days < 0:
        return None
    # 週數從第 1 週起算；上限 42w 防止超預產期後顯示異常大數字
    weeks = min(42, delta.days // 7 + 1)
    days = delta.days % 7
    progress_percent = min(100, max(0, round(delta.days / 280 * 100)))
    return {
        'weeks': weeks,
        'days': days,
        'total_days': delta.days,
        'progress_percent': progress_percent,
        'is_overdue': delta.days > 294,
    }


def get_gestation_text(case, on_date=None):
    """Weeks + days since LMP for an ongoing pregnancy."""
    parts = get_gestation_parts(case, on_date)
    if not parts:
        return "未知週數"
    return f"{parts['weeks']}w {parts['days']}d"


def get_pregnancy_status(case, on_date=None):
    """
    回傳 'pregnant' | 'overdue' | 'born'。
    overdue = 仍有未出生嬰幼兒且已超預產期；born = 所有嬰幼兒皆已出生。
    """
    on_date = on_date or timezone.now().date()
    babies = list(case.babyinformation_set.all())

    if babies:
        # 所有嬰幼兒都有出生日期才算 born；否則繼續判斷是否超期
        if all(b.birthdaytime is not None for b in babies):
            return 'born'

    # 尚未登記出生 → 以預產期後兩週
    due = case.expecteddate or (
        get_lmp_date(case) + timedelta(days=280) if get_lmp_date(case) else None
    )
    lmp = get_lmp_date(case)
    if lmp and (on_date - lmp).days > 294:
        return 'overdue'
    elif due and not lmp and on_date > due + timedelta(days=14):
        return 'overdue'
    return 'pregnant'


def is_pregnancy_ongoing(case, on_date=None):
    """pregnant/overdue 都屬於「進行中」，born 才算結束。"""
    return get_pregnancy_status(case, on_date) in ('pregnant', 'overdue')


def get_case_display_baby(case):
    """Baby shown in pregnancy UI: first without birth date, else first baby."""
    babies = list(case.babyinformation_set.all())
    if not babies:
        return None
    for baby in babies:
        if baby.birthdaytime is None:
            return baby
    return babies[0]


# 年齡計算
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


def partition_pregnancy_cases(cases, on_date=None):
    
    """Split cases into ongoing pregnancies and born babies."""
    on_date = on_date or timezone.now().date()
    ongoing_cases = []
    born_babies = []

    for case in cases:
        status = get_pregnancy_status(case, on_date)
        if status in ('pregnant', 'overdue'):
            case.gestation_text = get_gestation_text(case, on_date)
            case.display_baby = get_case_display_baby(case)
            case.is_overdue = (status == 'overdue')
            case.all_babies = list(case.babyinformation_set.all().order_by('baby_id'))
            ongoing_cases.append(case)
            continue

        for baby in case.babyinformation_set.all().order_by('baby_id'):
            if not baby.birthdaytime:
                continue
            baby._case_id = case.pregnancycase_id 
            baby.age_text = baby_age_text(baby.birthdaytime, on_date)
            baby.birthday_str = (
                baby.birthdaytime.date()
                if isinstance(baby.birthdaytime, datetime)
                else baby.birthdaytime
            )
            if hasattr(baby.birthday_str, "strftime"):
                baby.birthday_str = baby.birthday_str.strftime("%Y-%m-%d")
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
    """Active懷孕紀錄: honors ?case_id= / ?baby_id=, then session."""
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

    display_baby = get_case_display_baby(case)
    baby_name = display_baby.name if display_baby else ''

    #懷孕中對每個寶寶各建一筆 baby-level item
    if is_pregnancy_ongoing(case):
        parts = get_gestation_parts(case, on_date)
        if not parts:
            return {
                'show_card': True,
                'is_ongoing': True,
                'baby_name': baby_name,
                'weeks': None,
                'days': None,
                'progress_percent': 0,
                'status_note': '請填寫最後月經或預產期以顯示週數',
            }

        return {
            'show_card': True,
            'is_ongoing': True,
            'baby_name': baby_name,
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

        years = on_date_val.year - bday.year
        months = on_date_val.month - bday.month
        days_remainder = on_date_val.day - bday.day
        if days_remainder < 0:
            months -= 1
            days_in_prev_month = (on_date_val.replace(day=1) - timedelta(days=1)).day
            days_remainder += days_in_prev_month
        if months < 0:
            years -= 1
            months += 12
        total_months = years * 12 + months

        baby_progress_percent = min(100, max(0, round(total_months / 36 * 100)))

        return {
            'show_card': True,
            'is_ongoing': False,
            'baby_name': baby.name,
            'status_note': f'已出生 · {baby_age_text(baby.birthdaytime, on_date)}',
            'weeks': total_months,
            'days': max(0, days_remainder),
            'progress_percent': baby_progress_percent,
        }

    return {
        'show_card': True,
        'is_ongoing': False,
        'baby_name': baby_name,
        'status_note': '此懷孕紀錄已完成',
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

    switcher_items = []
    current_date = timezone.now().date()

    for case in cases:
        display_baby = get_case_display_baby(case)
        baby_name = display_baby.name if display_baby else '懷孕紀錄'

        if is_pregnancy_ongoing(case):
            gestation = get_gestation_text(case, current_date)
            gestation_text = (
                f"懷孕中 ({gestation.split()[0]})"
                if gestation != "未知週數"
                else "懷孕中"
            )
            babies = list(case.babyinformation_set.all().order_by('baby_id'))
            if not babies:
                item = {
                    'is_baby': False,
                    'name': baby_name,
                    'desc': gestation_text,
                    'icon': 'pregnant_woman',
                    'case_id': case.pregnancycase_id,
                }
                item['url'] = build_switcher_target_url(request, item)
                switcher_items.append(item)
            else:
                for baby in babies:
                    item = {
                        'is_baby': True,
                        'name': baby.name,
                        'desc': gestation_text,
                        'icon': 'pregnant_woman',
                        'baby_id': baby.baby_id,
                        'case_id': case.pregnancycase_id,
                    }
                    item['url'] = build_switcher_target_url(request, item)
                    switcher_items.append(item)
        else:
            for baby in case.babyinformation_set.all().order_by('baby_id'):
                if baby.birthdaytime:
                    item = {
                        'is_baby': True,
                        'name': baby.name,
                        'desc': baby_age_text(baby.birthdaytime, current_date),
                        'icon': 'face',
                        'baby_id': baby.baby_id,
                        'case_id': case.pregnancycase_id,
                    }
                    item['url'] = build_switcher_target_url(request, item)
                    switcher_items.append(item)

    active_baby_id = request.session.get('active_baby_id')
    active_case_id = request.session.get('active_case_id')

    if '/pregnancyrecord' in request.path:
        ongoing_case_ids = {
            c.pregnancycase_id for c in cases
            if is_pregnancy_ongoing(c)
        }
        ongoing_items = [
            item for item in switcher_items
            if item.get('case_id') in ongoing_case_ids
        ]
        if ongoing_items:
            switcher_items = ongoing_items

    if '/babyinformation' in request.path or '/babyrecord' in request.path or '/babygrowthmap' in request.path:
        switcher_items = [item for item in switcher_items if item.get('is_baby')]
            

    


    
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
    user = get_current_user_profile(request)
    if not user:
        return redirect('login')
    
    delete_id = request.GET.get('delete_id')
    if delete_id:
        case = get_object_or_404(PregnancyCase, pregnancycase_id=delete_id)
        if case.user_id == user.user_id:
            case.delete()
        return redirect('pregnancy_case')

    cases_own = list(PregnancyCase.objects.filter(user=user))
    shared = [m.pregnancycase for m in FamilyMember.objects.filter(user_id=user).select_related('pregnancycase') if m.pregnancycase]
    cases_dict = {c.pregnancycase_id: c for c in cases_own + shared}
    cases_list = sorted(cases_dict.values(), key=lambda c: c.create_time)
    active_cases, born_babies = partition_pregnancy_cases(cases_list)


     # 標記哪些 case 是自己建的（模板用來決定是否顯示編輯/刪除）
    own_case_ids = {c.pregnancycase_id for c in cases_own}
    for case in active_cases:
        case.is_owner = case.pregnancycase_id in own_case_ids
    for baby in born_babies:
        baby.case_id_for_edit = baby._case_id    
        baby.is_owner = baby.pregnancycase_id in own_case_ids


    return render(request, 'pregnancycase/pregnancycase.html', {
        'active_cases': active_cases,
        'born_babies': born_babies,
    })


def add_pregnancy_case(request):
    if request.method == 'POST':
        user = get_current_user_profile(request)
        if not user:
            return redirect('login')
        menstruation_str = (request.POST.get('menstruation') or '').strip()
        expecteddate_str = (request.POST.get('expecteddate') or '').strip()
        code = (request.POST.get('code') or '').strip()

        # 最後月經日期為必填
        if not menstruation_str:
            generated_code = _generate_unique_code()
            return render(request, 'pregnancycase/add_pregnancy_case.html', {
                'generated_code': generated_code,
                'error': '請填寫最後一次月經日期',
                'form_data': request.POST,
            })

        try:
            menstruation = datetime.strptime(menstruation_str, '%Y-%m-%d').date()
        except ValueError:
            generated_code = _generate_unique_code()
            return render(request, 'pregnancycase/add_pregnancy_case.html', {
                'generated_code': generated_code,
                'error': '月經日期格式不正確，請重新輸入',
                'form_data': request.POST,
            })

        # 預產期：優先使用使用者填寫的值，否則自動以 Naegele's Rule 推算
        try:
            expecteddate = datetime.strptime(expecteddate_str, '%Y-%m-%d').date() if expecteddate_str else None
        except ValueError:
            expecteddate = None
        if not expecteddate:
            expecteddate = _calculate_expected_date(menstruation)

        if not code or PregnancyCase.objects.filter(code=code).exists():
            code = _generate_unique_code()

        case = PregnancyCase.objects.create(
            user=user,
            menstruation=menstruation,
            expecteddate=expecteddate,
            code=code,
            create_time=timezone.now(),
        )

        # 解析出生時間（所有嬰幼兒共用同一出生時間）
        birthdaytime_str = (request.POST.get('birthdaytime') or '').strip()
        birthdaytime = None
        if birthdaytime_str:
            try:
                birthdaytime = timezone.make_aware(datetime.strptime(birthdaytime_str, '%Y-%m-%dT%H:%M'))
            except ValueError:
                birthdaytime = None

        # 解析胎兒數：1 / 2 / 3+（三胞胎時讀取 triplet_count）
        baby_count_raw = request.POST.get('baby_count', '1')
        if baby_count_raw == '3+':
            try:
                baby_count = max(3, min(8, int(request.POST.get('triplet_count', 3))))
            except (ValueError, TypeError):
                baby_count = 3
        else:
            try:
                baby_count = max(1, min(8, int(baby_count_raw)))
            except (ValueError, TypeError):
                baby_count = 1

        # 批次建立多胎嬰幼兒資料，出生體徵資料套用至每一位
        first_baby = None
        for i in range(baby_count):
            num = i + 1
            birthdaytime_str = (
                request.POST.get(f'birthdaytime_{num}')
                or request.POST.get('birthdaytime')
                or ''
            ).strip()
            birthdaytime = None
            if birthdaytime_str:
                try:
                    birthdaytime = timezone.make_aware(datetime.strptime(birthdaytime_str, '%Y-%m-%dT%H:%M'))
                except ValueError:
                    birthdaytime = None
            name = (request.POST.get(f'baby_name_{num}') or '').strip() or f'嬰幼兒 {num}'
            baby = BabyInformation.objects.create(
                pregnancycase=case,
                name=name,
                birthdaytime=birthdaytime,
                # 出生體徵由使用者在後續「登記出生」頁面逐一填寫，此處僅儲存可選的初始值
                baby_height=_parse_float(request.POST.get(f'baby_height_{num}') or request.POST.get('baby_height')),
                baby_weight=_parse_float(request.POST.get(f'baby_weight_{num}') or request.POST.get('baby_weight')),
                babyheadcircumference=_parse_float(request.POST.get(f'baby_head_{num}') or request.POST.get('baby_head')),
                chestcircumference=_parse_float(request.POST.get(f'baby_chest_{num}') or request.POST.get('baby_chest')),
                production_method=request.POST.get(f'production_method_{num}') or request.POST.get('production_method'),
            )
            if first_baby is None:
                first_baby = baby

        # 切換 session 至第一位嬰幼兒（多胎時使用者可在嬰幼兒頁面自行切換）
        if first_baby:
            request.session['active_baby_id'] = first_baby.baby_id
            request.session.modified = True

        return redirect('pregnancy_case')

    code = _generate_unique_code()
    return render(request, 'pregnancycase/add_pregnancy_case.html', {'generated_code': code})

def edit_pregnancy_case(request):
    case_id = request.GET.get('id')
    if not case_id:
        return redirect('pregnancy_case')

    case = get_object_or_404(PregnancyCase, pregnancycase_id=case_id)
    current_user = get_current_user_profile(request)
    if not current_user or case.user_id != current_user.user_id:
        return redirect('login')

    # 取全部寶寶（多胎支援）
    babies = list(case.babyinformation_set.all().order_by('baby_id'))

    if request.method == 'POST':
        menstruation_str = (request.POST.get('menstruation') or '').strip()
        expecteddate_str = (request.POST.get('expecteddate') or '').strip()

        # 最後月經日期為必填
        if not menstruation_str:
            return render(request, 'pregnancycase/edit_pregnancy_case.html', {
                'case': case,
                'babies': babies,
                'menstruation_str': case.menstruation.strftime('%Y-%m-%d') if case.menstruation else '',
                'expecteddate_str': case.expecteddate.strftime('%Y-%m-%d') if case.expecteddate else '',
                'error': '請填寫最後一次月經日期',
            })

        try:
            case.menstruation = datetime.strptime(menstruation_str, '%Y-%m-%d').date()
        except ValueError:
            return render(request, 'pregnancycase/edit_pregnancy_case.html', {
                'case': case,
                'babies': babies,
                'menstruation_str': menstruation_str,
                'expecteddate_str': expecteddate_str,
                'error': '月經日期格式不正確，請重新輸入',
            })

        # 預產期：優先使用使用者填寫的值，否則自動推算
        try:
            case.expecteddate = datetime.strptime(expecteddate_str, '%Y-%m-%d').date() if expecteddate_str else None
        except ValueError:
            case.expecteddate = None
        if not case.expecteddate:
            case.expecteddate = _calculate_expected_date(case.menstruation)
        case.save()

        # 逐一更新每個寶寶名字（baby_name_1, baby_name_2, ...）
        for i, baby in enumerate(babies, start=1):
            new_name = (request.POST.get(f'baby_name_{i}') or '').strip()
            if new_name:
                baby.name = new_name
                baby.save()

        # 若 case 下還沒有任何寶寶，且有填 baby_name_1，則新建一筆
        if not babies:
            new_name = (request.POST.get('baby_name_1') or '').strip()
            if new_name:
                BabyInformation.objects.create(pregnancycase=case, name=new_name)

        return redirect('pregnancy_case')

    status = get_pregnancy_status(case)
    return render(request, 'pregnancycase/edit_pregnancy_case.html', {
        'case': case,
        'babies': babies,
        'menstruation_str': case.menstruation.strftime('%Y-%m-%d') if case.menstruation else '',
        'expecteddate_str': case.expecteddate.strftime('%Y-%m-%d') if case.expecteddate else '',
        'is_overdue': status == 'overdue',
    })