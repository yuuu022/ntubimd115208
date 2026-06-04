from django.shortcuts import render
from core.models import BabyGrowthMap, BabyStatus, BabyRecord
from views.baby_utils import get_active_baby, split_note_and_milestones

#成長地圖
def baby_growthmap(request):

    baby = get_active_baby(request)
    growth_maps = BabyGrowthMap.objects.all().order_by('timecourse')
    growth_timeline = []

    if not baby:
        return render(request, "baby/baby_growthmap.html", {
            "growth_timeline": [],
            "growth_owner_name": "寶寶"
        })

    # 已完成里程碑
    completed_map_ids = set(
        BabyStatus.objects
        .filter(babyrecord__baby=baby)
        .values_list('babygrowthmap_id', flat=True)
    )

    # fallback：從紀錄解析 milestone（避免舊資料缺關聯）
    baby_records = list(BabyRecord.objects.filter(baby=baby))
    milestone_set = set()

    for rec in baby_records:
        milestones, _ = split_note_and_milestones(rec)
        milestone_set.update(milestones)

    # 組裝時間軸
    for growth_map in growth_maps:

        is_completed = (
            growth_map.babygrowthmap_id in completed_map_ids
            or growth_map.growthrecord in milestone_set
        )

        growth_timeline.append({
            "map_id": growth_map.babygrowthmap_id,
            "timecourse": growth_map.timecourse,
            "growthrecord": growth_map.growthrecord,
            "status": "completed" if is_completed else "pending",
        })

    return render(request, "baby/baby_growthmap.html", {
        "growth_timeline": growth_timeline,
        "growth_owner_name": baby.name,
    })