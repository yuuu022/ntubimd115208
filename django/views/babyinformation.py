import calendar
import datetime

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, redirect, get_object_or_404
from core.models import BabyInformation, BabyRecord, BabyGrowthMap, BabyStatus
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
        pregnancy_count = baby.pregnancycase.babies.count() or 1

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
        baby_count = baby.pregnancycase.babies.count()

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
    baby_id = request.GET.get('baby_id') or request.POST.get('baby_id')
    if baby_id:
        try:
            baby = BabyInformation.objects.filter(baby_id=int(baby_id)).first()
            if baby:
                request.session['active_baby_id'] = baby.baby_id
                return baby
        except (ValueError, TypeError):
            pass

    session_baby_id = request.session.get('active_baby_id')
    if session_baby_id:
        baby = BabyInformation.objects.filter(baby_id=session_baby_id).first()
        if baby:
            return baby

    # Fallback to the first baby
    baby = BabyInformation.objects.first()
    if baby:
        request.session['active_baby_id'] = baby.baby_id
    return baby


def _get_baby_milestones_summary(baby):
    if not baby:
        return []

    growth_maps = BabyGrowthMap.objects.all().order_by('timecourse')
    baby_records = list(BabyRecord.objects.filter(baby=baby))

    DEFAULT_DESCRIPTIONS = {
        # 0-6 個月
        '對巨大聲音有反應': '聽到突如其來的巨大聲響時，會出現驚嚇、眼睛睜大或哭泣等自然反射動作。',
        '眼睛注視照顧者的臉': '當大人靠近並溫柔說話時，雙眼能主動追隨注視照顧者的臉龐或面部表情。',
        '逗弄時會微笑及發出咿呀聲': '在照顾者的引導逗樂下，會展現出甜美的微笑，並嘗試發出簡單的「啊」、「喔」咿呀聲。',
        '趴臥時頭部能短暫抬起': '趴著時，能嘗試將頭部抬起離地數秒，展示頸部肌肉力量的初步發展。',
        '抬頭自如': '趴著時能穩定用雙手手肘支撐，將頭部高高抬起並觀察四周，持續時間變長。',
        '眼睛能追視移動的物體或人': '雙眼能順暢、對焦地隨著左右緩慢移動的人臉或玩具移動，視野開闊度增加。',
        '第一次翻身': '成功從仰躺翻轉成趴姿，學習控制身體與軀幹的力量。',
        '會主動伸手抓握玩具': '看到眼前感興趣的玩具或懸掛物時，會主動伸出小手去碰觸或緊緊抓握住。',
        # 6-12 個月
        '扶著腋下可以站得很穩': '雙手扶在雙腳著地時，能短暫站直並用雙腿支撐部分身體重量。',
        '會將玩具從一隻手換到另一隻手': '左右手協調度提升，能順暢地將手中的玩具在雙手之間轉移與把玩。',
        '獨立坐穩': '不需外力支撐可自己平穩坐立超過 5 分鐘，正在穩健學習平衡中。',
        '開始爬行': '肚子離地，能用雙手與雙膝支撐身體並協調地往前爬行，探索更大空間。',
        '扶物站立': '能抓住沙發、家具或欄杆自己站立起來，大腿與腳部力量逐步增強。',
        '會拍手或揮手表示再見': '能模仿大人的肢體動作，主動做出拍手慶祝或揮手說再見的社交互動。',
        # 1-2 歲
        '開口叫媽媽': '嘗試發出有意義的單音或疊字（如媽媽、爸爸、奶奶），開啟語言雙向溝通。',
        '扶著家具能走幾步路': '能抓著家具邊緣橫向跨步，或牽著大人的雙手向前跨出步伐。',
        '能獨自站立並平穩行走': '不需任何扶持能自己站穩，並能獨立向前跨步，走得平穩且自然。',
        '會用手指指出想要的東西': '當想索取某樣物品或看到感興趣的事物時，會主動用食指指向該方向表達意願。',
        '會自己用湯匙吃東西': '手眼協調能力提升，能嘗試自己用湯匙舀起食物並成功送入口中。',
        '能指認至少3個身體部位': '當大人詢問時，能正確指認並摸摸自己的眼睛、鼻子、嘴巴或耳朵等身體部位。',
        # 2-3 歲
        '雙腳能同時跳離地面': '下肢爆發力與平衡感成熟，能在原地做出雙腳同時跳起離地的可愛動作。',
        '會說 2-3 個字組成的短句子': '語言表達能力大躍進，能說出如「媽媽抱抱」、「吃大蘋果」等兩個以上詞彙組成的短句。',
        '會自己脫鞋襪或簡單衣物': '生活自理能力萌芽，能自己動手脫掉小鞋子、襪子或解開簡單的小衣物。',
        '能清楚說出自己的名字': '自我意識與語言認知成熟，當被問起時能清晰且驕傲地說出自己的小名或完整名字。',
        '學會騎三輪車': '雙腿交替用力與方向控制能力提升，能用雙腳踩踏板並順暢騎乘三輪玩具車。',
        '能與大人進行流暢的日常對話': '字彙量與文法結構完整，能主動詢問問題、回答照顧者的對話並清晰表達自己的想法。',
    }

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

        if is_completed and matching_record:
            item_status = 'completed'
            milestones, note_text = _split_note_and_milestones(matching_record.record)
            achieved_date_str = matching_record.date.strftime('%Y.%m.%d') if hasattr(matching_record.date, 'strftime') else str(matching_record.date)
            description = note_text.strip() or DEFAULT_DESCRIPTIONS.get(growth_map.growthrecord)
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
                description = DEFAULT_DESCRIPTIONS.get(desc_key)
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
    if completed_items:
        summary_list.append(completed_items[-1])  # 顯示最後一個已達成的
    if in_progress_items:
        summary_list.extend(in_progress_items)  # 顯示目前進行中的下一個目標
    if pending_items:
        summary_list.append(pending_items[0])  # 顯示後續的第一個期待

    if not summary_list:
        summary_list = growth_timeline[:3]

    return summary_list[:3]


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
    for rec in records:
        rec_date = rec.date.date() if hasattr(rec.date, 'date') else rec.date
        if rec_date == selected_date:
            selected_day_record = rec
            break

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
    baby = _get_active_baby(request)
    return render(request, 'baby/add_baby_information.html', {
        'baby_form': _get_baby_form_data(baby),
        'baby': baby,
    })


def edit_baby_information(request):
    baby = _get_active_baby(request)
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
                
        return redirect('babyinformation')

    baby_list = BabyInformation.objects.all()
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
    record = get_object_or_404(BabyRecord, babyrecord_id=babyrecord_id)
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

        return redirect('babyinformation')

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
    record = get_object_or_404(BabyRecord, babyrecord_id=babyrecord_id)
    if request.method == 'POST':
        record.delete()
    return redirect('babyinformation')
