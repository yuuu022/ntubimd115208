# baby_growthmap.py
from django.shortcuts import render
from views import baby_utils

def baby_growthmap(request):
    """成長里程碑地圖（獨立分頁）"""
    baby = baby_utils.get_active_baby(request)
    # 直接呼叫共用核心
    context = baby_utils.build_growth_timeline_context(baby)
    return render(request, "baby/baby_growthmap.html", context)