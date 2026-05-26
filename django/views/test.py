from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from core.forms import UserProfileForm
from core.models import BabyGrowthMap, BabyStatus

MILESTONE_PREFIX = '里程碑：'


def _split_note_and_milestones(text):
    if not text:
        return [], ''
    text = str(text)
    if text.startswith(MILESTONE_PREFIX):
        first_line, _, rest = text.partition('\n')
        milestones_part = first_line[len(MILESTONE_PREFIX):].strip()
        milestones = [m.strip() for m in milestones_part.split(',') if m.strip()]
        return milestones, rest.strip()
    return [], text


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

                milestones, note_text = _split_note_and_milestones(baby_record.record)
                status_detail = {
                    'status_id': status.babystatus_id,
                    'baby_name': baby_info.name,
                    'record_date': baby_record.date,
                    'weight': baby_record.weight,
                    'height': baby_record.height,
                    'headcircumference': baby_record.headcircumference,
                    'chestcircumference': baby_record.chestcircumference,
                    'record': note_text,
                    'photo': baby_record.photo,
                    'milestones': milestones,
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

    growth_owner_name = None
    if growth_timeline and growth_timeline[0]['baby_statuses']:
        growth_owner_name = growth_timeline[0]['baby_statuses'][0]['baby_name']

    context = {
        'growth_timeline': growth_timeline,
        'total_maps': len(growth_timeline),
        'growth_owner_name': growth_owner_name,
    }
    return render(request, 'baby/baby_growthmap.html', context)
