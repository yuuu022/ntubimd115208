import datetime
import calendar
from django.shortcuts import render
from core.models import BabyRecord, BabyGrowthMap, BabyStatus
from views import baby_utils



def _fill_forward_growth_data(records):
    sorted_records = sorted(records, key=lambda r: (r.date.date() if hasattr(r.date, 'date') else r.date))
    last_height = last_weight = last_head = last_chest = None
    result = []
    for rec in sorted_records:
        filled_height = rec.height if rec.height is not None else last_height
        filled_weight = rec.weight if rec.weight is not None else last_weight
        filled_head   = rec.headcircumference if rec.headcircumference is not None else last_head
        filled_chest  = rec.chestcircumference if rec.chestcircumference is not None else last_chest

        result.append({
            'record': rec, 'date': rec.date.date() if hasattr(rec.date, 'date') else rec.date,
            'height': filled_height, 'weight': filled_weight, 'headcircumference': filled_head, 'chestcircumference': filled_chest,
            'is_carried_height': (rec.height is None and filled_height is not None),
            'is_carried_weight': (rec.weight is None and filled_weight is not None),
            'is_carried_head': (rec.headcircumference is None and filled_head is not None),
            'is_carried_chest': (rec.chestcircumference is None and filled_chest is not None),
        })
        if rec.height is not None: last_height = rec.height
        if rec.weight is not None: last_weight = rec.weight
        if rec.headcircumference is not None: last_head = rec.headcircumference
        if rec.chestcircumference is not None: last_chest = rec.chestcircumference
    return result

def _get_calendar_data(records, selected_date):
    year, month = selected_date.year, selected_date.month
    first_weekday, days_in_month = calendar.monthrange(year, month)
    
    # 1. 取得今天日期，用來比對是否為未來日期
    today = datetime.date.today()
    
    # 填補當月第一天之前的空白格子
    cells = [{'empty': True} for _ in range((first_weekday + 1) % 7)]
    
    # 整理當月已有紀錄的日期
    record_days = {
        (r.date.date().day if hasattr(r.date, 'date') else r.date.day): r 
        for r in records 
        if (r.date.date().year if hasattr(r.date, 'date') else r.date.year) == year 
        and (r.date.date().month if hasattr(r.date, 'date') else r.date.month) == month
    }

    # 生成每一天的日期格子
    for day in range(1, days_in_month + 1):
        d = datetime.date(year, month, day)
        cells.append({
            'empty': False, 
            'day': day, 
            'date_iso': d.isoformat(), 
            'is_selected': d == selected_date, 
            'has_record': day in record_days,
            'is_future': d > today,  # 👈 核心修改：判斷是否大於今天
        })

    # 填補當月最後一天之後的空白格子，確保每週 7 格
    while len(cells) % 7 != 0: 
        cells.append({'empty': True})
        
    calendar_weeks = [cells[i:i + 7] for i in range(0, len(cells), 7)]
    while len(calendar_weeks) < 5: 
        calendar_weeks.append([{'empty': True} for _ in range(7)])
        
    record_years = {today.year, year} | {(r.date.date().year if isinstance(r.date, datetime.datetime) else r.date.year) for r in records}

    return {
        'calendar_weeks': calendar_weeks, 
        'selected_year': year, 
        'selected_month': month, 
        'selected_month_label': f'{year}年 {month}月', 
        'selected_date_iso': selected_date.isoformat(), 
        'selected_day': selected_date.day, 
        'calendar_years': sorted(record_years, reverse=True), 
        'calendar_months': list(range(1, 13))
    }

def _get_baby_milestones_summary(baby):
    if not baby: return []
    growth_maps, baby_records = BabyGrowthMap.objects.all().order_by('timecourse'), list(BabyRecord.objects.filter(baby=baby))
    achieved_map = {bs.babygrowthmap_id: bs for bs in BabyStatus.objects.filter(babyrecord__baby=baby).select_related('babygrowthmap', 'babyrecord')}
    completed_list = []

    for idx, growth_map in enumerate(growth_maps):
        bs = achieved_map.get(growth_map.pk)
        is_completed, matching_record = bs is not None, bs.babyrecord if bs else None
        if not is_completed:
            for rec in baby_records:
                milestones, _ = baby_utils.split_note_and_milestones(rec)
                if growth_map.growthrecord in milestones: is_completed, matching_record = True, rec; break
        if is_completed and matching_record:
            completed_list.append({'growthrecord': growth_map.growthrecord, 'timecourse': growth_map.timecourse, 'status': 'completed', 'achieved_date': matching_record.date.strftime('%Y.%m.%d') if hasattr(matching_record.date, 'strftime') else str(matching_record.date), 'description': growth_map.growthrecord, 'sort_order': idx})
    return sorted(completed_list, key=lambda x: x['sort_order'])

def baby(request):
    """主頁總覽"""
    active_baby = baby_utils.get_active_baby(request)
    records = list(BabyRecord.objects.filter(baby=active_baby).order_by('-date')) if active_baby else []
    for record in records: record.milestones, record.note_text = baby_utils.split_note_and_milestones(record)

    try: selected_date = datetime.date.fromisoformat(request.GET.get('date', '')) if request.GET.get('date') else datetime.date.today()
    except Exception: selected_date = datetime.date.today()

    filled_records = _fill_forward_growth_data(records)
    filled_by_date = {item['date']: item for item in filled_records}
    selected_day_records = [r for r in records if (r.date.date() if hasattr(r.date, 'date') else r.date) == selected_date]
    selected_day_record = None

    if selected_day_records:
        primary = selected_day_records[0]
        merged_h, merged_w, merged_hd, merged_ch = primary.height, primary.weight, primary.headcircumference, primary.chestcircumference
        all_m, all_n = [], []
        for r in selected_day_records:
            if merged_h is None: merged_h = r.height
            if merged_w is None: merged_w = r.weight
            if merged_hd is None: merged_hd = r.headcircumference
            if merged_ch is None: merged_ch = r.chestcircumference
            for ms in (r.milestones or []):
                if ms not in all_m: all_m.append(ms)
            if (r.note_text or '').strip() and (r.note_text or '').strip() not in all_n: all_n.append((r.note_text or '').strip())
        primary.height, primary.weight, primary.headcircumference, primary.chestcircumference, primary.milestones, primary.note_text = merged_h, merged_w, merged_hd, merged_ch, all_m, '\n'.join(all_n)
        selected_day_record = primary
        filled = filled_by_date.get(selected_date)
        if filled and selected_day_record:
            if selected_day_record.height is None and filled['height'] is not None: selected_day_record.height, selected_day_record.height_carried = filled['height'], True
            if selected_day_record.weight is None and filled['weight'] is not None: selected_day_record.weight, selected_day_record.weight_carried = filled['weight'], True
            if selected_day_record.headcircumference is None and filled['headcircumference'] is not None: selected_day_record.headcircumference, selected_day_record.head_carried = filled['headcircumference'], True
            if selected_day_record.chestcircumference is None and filled['chestcircumference'] is not None: selected_day_record.chestcircumference, selected_day_record.chest_carried = filled['chestcircumference'], True

    if active_baby:
        summary = {'baby_name': active_baby.name or '小寶', 'birth_week': baby_utils.get_birth_week(active_baby) or '-', 'birth_method': active_baby.production_method or '-', 'birth_time': active_baby.birthdaytime.strftime('%Y.%m.%d %H:%M') if active_baby.birthdaytime else '-', 'birth_height': active_baby.baby_height or '-', 'birth_weight': active_baby.baby_weight or '-', 'birth_head': active_baby.babyheadcircumference or '-', 'birth_chest': active_baby.chestcircumference or '-', 'photo_url': None}
        baby_form = {'baby_name': active_baby.name or '', 'birthdaytime_value': active_baby.birthdaytime.strftime('%Y-%m-%dT%H:%M') if active_baby.birthdaytime else '', 'birth_week': baby_utils.get_birth_week(active_baby) or '', 'birth_weight': active_baby.baby_weight or '', 'birth_height': active_baby.baby_height or '', 'birth_head': active_baby.babyheadcircumference or '', 'birth_chest': active_baby.chestcircumference or '', 'production_method': active_baby.production_method or '', 'join_code': getattr(active_baby.pregnancycase, 'code', '') if active_baby.pregnancycase_id else ''}
    else:
        summary = {k: '-' for k in ['baby_name', 'birth_week', 'birth_method', 'birth_time', 'birth_height', 'birth_weight', 'birth_head', 'birth_chest']}; summary['photo_url'] = None
        baby_form = {k: '' for k in ['baby_name', 'birthdaytime_value', 'birth_week', 'birth_weight', 'birth_height', 'birth_head', 'birth_chest', 'production_method', 'join_code']}
    for r in records:
        if r.photo: summary['photo_url'] = r.photo; break

    context = {'baby': active_baby, 'baby_is_born': bool(active_baby and active_baby.birthdaytime), 'records': records, 'chart_records': filled_records, 'baby_summary': summary, 'baby_form': baby_form, 'selected_date': selected_date, 'selected_day_record': selected_day_record, 'has_day_data': bool(selected_day_record), 'milestones_summary': _get_baby_milestones_summary(active_baby)}
    context.update(_get_calendar_data(records, selected_date))
    return render(request, 'baby/babyinformation.html', context)

def baby_growthmap(request):
    """成長地圖"""
    baby = baby_utils.get_active_baby(request)
    if not baby: return render(request, "baby/baby_growthmap.html", {"growth_timeline": [], "growth_owner_name": "寶寶"})
    growth_maps, growth_timeline = BabyGrowthMap.objects.all().order_by('timecourse'), []
    completed_ids = set(BabyStatus.objects.filter(babyrecord__baby=baby).values_list('babygrowthmap_id', flat=True))
    m_set = set()
    for rec in BabyRecord.objects.filter(baby=baby):
        m, _ = baby_utils.split_note_and_milestones(rec); m_set.update(m)
    for g_map in growth_maps:
        is_completed = (g_map.babygrowthmap_id in completed_ids or g_map.growthrecord in m_set)
        growth_timeline.append({"map_id": g_map.babygrowthmap_id, "timecourse": g_map.timecourse, "growthrecord": g_map.growthrecord, "status": "completed" if is_completed else "pending"})
    return render(request, "baby/baby_growthmap.html", {"growth_timeline": growth_timeline, "growth_owner_name": baby.name})
