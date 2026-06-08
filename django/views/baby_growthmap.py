import datetime

from django.shortcuts import render

from core.models import BabyGrowthMap, BabyStatus, BabyRecord
from views.baby_utils import (
    get_active_baby,
    split_note_and_milestones,
    calculate_age_in_months,
    get_relevant_timecourses,
)


def baby_growthmap(request):
    """成長里程碑地圖。"""
    
    baby        = get_active_baby(request)
    growth_maps = BabyGrowthMap.objects.all().order_by('timecourse')

    if not baby:
        return render(request, "baby/baby_growthmap.html", {
            "growth_timeline":   [],
            "growth_owner_name": "寶寶",
        })

    today = datetime.date.today()

    # ── 已完成里程碑（BabyStatus 關聯表） ─────────────────────
    achieved_qs = (
        BabyStatus.objects
        .filter(babyrecord__baby=baby)
        .select_related('babyrecord', 'babygrowthmap')
    )
    # babygrowthmap_id → 達成日期
    achieved_map = {}
    for bs in achieved_qs:
        if bs.babygrowthmap_id not in achieved_map:
            achieved_map[bs.babygrowthmap_id] = bs.babyrecord.date

    completed_map_ids = set(achieved_map.keys())

    # ── fallback：從紀錄文字解析（向下相容舊資料） ───────────
    milestone_date_map = {}   # growthrecord 文字 → 達成日期
    for rec in BabyRecord.objects.filter(baby=baby).order_by('date'):
        milestones, _ = split_note_and_milestones(rec)
        for m in milestones:
            if m not in milestone_date_map:
                milestone_date_map[m] = rec.date

    # ── 計算目前月齡，決定「進行中」區間 ─────────────────────
    age_in_months    = calculate_age_in_months(baby.birthdaytime, today)
    relevant_courses = get_relevant_timecourses(age_in_months) or []

    # ── 組裝時間軸 ────────────────────────────────────────────
    growth_timeline = []

    for growth_map in growth_maps:
        gid  = growth_map.babygrowthmap_id
        name = growth_map.growthrecord

        # 判斷是否已完成
        achieved_date_raw = None
        if gid in completed_map_ids:
            achieved_date_raw = achieved_map[gid]
        elif name in milestone_date_map:
            achieved_date_raw = milestone_date_map[name]

        is_completed = achieved_date_raw is not None

        # 達成日期格式化
        if achieved_date_raw:
            achieved_date = (
                achieved_date_raw.strftime('%Y.%m.%d')
                if hasattr(achieved_date_raw, 'strftime')
                else str(achieved_date_raw)
            )
        else:
            achieved_date = ""

        # 判斷狀態
        if is_completed:
            status = "completed"
        elif growth_map.timecourse in relevant_courses:
            status = "in_progress"
        else:
            status = "pending"

        growth_timeline.append({
            "map_id":        gid,
            "timecourse":    growth_map.timecourse,
            "growthrecord":  name,
            "status":        status,
            "description":   "",   # BabyGrowthMap 目前無此欄位
            "category":      "",   # 同上
            "photo":         None,
            "achieved_date": achieved_date,
        })

    return render(request, "baby/baby_growthmap.html", {
        "growth_timeline":   growth_timeline,
        "growth_owner_name": baby.name,
    })
