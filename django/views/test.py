from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from core.forms import UserProfileForm
from core.models import BabyGrowthMap, BabyStatus

def add_user(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'User successfully created!')
                return redirect('add_user')
            except Exception as e:
                messages.error(request, f'Error creating user: {e}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserProfileForm()

    return render(request, 'add_user.html', {'form': form})


#成長地圖畫面
def baby_growthmap(request):
    """成長地圖畫面 - 顯示寶寶的成長進度"""
    # 獲取所有成長地圖，按時間軸排序
    growth_maps = BabyGrowthMap.objects.all().order_by('timecourse')

    # 構建詳細的成長數據
    growth_timeline = []
    for growth_map in growth_maps:
        # 獲取該成長地圖關聯的所有寶寶狀態
        baby_statuses = BabyStatus.objects.filter(babygrowthmap=growth_map)

        status_details = []
        for status in baby_statuses:
            try:
                baby_record = status.babyrecord
                baby_info = baby_record.baby

                status_detail = {
                    'status_id': status.babystatus_id,
                    'baby_name': baby_info.name,
                    'record_date': baby_record.date,
                    'weight': baby_record.weight,
                    'height': baby_record.height,
                    'headcircumference': baby_record.headcircumference,
                    'chestcircumference': baby_record.chestcircumference,
                    'record': baby_record.record,
                    'photo': baby_record.photo,
                }
                status_details.append(status_detail)
            except Exception as e:
                # 如果缺少關聯數據，跳過
                continue

        # 構建時間軸項目
        timeline_item = {
            'map_id': growth_map.babygrowthmap_id,
            'timecourse': growth_map.timecourse,
            'growthrecord': growth_map.growthrecord,
            'baby_statuses': status_details,
            'status_count': len(status_details),
        }
        growth_timeline.append(timeline_item)

    context = {
        'growth_timeline': growth_timeline,
        'total_maps': len(growth_timeline),
    }
    return render(request, 'baby/baby_growthmap.html', context)
