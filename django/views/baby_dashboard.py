import datetime

from django.shortcuts import render

from core.models import BabyRecord

from views.baby_utils import (
    get_active_baby,
    get_baby_summary,
    get_baby_form_data,
    get_baby_milestones_summary,
    get_calendar_data,
    split_note_and_milestones,
    fill_forward_growth_data,
)

"""
- 顯示嬰幼兒基本資料摘要
- 渲染月曆，點選日期顯示當日紀錄
- 同日多筆紀錄自動合併（取最完整值）
- 當日欄位空值自動帶入前次有效值並標記「沿用」
- 提供成長圖表所需的前向填補資料（chart_records）
- 顯示已達成里程碑摘要列表
"""
#嬰幼兒主頁總覽（babyinformation）
def baby(request):
    active_baby = get_active_baby(request)
    records = []

    if active_baby is not None:
        records = BabyRecord.objects.filter(baby=active_baby).order_by('-date')
        for record in records:
            record.milestones, record.note_text = split_note_and_milestones(record)

    raw_date = request.GET.get('date')
    try:
        selected_date = datetime.date.fromisoformat(raw_date) if raw_date else datetime.date.today()
    except Exception:
        selected_date = datetime.date.today()

    filled_records = fill_forward_growth_data(list(records))
    filled_by_date = {item['date']: item for item in filled_records}

    selected_day_records = []
    for rec in records:
        rec_date = rec.date.date() if hasattr(rec.date, 'date') else rec.date
        if rec_date == selected_date:
            selected_day_records.append(rec)

    selected_day_record = None

    if selected_day_records:
        primary = selected_day_records[0]

        merged_height = primary.height
        merged_weight = primary.weight
        merged_head   = primary.headcircumference
        merged_chest  = primary.chestcircumference
        all_milestones = []
        all_notes      = []

        for r in selected_day_records:
            if merged_height is None and r.height is not None:
                merged_height = r.height
            if merged_weight is None and r.weight is not None:
                merged_weight = r.weight
            if merged_head is None and r.headcircumference is not None:
                merged_head = r.headcircumference
            if merged_chest is None and r.chestcircumference is not None:
                merged_chest = r.chestcircumference

            for ms in (r.milestones or []):
                if ms not in all_milestones:
                    all_milestones.append(ms)

            note_stripped = (r.note_text or '').strip()
            if note_stripped and note_stripped not in all_notes:
                all_notes.append(note_stripped)

        primary.height            = merged_height
        primary.weight            = merged_weight
        primary.headcircumference  = merged_head
        primary.chestcircumference = merged_chest
        primary.milestones        = all_milestones
        primary.note_text         = '\n'.join(all_notes) if all_notes else ''

        selected_day_record = primary

        filled = filled_by_date.get(selected_date)
        if filled:
            if selected_day_record.height is None and filled['height'] is not None:
                selected_day_record.height = filled['height']
                selected_day_record.height_carried = True
            if selected_day_record.weight is None and filled['weight'] is not None:
                selected_day_record.weight = filled['weight']
                selected_day_record.weight_carried = True
            if selected_day_record.headcircumference is None and filled['headcircumference'] is not None:
                selected_day_record.headcircumference = filled['headcircumference']
                selected_day_record.head_carried = True
            if selected_day_record.chestcircumference is None and filled['chestcircumference'] is not None:
                selected_day_record.chestcircumference = filled['chestcircumference']
                selected_day_record.chest_carried = True

    summary = get_baby_summary(active_baby)
    for r in records:
        if r.photo:
            summary['photo_url'] = r.photo
            break

    milestones_summary = get_baby_milestones_summary(active_baby)

    context = {
        'baby':                active_baby,
        'records':             records,
        'chart_records':       filled_records,
        'baby_summary':        summary,
        'baby_form':           get_baby_form_data(active_baby),
        'selected_date':       selected_date,
        'selected_day_record': selected_day_record,
        'has_day_data':        bool(selected_day_record),
        'milestones_summary':  milestones_summary,
    }
    context.update(get_calendar_data(records, selected_date))

    return render(request, 'baby/babyinformation.html', context)
