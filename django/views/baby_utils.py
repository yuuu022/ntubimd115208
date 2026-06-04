#嬰幼兒模組共用輔助函式（Helper Functions）
#被以下檔案引用：baby_dashboard.py、baby_info.py、baby_record.py
import calendar
import datetime

from django.conf import settings
from django.core.files.storage import FileSystemStorage

from core.models import (
    BabyRecord,
    BabyGrowthMap,
    BabyStatus,
)

# 日期 / 月齡工具
def calculate_age_in_months(birthdaytime, record_date):

    if not birthdaytime or not record_date:
        return None

    def _to_date(value):
        if isinstance(value, datetime.datetime):
            return value.date()
        if isinstance(value, datetime.date):
            return value
        try:
            return datetime.date.fromisoformat(str(value)[:10])
        except Exception:
            return None

    birth_date = _to_date(birthdaytime)
    rec_date   = _to_date(record_date)

    if birth_date is None or rec_date is None:
        return None

    delta = rec_date - birth_date
    if delta.days < 0:
        return 0

    return int(delta.days / 30.4375)

#里程碑時間區間列表
def get_relevant_timecourses(age_in_months):
  
    if age_in_months is None:
        return None

    if age_in_months <= 0:
        age_in_months = 1

    if age_in_months <= 11:
        m = max(1, age_in_months)
        return sorted({max(1, m - 1), m, m + 1})
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


# 資料型別轉換工具
def parse_int(value, default):
    """安全將 value 轉為整數，失敗時回傳 default。"""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def parse_float(value):
    """安全將 value 轉為浮點數，失敗時回傳 None。"""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None



# 嬰幼兒基本資料工具
def get_active_baby(request):
    
    from views.pregnancycase import resolve_active_baby
    from views.session_utils import get_current_user_profile

    return resolve_active_baby(request, get_current_user_profile(request))

#計算生產週數
def get_birth_week(baby):
    if (
        not baby
        or not baby.birthdaytime
        or not baby.pregnancycase
        or not baby.pregnancycase.menstruation
    ):
        return None

    delta = baby.birthdaytime.date() - baby.pregnancycase.menstruation
    if delta.days < 0:
        return None

    weeks = delta.days // 7
    days  = delta.days % 7
    return f'{weeks}w{days}d' if days else f'{weeks}w'

#嬰幼兒生日格式化為顯示用字串（YYYY.MM.DD HH:MM）
def format_birth_datetime(baby):
   
    if not baby or not baby.birthdaytime:
        return None
    return baby.birthdaytime.strftime('%Y.%m.%d %H:%M')

#將嬰幼兒生日格式化為 （YYYY-MM-DDTHH:MM）
def format_datetime_local(baby):
    if not baby or not baby.birthdaytime:
        return ''
    return baby.birthdaytime.strftime('%Y-%m-%dT%H:%M')

#新增/編輯嬰幼兒表單所需的初始值字
def get_baby_form_data(baby):
  
    if not baby:
        return {
            'baby_name':        '',
            'birthdaytime_value': '',
            'birth_week':       '',
            'birth_weight':     '',
            'birth_height':     '',
            'birth_head':       '',
            'birth_chest':      '',
            'production_method': '',
            'join_code':        '',
        }

    return {
        'baby_name':        baby.name or '',
        'birthdaytime_value': format_datetime_local(baby),
        'birth_week':       get_birth_week(baby) or '',
        'birth_weight':     baby.baby_weight or '',
        'birth_height':     baby.baby_height or '',
        'birth_head':       baby.babyheadcircumference or '',
        'birth_chest':      baby.chestcircumference or '',
        'production_method': baby.production_method or '',
        # 安全存取 pregnancycase.code，避免外鍵為 None 的 AttributeError
        'join_code': getattr(baby.pregnancycase, 'code', '') if baby.pregnancycase_id else '',
    }

#嬰幼兒資訊摘要字典，供頁面頂部基本資料區塊使用。
def get_baby_summary(baby):
    if not baby:
        return {
            'baby_name':    '小寶',
            'birth_week':   '-',
            'birth_method': '-',
            'birth_time':   '-',
            'birth_height': '-',
            'birth_weight': '-',
            'birth_head':   '-',
            'birth_chest':  '-',
            'photo_url':    None,
        }

    return {
        'baby_name':    baby.name or '小寶',
        'birth_week':   get_birth_week(baby) or '-',
        'birth_method': baby.production_method or '-',
        'birth_time':   format_birth_datetime(baby) or '-',
        'birth_height': baby.baby_height or '-',
        'birth_weight': baby.baby_weight or '-',
        'birth_head':   baby.babyheadcircumference or '-',
        'birth_chest':  baby.chestcircumference or '-',
        'photo_url':    None,  # 由呼叫端從最新紀錄補入
    }



# 生長紀錄工具
def split_note_and_milestones(record):
    """
    從 BabyStatus 關聯表讀取已達成里程碑，並分離日記內容。

    Args:
        record (BabyRecord | None)

    Returns:
        tuple[list[str], str]: (milestones, note_text)
    """
    if not record:
        return [], ""

    milestones = list(
        BabyStatus.objects.filter(babyrecord=record)
        .values_list('babygrowthmap__growthrecord', flat=True)
    )
    note_text = str(record.record or "")
    return milestones, note_text


# 圖片儲存至 MEDIA_ROOT/baby_records/ 
def save_uploaded_image(image_file):
    if not image_file:
        return None
    storage = FileSystemStorage(
        location=settings.MEDIA_ROOT,
        base_url=settings.MEDIA_URL,
    )
    filename = storage.save(f'baby_records/{image_file.name}', image_file)
    return storage.url(filename)

#對生長紀錄執行「前向填補
def fill_forward_growth_data(records):
    sorted_records = sorted(
        records,
        key=lambda r: (r.date.date() if hasattr(r.date, 'date') else r.date),
    )

    last_height = last_weight = last_head = last_chest = None
    result = []

    for rec in sorted_records:
        cur_height = rec.height
        cur_weight = rec.weight
        cur_head   = rec.headcircumference
        cur_chest  = rec.chestcircumference

        filled_height = cur_height if cur_height is not None else last_height
        filled_weight = cur_weight if cur_weight is not None else last_weight
        filled_head   = cur_head   if cur_head   is not None else last_head
        filled_chest  = cur_chest  if cur_chest  is not None else last_chest

        result.append({
            'record': rec,
            'date':   rec.date.date() if hasattr(rec.date, 'date') else rec.date,
            'height':             filled_height,
            'weight':             filled_weight,
            'headcircumference':  filled_head,
            'chestcircumference': filled_chest,
            'is_carried_height':  (cur_height is None and filled_height is not None),
            'is_carried_weight':  (cur_weight is None and filled_weight is not None),
            'is_carried_head':    (cur_head   is None and filled_head   is not None),
            'is_carried_chest':   (cur_chest  is None and filled_chest  is not None),
        })

        if cur_height is not None: last_height = cur_height
        if cur_weight is not None: last_weight = cur_weight
        if cur_head   is not None: last_head   = cur_head
        if cur_chest  is not None: last_chest  = cur_chest

    return result


def get_baby_milestones_summary(baby):
    """
    取得嬰幼兒所有已達成的里程碑摘要列表，依原始時間軸順序排列。

    Args:
        baby (BabyInformation | None)

    Returns:
        list[dict]
    """
    if not baby:
        return []

    growth_maps  = BabyGrowthMap.objects.all().order_by('timecourse')
    baby_records = list(BabyRecord.objects.filter(baby=baby))

    # 一次性預載所有 BabyStatus，避免迴圈內 N×M 次查詢
    achieved_map = {}
    for bs in BabyStatus.objects.filter(
        babyrecord__baby=baby
    ).select_related('babygrowthmap', 'babyrecord'):
        achieved_map.setdefault(bs.babygrowthmap_id, bs)

    completed_list = []

    for idx, growth_map in enumerate(growth_maps):
        bs              = achieved_map.get(growth_map.pk)
        is_completed    = bs is not None
        matching_record = bs.babyrecord if bs else None

        # 備援：文字比對（向下相容舊資料）
        if not is_completed:
            for rec in baby_records:
                milestones, _ = split_note_and_milestones(rec)
                if growth_map.growthrecord in milestones:
                    is_completed    = True
                    matching_record = rec
                    break

        if is_completed and matching_record:
            achieved_date_str = (
                matching_record.date.strftime('%Y.%m.%d')
                if hasattr(matching_record.date, 'strftime')
                else str(matching_record.date)
            )
            completed_list.append({
                'growthrecord':  growth_map.growthrecord,
                'timecourse':    growth_map.timecourse,
                'status':        'completed',
                'achieved_date': achieved_date_str,
                'description':   growth_map.growthrecord,
                'sort_order':    idx,
            })

    completed_list.sort(key=lambda x: x['sort_order'])
    return completed_list



# 月曆資料工具
def get_calendar_data(records, selected_date):
    year  = selected_date.year
    month = selected_date.month

    first_weekday, days_in_month = calendar.monthrange(year, month)
    leading_blanks = (first_weekday + 1) % 7

    cells = [{'empty': True} for _ in range(leading_blanks)]

    record_days = {}
    for rec in records:
        rec_date = rec.date.date() if hasattr(rec.date, 'date') else rec.date
        if rec_date.year == year and rec_date.month == month:
            record_days[rec_date.day] = rec

    for day in range(1, days_in_month + 1):
        d = datetime.date(year, month, day)
        cells.append({
            'empty':      False,
            'day':        day,
            'date_iso':   d.isoformat(),
            'is_selected': d == selected_date,
            'has_record': day in record_days,
        })

    while len(cells) % 7 != 0:
        cells.append({'empty': True})

    calendar_weeks = [cells[i:i + 7] for i in range(0, len(cells), 7)]
    while len(calendar_weeks) < 5:
        calendar_weeks.append([{'empty': True} for _ in range(7)])

    def _rec_year(rec):
        d = rec.date
        return d.date().year if isinstance(d, datetime.datetime) else d.year

    today = datetime.date.today()
    record_years = {today.year, year} | {_rec_year(r) for r in records}

    return {
        'calendar_weeks':       calendar_weeks,
        'selected_year':        year,
        'selected_month':       month,
        'selected_month_label': f'{year}年 {month}月',
        'selected_date_iso':    selected_date.isoformat(),
        'selected_day':         selected_date.day,
        'calendar_years':       sorted(record_years, reverse=True),
        'calendar_months':      list(range(1, 13)),
    }
