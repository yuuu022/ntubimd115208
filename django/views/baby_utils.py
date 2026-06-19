import datetime
import calendar
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from core.models import BabyRecord, BabyGrowthMap, BabyStatus
from views.pregnancycase import resolve_active_baby
from views.session_utils import get_current_user_profile

def get_active_baby(request):
    """取得當前 Session 活躍的寶寶"""
    return resolve_active_baby(request, get_current_user_profile(request))

def parse_float(value):
    """安全地將數值轉成浮點數"""
    try: return float(value)
    except (TypeError, ValueError): return None

def get_birth_week(baby):
    #計算出生週數、進行合理性檢查：
    if not baby or not baby.birthdaytime or not baby.pregnancycase or not baby.pregnancycase.menstruation:
        return None
    
    # 統一轉換為 date 型別
    birth_date = baby.birthdaytime.date() if hasattr(baby.birthdaytime, 'date') else baby.birthdaytime
    lmp_date = baby.pregnancycase.menstruation
    
    # 防禦一：出生日不可大於今天
    if birth_date > datetime.date.today():
        return None
        
    delta = birth_date - lmp_date
    
    # 防禦二：出生日不可小於或等於 LMP。
    # 醫學極限防線：懷孕小於 14 週（98天）出生無法存活，通常為早期流產，若作為出生日登記必為亂填。
    if delta.days < 98:
        return None

    weeks = delta.days // 7
    days  = delta.days % 7
    
    return f'{weeks}w{days}d' if days else f'{weeks}w'

def split_note_and_milestones(record):
    """分離紀錄內文與綁定的里程碑清單"""
    if not record: return [], ""
    milestones = list(BabyStatus.objects.filter(babyrecord=record).values_list('babygrowthmap__growthrecord', flat=True))
    return milestones, str(record.record or "")

def calculate_age_in_months(birthdaytime, record_date):
    """精確計算月齡"""
    if not birthdaytime or not record_date: return None
    def _to_date(value):
        if isinstance(value, datetime.datetime): return value.date()
        if isinstance(value, datetime.date): return value
        try: return datetime.date.fromisoformat(str(value)[:10])
        except Exception: return None

    birth_date, rec_date = _to_date(birthdaytime), _to_date(record_date)
    if birth_date is None or rec_date is None: return None
    delta = rec_date - birth_date
    return 0 if delta.days < 0 else int(delta.days / 30.4375)

def get_relevant_timecourses(age_in_months):
    """根據月齡推薦發展指標區間時間軸代碼"""
    if age_in_months is None: return None
    if age_in_months <= 0: age_in_months = 1
    if age_in_months <= 11:
        m = max(1, age_in_months)
        return sorted({max(1, m - 1), m, m + 1})
    elif age_in_months == 12: return [11, 12, 18]
    elif age_in_months < 18: return [12, 18]
    elif age_in_months == 18: return [12, 18, 24]
    elif age_in_months < 24: return [18, 24]
    elif age_in_months == 24: return [18, 24, 36]
    elif age_in_months < 36: return [24, 36]
    else: return [36]

def save_uploaded_image(image_file):
    """上傳圖片至儲存區，回傳相對 URL"""
    if not image_file: return None
    storage = FileSystemStorage(location=settings.MEDIA_ROOT, base_url=settings.MEDIA_URL)
    filename = storage.save(f'baby_records/{image_file.name}', image_file)
    return storage.url(filename)


def build_growth_timeline_context(baby):
    """
    核心架構重構：統一處理寶寶成長里程碑與舊資料文字向下相容的 Context 產生器
    """
    if not baby:
        return {"growth_timeline": [], "growth_owner_name": "寶寶"}

    growth_maps = BabyGrowthMap.objects.all().order_by('timecourse')
    
    # 1. 取得已完成里程碑關聯表
    completed_ids = set(
        BabyStatus.objects.filter(babyrecord__baby=baby).values_list('babygrowthmap_id', flat=True)
    )
    
    # 2. 取得歷史紀錄文字雜湊（向下相容舊資料）
    milestone_text_set = set()
    for rec in BabyRecord.objects.filter(baby=baby):
        # 呼叫現有的分割文字工具
        m, _ = split_note_and_milestones(rec)
        milestone_text_set.update(m)
        
    # 3. 建立統一的 Timeline 資料結構
    growth_timeline = []
    for g_map in growth_maps:
        is_completed = (g_map.babygrowthmap_id in completed_ids or g_map.growthrecord in milestone_text_set)
        
        growth_timeline.append({
            "map_id": g_map.babygrowthmap_id,
            "timecourse": g_map.timecourse,
            "growthrecord": g_map.growthrecord,
            "status": "completed" if is_completed else "pending",
            "description": "", 
            "category": "",   
            "photo": None,
            "achieved_date": "" # 可根據需求再擴充關聯日期
        })
        
    return {
        "growth_timeline": growth_timeline,
        "growth_owner_name": getattr(baby, 'name', '寶寶')
    }