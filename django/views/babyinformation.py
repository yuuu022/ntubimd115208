import calendar
import datetime

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from core.models import BabyInformation, BabyRecord, BabyGrowthMap, BabyStatus, PregnancyCase, FamilyMember
from views.pregnancycase import url_with_active_selection
from django.db.models import Q
from django.utils import timezone

MILESTONE_PREFIX = '里程碑：'


def _calculate_age_in_months(birthdaytime, record_date):
    if not birthdaytime or not record_date:
        return None
    
    if isinstance(birthdaytime, datetime.datetime):
        birth_date = birthdaytime.date()
    elif isinstance(birthdaytime, datetime.date):
        birth_date = birthdaytime
    else:
        try:
            birth_date = datetime.date.fromisoformat(str(birthdaytime)[:10])
        except Exception:
            return None

    if isinstance(record_date, datetime.datetime):
        rec_date = record_date.date()
    elif isinstance(record_date, datetime.date):
        rec_date = record_date
    else:
        try:
            rec_date = datetime.date.fromisoformat(str(record_date)[:10])
        except Exception:
            return None

    delta = rec_date - birth_date
    if delta.days < 0:
        return 0
        
    # 以 30.4375 天為一個月計算月齡
    age_in_months = int(delta.days / 30.4375)
    return age_in_months


def _get_relevant_timecourses(age_in_months):
    if age_in_months is None:
        return None
        
    if age_in_months <= 0:
        age_in_months = 1
        
    if age_in_months <= 11:
        m = max(1, age_in_months)
        courses = {max(1, m - 1), m, m + 1}
        return sorted(list(courses))
    elif age_in_months == 12:
        return [11, 12, 18]
    elif age_in_months < 18:
        return [12, 18]
    elif age_in_months == 18:
        return [12, 18, 24]
    elif age_in_months < 24:
        return [18, 24]
    elif age_in_months == 24:
        return [18, 24, 36]
    elif age_in_months < 36:
        return [24, 36]
    else:
        return [36]


def _parse_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _get_calendar_data(records, selected_date):
    year = selected_date.year
    month = selected_date.month
    cal = calendar.Calendar(firstweekday=6)
    
    first_weekday, days_in_month = calendar.monthrange(year, month)
    leading_blanks = (first_weekday + 1) % 7
    
    cells = []
    for _ in range(leading_blanks):
        cells.append({'empty': True})
        
    record_days = {}
    for rec in records:
        rec_date = rec.date.date() if hasattr(rec.date, 'date') else rec.date
        if rec_date.year == year and rec_date.month == month:
            record_days[rec_date.day] = rec
            
    for day in range(1, days_in_month + 1):
        d = datetime.date(year, month, day)
        cells.append({
            'empty': False,
            'day': day,
            'date_iso': d.isoformat(),
            'is_selected': d == selected_date,
            'has_record': d.day in record_days,
        })
        
    while len(cells) % 7 != 0:
        cells.append({'empty': True})
        
    calendar_weeks = [cells[i:i+7] for i in range(0, len(cells), 7)]
    while len(calendar_weeks) < 5:
        empty_week = [{'empty': True} for _ in range(7)]
        calendar_weeks.append(empty_week)
        
    today = datetime.date.today()
    record_years = {today.year, year} | {rec.date.year for rec in records if hasattr(rec.date, 'year')}
    
    return {
        'calendar_weeks': calendar_weeks,
        'selected_year': year,
        'selected_month': month,
        'selected_month_label': f'{year}年 {month}月',
        'selected_date_iso': selected_date.isoformat(),
        'selected_day': selected_date.day,
        'calendar_years': sorted(record_years, reverse=True),
        'calendar_months': list(range(1, 13)),
    }


def _parse_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _save_uploaded_image(image_file):
    if not image_file:
        return None
    storage = FileSystemStorage(location=settings.MEDIA_ROOT, base_url=settings.MEDIA_URL)
    filename = storage.save(f'baby_records/{image_file.name}', image_file)
    return storage.url(filename)


def _split_note_and_milestones(text):
    if not text:
        return [], ''
    text = str(text)
    if text.startswith(MILESTONE_PREFIX):
        first_line, _, rest = text.partition('\n')
        milestones_part = first_line[len(MILESTONE_PREFIX):].strip()
        if '|' in milestones_part:
            milestones = [m.strip() for m in milestones_part.split('|') if m.strip()]
        else:
            milestones = [m.strip() for m in milestones_part.split(',') if m.strip()]
        return milestones, rest.strip()
    return [], text


def _build_record_text(note, milestones):
    note = (note or '').strip()
    milestones = (milestones or '').strip()
    if milestones:
        return f"{MILESTONE_PREFIX}{milestones}\n\n{note}".strip()
    return note


def _format_birth_datetime(baby):
    if not baby or not baby.birthdaytime:
        return None
    return baby.birthdaytime.strftime('%Y.%m.%d %H:%M')


def _format_datetime_local(baby):
    if not baby or not baby.birthdaytime:
        return ''
    return baby.birthdaytime.strftime('%Y-%m-%dT%H:%M')


def _get_baby_form_data(baby):
    if not baby:
        return {
            'baby_name': '',
            'birthdaytime_value': '',
            'birth_week': '',
            'pregnancy_order': 1,
            'pregnancy_count': 1,
            'birth_weight': '',
            'birth_height': '',
            'birth_head': '',
            'birth_chest': '',
            'production_method': '',
            'join_code': '',
        }

    pregnancy_count = 1
    if getattr(baby, 'pregnancycase', None):
        pregnancy_count = baby.pregnancycase.babyinformation_set.count() or 1

    return {
        'baby_name': baby.name or '',
        'birthdaytime_value': _format_datetime_local(baby),
        'birth_week': _get_birth_week(baby) or '',
        'pregnancy_order': 1,
        'pregnancy_count': pregnancy_count,
        'birth_weight': baby.baby_weight or '',
        'birth_height': baby.baby_height or '',
        'birth_head': baby.babyheadcircumference or '',
        'birth_chest': baby.chestcircumference or '',
        'production_method': baby.production_method or '',
        'join_code': baby.pregnancycase.code if getattr(baby, 'pregnancycase', None) else '',
    }


def _get_birth_week(baby):
    if not baby or not baby.birthdaytime or not baby.pregnancycase or not baby.pregnancycase.menstruation:
        return None
    delta = baby.birthdaytime.date() - baby.pregnancycase.menstruation
    if delta.days < 0:
        return None
    weeks = delta.days // 7
    days = delta.days % 7
    return f'{weeks}w{days}d' if days else f'{weeks}w'


def _get_baby_summary(baby):
    if not baby:
        return {
            'baby_name': '小寶',
            'birth_week': '-',
            'birth_method': '-',
            'birth_order': '-',
            'birth_time': '-',
            'birth_height': '-',
            'birth_weight': '-',
            'birth_head': '-',
            'birth_chest': '-',
            'photo_url': None,
        }

    baby_count = 1
    if baby.pregnancycase_id:
        baby_count = baby.pregnancycase.babyinformation_set.count()

    return {
        'baby_name': baby.name or '小寶',
        'birth_week': _get_birth_week(baby) or '-',
        'birth_method': baby.production_method or '-',
        'birth_order': f'第{baby_count}胎',
        'birth_time': _format_birth_datetime(baby) or '-',
        'birth_height': baby.baby_height or '-',
        'birth_weight': baby.baby_weight or '-',
        'birth_head': baby.babyheadcircumference or '-',
        'birth_chest': baby.chestcircumference or '-',
        'photo_url': None,
    }


def _get_active_baby(request):
    from views.pregnancycase import resolve_active_baby
    from views.session_utils import get_current_user_profile

    return resolve_active_baby(request, get_current_user_profile(request))


def _get_baby_milestones_summary(baby):
    if not baby:
        return []

    from views.baby_growthmap import DEFAULT_DESCRIPTIONS as MAP_DESCRIPTIONS

    growth_maps = BabyGrowthMap.objects.all().order_by('timecourse')
    baby_records = list(BabyRecord.objects.filter(baby=baby))

    growth_timeline = []
    found_in_progress = False

    for growth_map in growth_maps:
        baby_statuses = list(BabyStatus.objects.filter(babygrowthmap=growth_map, babyrecord__baby=baby))
        is_completed = len(baby_statuses) > 0
        matching_record = None

        if is_completed:
            matching_record = baby_statuses[0].babyrecord
        else:
            # 備用文字比對
            for rec in baby_records:
                milestones, note_text = _split_note_and_milestones(rec.record)
                if growth_map.growthrecord in milestones:
                    is_completed = True
                    matching_record = rec
                    break

        item_status = 'pending'
        achieved_date_str = None
        description = ""

        details = MAP_DESCRIPTIONS.get(growth_map.growthrecord)
        desc_val = details.get('desc') if (details and isinstance(details, dict)) else None

        if is_completed and matching_record:
            item_status = 'completed'
            achieved_date_str = matching_record.date.strftime('%Y.%m.%d') if hasattr(matching_record.date, 'strftime') else str(matching_record.date)
            description = desc_val
            if not description:
                description = f'恭喜寶寶達成「{growth_map.growthrecord}」里程碑！'
        else:
            if not found_in_progress:
                item_status = 'in_progress'
                found_in_progress = True
            else:
                item_status = 'pending'

            desc_key = growth_map.growthrecord
            if '新生兒' in desc_key:
                description = '趴趴抬頭練習與新手父母撫摸擁抱，增強肌張力。'
            elif '快速適應' in desc_key:
                description = '開始追視移動物體與對聲音轉頭，逐漸熟悉外界環境。'
            else:
                description = desc_val
                if not description:
                    description = f'引導與觀察寶寶在 {growth_map.timecourse} 個月左右時「{desc_key}」的成長變化。'

        growth_timeline.append({
            'growthrecord': growth_map.growthrecord,
            'timecourse': growth_map.timecourse,
            'status': item_status,
            'achieved_date': achieved_date_str,
            'description': description,
        })

    completed_items = [item for item in growth_timeline if item['status'] == 'completed']
    in_progress_items = [item for item in growth_timeline if item['status'] == 'in_progress']
    pending_items = [item for item in growth_timeline if item['status'] == 'pending']

    summary_list = []
    
    # 顯示已達成最後 2 個 + 進行中 + 下一個期待 (保持連貫)
    if completed_items:
        # 取最後 2 個已達成的
        summary_list.extend(completed_items[-2:])
    
    if in_progress_items:
        # 顯示所有進行中的 (通常只有1個)
        summary_list.extend(in_progress_items)
    
    if pending_items and len(summary_list) < 5:
        # 填補至 5 筆或用前 2 個待做的
        remaining_slots = 5 - len(summary_list)
        summary_list.extend(pending_items[:max(1, remaining_slots)])

    if not summary_list:
        summary_list = growth_timeline[:5]

    return summary_list[:5]


def baby(request):
    baby = _get_active_baby(request)
    records = []
    if baby is not None:
        records = BabyRecord.objects.filter(baby=baby).order_by('-date')
        for record in records:
            record.milestones, record.note_text = _split_note_and_milestones(record.record)

    raw = request.GET.get('date')
    try:
        selected_date = datetime.date.fromisoformat(raw) if raw else datetime.date.today()
    except Exception:
        selected_date = datetime.date.today()

    selected_day_record = None
    selected_day_records = []
    for rec in records:
        rec_date = rec.date.date() if hasattr(rec.date, 'date') else rec.date
        if rec_date == selected_date:
            selected_day_records.append(rec)

    if selected_day_records:
        # Use the first one as primary (latest due to ordering)
        primary = selected_day_records[0]
        
        merged_height = primary.height
        merged_weight = primary.weight
        merged_head = primary.headcircumference
        merged_chest = primary.chestcircumference
        
        all_milestones = []
        all_notes = []
        
        for r in selected_day_records:
            if merged_height is None and r.height is not None:
                merged_height = r.height
            if merged_weight is None and r.weight is not None:
                merged_weight = r.weight
            if merged_head is None and r.headcircumference is not None:
                merged_head = r.headcircumference
            if merged_chest is None and r.chestcircumference is not None:
                merged_chest = r.chestcircumference
                
            if r.milestones:
                for ms in r.milestones:
                    if ms not in all_milestones:
                        all_milestones.append(ms)
            if r.note_text and r.note_text.strip():
                note_stripped = r.note_text.strip()
                if note_stripped not in all_notes:
                    all_notes.append(note_stripped)
                    
        primary.height = merged_height
        primary.weight = merged_weight
        primary.headcircumference = merged_head
        primary.chestcircumference = merged_chest
        primary.milestones = all_milestones
        primary.note_text = '\n'.join(all_notes) if all_notes else ''
        
        selected_day_record = primary

    summary = _get_baby_summary(baby)
    if records:
        for r in records:
            if r.photo:
                summary['photo_url'] = r.photo
                break

    milestones_summary = _get_baby_milestones_summary(baby)

    context = {
        'baby': baby,
        'records': records,
        'baby_summary': summary,
        'baby_form': _get_baby_form_data(baby),
        'selected_date': selected_date,
        'selected_day_record': selected_day_record,
        'has_day_data': bool(selected_day_record),
        'milestones_summary': milestones_summary,
    }
    context.update(_get_calendar_data(records, selected_date))

    return render(request, 'baby/babyinformation.html', context)


def add_baby_information(request):
    from views.session_utils import get_current_user_profile
    from views.pregnancycase import resolve_active_pregnancy_case
    user = get_current_user_profile(request)
    if not user:
        return redirect('login')

    case = resolve_active_pregnancy_case(request, user)
    if not case:
        return redirect('pregnancy_case')

    if request.method == 'POST':
        baby_name = (request.POST.get('baby_name') or '').strip()
        birthdaytime_str = (request.POST.get('birthdaytime') or '').strip()
        birthdaytime = None
        if birthdaytime_str:
            try:
                naive = datetime.datetime.strptime(birthdaytime_str, '%Y-%m-%dT%H:%M')
                birthdaytime = timezone.make_aware(naive)
            except Exception:
                pass

        baby_height = _parse_float(request.POST.get('birth_height'))
        baby_weight = _parse_float(request.POST.get('birth_weight'))
        babyheadcircumference = _parse_float(request.POST.get('birth_head'))
        chestcircumference = _parse_float(request.POST.get('birth_chest'))
        production_method = (request.POST.get('production_method') or '').strip()

        new_baby = BabyInformation.objects.create(
            pregnancycase=case,
            name=baby_name or "小寶",
            birthdaytime=birthdaytime,
            baby_height=baby_height,
            baby_weight=baby_weight,
            babyheadcircumference=babyheadcircumference,
            chestcircumference=chestcircumference,
            production_method=production_method,
        )
        request.session['active_baby_id'] = new_baby.baby_id
        request.session.modified = True
        return redirect('babyinformation')

    return render(request, 'baby/add_baby_information.html', {
        'baby_form': _get_baby_form_data(None),
        'baby': None,
    })


def edit_baby_information(request):
    baby = _get_active_baby(request)
    if baby is None:
        return redirect('pregnancy_case')

    if request.method == 'POST':
        baby_name = (request.POST.get('baby_name') or '').strip()
        if baby_name:
            baby.name = baby_name

        birthdaytime_str = (request.POST.get('birthdaytime') or '').strip()
        if birthdaytime_str:
            naive = datetime.datetime.strptime(birthdaytime_str, '%Y-%m-%dT%H:%M')
            baby.birthdaytime = timezone.make_aware(naive)

        baby.baby_weight = _parse_float(request.POST.get('birth_weight'))
        baby.baby_height = _parse_float(request.POST.get('birth_height'))
        baby.babyheadcircumference = _parse_float(request.POST.get('birth_head'))
        baby.chestcircumference = _parse_float(request.POST.get('birth_chest'))
        production_method = (request.POST.get('production_method') or '').strip()
        if production_method:
            baby.production_method = production_method
        baby.save()
        return redirect('pregnancy_case')

    return render(request, 'baby/edit_baby_information.html', {
        'baby_form': _get_baby_form_data(baby),
        'baby': baby,
    })


def add_baby_record(request):
    baby = _get_active_baby(request)

    if baby is None:
        return render(request, 'baby/add_baby_record.html', {
            'error': '請先建立寶寶資料',
        })

    initial_date = request.GET.get('date', '')

    if request.method == 'POST':
        date = request.POST.get('date')
        if not date:
            return render(request, 'baby/add_baby_record.html', {
                'baby': baby,
                'error': '請填寫紀錄日期',
                'form_data': request.POST,
            })

        photo_url = _save_uploaded_image(request.FILES.get('photo'))
        milestones_str = request.POST.get('milestones', '')
        record_text = _build_record_text(request.POST.get('record', ''), milestones_str)
        
        baby_record = BabyRecord.objects.create(
            baby=baby,
            date=date,
            record=record_text,
            weight=_parse_float(request.POST.get('weight')),
            height=_parse_float(request.POST.get('height')),
            headcircumference=_parse_float(request.POST.get('headcircumference')),
            chestcircumference=_parse_float(request.POST.get('chestcircumference')),
            photo=photo_url,
        )
        
        # 建立里程碑關係對應，使成長地圖頁面能即時反映
        milestone_names = [m.strip() for m in milestones_str.split('|') if m.strip()]
        for m_name in milestone_names:
            growth_map = BabyGrowthMap.objects.filter(growthrecord=m_name).first()
            if growth_map:
                BabyStatus.objects.get_or_create(
                    babyrecord=baby_record,
                    babygrowthmap=growth_map
                )
                
        return redirect(url_with_active_selection(request, reverse('babyinformation')))

    from views.session_utils import get_current_user_profile
    user = get_current_user_profile(request)
    if not user:
        return redirect('login')
    cases_own = PregnancyCase.objects.filter(user=user)
    cases_shared = FamilyMember.objects.filter(user_id=user).values_list('pregnancycase_id', flat=True)
    baby_list = BabyInformation.objects.filter(
        Q(pregnancycase__in=cases_own) | Q(pregnancycase_id__in=cases_shared)
    ).distinct()
    try:
        record_date = datetime.date.fromisoformat(initial_date) if initial_date else datetime.date.today()
    except Exception:
        record_date = datetime.date.today()

    age_in_months = _calculate_age_in_months(baby.birthdaytime, record_date)
    relevant_courses = _get_relevant_timecourses(age_in_months)

    # 找出該寶寶過去已勾選並儲存的所有里程碑 ID 列表
    achieved_ids = BabyStatus.objects.filter(babyrecord__baby=baby).values_list('babygrowthmap_id', flat=True)

    if relevant_courses:
        all_milestones = BabyGrowthMap.objects.filter(
            timecourse__in=relevant_courses
        ).exclude(
            babygrowthmap_id__in=achieved_ids
        ).order_by('timecourse')
    else:
        all_milestones = BabyGrowthMap.objects.all().exclude(
            babygrowthmap_id__in=achieved_ids
        ).order_by('timecourse')

    return render(request, 'baby/add_baby_record.html', {
        'baby': baby,
        'baby_list': baby_list,
        'all_milestones': all_milestones,
        'form_data': {'date': record_date.isoformat()},
        'milestones': '',
    })


def edit_baby_record(request, babyrecord_id):
    from views.session_utils import get_current_user_profile
    from django.core.exceptions import PermissionDenied

    user = get_current_user_profile(request)
    if not user:
        return redirect('login')

    record = get_object_or_404(BabyRecord, babyrecord_id=babyrecord_id)
    case = record.baby.pregnancycase
    is_owner = (case.user_id == user.user_id)
    is_shared = FamilyMember.objects.filter(pregnancycase_id=case, user_id=user).exists()
    if not (is_owner or is_shared):
        raise PermissionDenied("您沒有權限編輯此紀錄")

    record.milestones, record.note_text = _split_note_and_milestones(record.record)

    if request.method == 'POST':
        date = request.POST.get('date')
        if not date:
            return render(request, 'baby/edit_baby_record.html', {
                'record': record,
                'error': '請填寫紀錄日期',
                'form_data': request.POST,
                'selected_milestones': request.POST.get('milestones', ''),
            })

        record.date = date
        milestones_str = request.POST.get('milestones', '')
        record.record = _build_record_text(request.POST.get('record', ''), milestones_str)
        record.weight = _parse_float(request.POST.get('weight'))
        record.height = _parse_float(request.POST.get('height'))
        record.headcircumference = _parse_float(request.POST.get('headcircumference'))
        record.chestcircumference = _parse_float(request.POST.get('chestcircumference'))
        photo_url = _save_uploaded_image(request.FILES.get('photo'))
        if photo_url:
            record.photo = photo_url
        record.update_time = timezone.now()
        record.save()

        # 同步更新里程碑關係對應
        BabyStatus.objects.filter(babyrecord=record).delete()
        milestone_names = [m.strip() for m in milestones_str.split('|') if m.strip()]
        for m_name in milestone_names:
            growth_map = BabyGrowthMap.objects.filter(growthrecord=m_name).first()
            if growth_map:
                BabyStatus.objects.create(
                    babyrecord=record,
                    babygrowthmap=growth_map
                )

        return redirect(url_with_active_selection(request, reverse('babyinformation')))

    # 根據紀錄當天的日期計算寶寶月齡，並動態過濾
    record_date = record.date
    baby = record.baby
    age_in_months = _calculate_age_in_months(baby.birthdaytime, record_date)
    relevant_courses = _get_relevant_timecourses(age_in_months)

    # 找出除了目前編輯的這一篇紀錄之外，該寶寶在其他篇紀錄已達成的里程碑 ID 列表
    achieved_ids_other = BabyStatus.objects.filter(
        babyrecord__baby=baby
    ).exclude(
        babyrecord=record
    ).values_list('babygrowthmap_id', flat=True)

    if relevant_courses:
        # 除了時間區間內，也要包含該紀錄本身已勾選的里程碑以防遺失，但需排除其他天已達成的里程碑
        all_milestones = BabyGrowthMap.objects.filter(
            Q(timecourse__in=relevant_courses) | Q(growthrecord__in=record.milestones)
        ).exclude(
            babygrowthmap_id__in=achieved_ids_other
        ).distinct().order_by('timecourse')
    else:
        all_milestones = BabyGrowthMap.objects.all().exclude(
            babygrowthmap_id__in=achieved_ids_other
        ).order_by('timecourse')

    return render(request, 'baby/edit_baby_record.html', {
        'record': record,
        'all_milestones': all_milestones,
        'form_data': {'record': record.note_text},
        'selected_milestones': '|'.join(record.milestones),
    })


def delete_baby_record(request, babyrecord_id):
    from views.session_utils import get_current_user_profile
    from django.core.exceptions import PermissionDenied

    user = get_current_user_profile(request)
    if not user:
        return redirect('login')

    record = get_object_or_404(BabyRecord, babyrecord_id=babyrecord_id)
    case = record.baby.pregnancycase
    is_owner = (case.user_id == user.user_id)
    is_shared = FamilyMember.objects.filter(pregnancycase_id=case, user_id=user).exists()
    if not (is_owner or is_shared):
        raise PermissionDenied("您沒有權限刪除此紀錄")

    if request.method == 'POST':
        record.delete()
    return redirect(url_with_active_selection(request, reverse('babyinformation')))
