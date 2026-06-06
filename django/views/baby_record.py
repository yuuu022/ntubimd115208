import datetime

from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone

from core.models import (
    BabyInformation,
    BabyRecord,
    BabyGrowthMap,
    BabyStatus,
    PregnancyCase,
    FamilyMember,
)
from views.pregnancycase import url_with_active_selection

from views.baby_utils import (
    get_active_baby,
    calculate_age_in_months,
    get_relevant_timecourses,
    parse_float,
    split_note_and_milestones,
    save_uploaded_image,
)

#嬰幼兒生長紀錄管理
def add_baby_record(request):

    active_baby = get_active_baby(request)

    if active_baby is None:
        return render(request, 'baby/add_baby_record.html', {
            'error': '請先建立寶寶資料',
        })

    initial_date = request.GET.get('date', '')

    if request.method == 'POST':
        date_str = request.POST.get('date')
        if not date_str:
            return render(request, 'baby/add_baby_record.html', {
                'baby':      active_baby,
                'error':     '請填寫紀錄日期',
                'form_data': request.POST,
            })

        # 後端二次驗證：防止直接呼叫 API 繞過前端限制
        try:
            record_date_post = datetime.date.fromisoformat(date_str)
        except (ValueError, TypeError):
            return render(request, 'baby/add_baby_record.html', {
                'baby':      active_baby,
                'error':     '日期格式不正確',
                'form_data': request.POST,
            })

        if record_date_post > datetime.date.today():
            return render(request, 'baby/add_baby_record.html', {
                'baby':      active_baby,
                'error':     '無法新增未來日期的紀錄',
                'form_data': request.POST,
            })

        photo_url      = save_uploaded_image(request.FILES.get('photo'))
        milestones_str = request.POST.get('milestones', '')
        record_text    = build_record_text(request.POST.get('record', ''), milestones_str)

        baby_record = BabyRecord.objects.create(
            baby=active_baby,
            date=record_date_post,
            record=record_text,
            weight=parse_float(request.POST.get('weight')),
            height=parse_float(request.POST.get('height')),
            headcircumference=parse_float(request.POST.get('headcircumference')),
            chestcircumference=parse_float(request.POST.get('chestcircumference')),
            photo=photo_url,
        )

        # 解析 pipe-separated 里程碑字串，逐一建立 BabyStatus 關聯
        milestone_names = [m.strip() for m in milestones_str.split('|') if m.strip()]
        for m_name in milestone_names:
            growth_map = BabyGrowthMap.objects.filter(growthrecord=m_name).first()
            if growth_map:
                BabyStatus.objects.get_or_create(
                    babyrecord=baby_record,
                    babygrowthmap=growth_map,
                )

        return redirect(url_with_active_selection(request, reverse('babyinformation')))

    # ---- GET：準備表單資料 ----
    from views.session_utils import get_current_user_profile

    user = get_current_user_profile(request)
    if not user:
        return redirect('login')

    # 查詢該使用者可存取的全部嬰幼兒（自有 + 家庭成員共享）
    cases_own    = PregnancyCase.objects.filter(user=user)
    cases_shared = FamilyMember.objects.filter(user_id=user).values_list('pregnancycase_id', flat=True)
    baby_list    = BabyInformation.objects.filter(
        Q(pregnancycase__in=cases_own) | Q(pregnancycase_id__in=cases_shared)
    ).distinct()

    try:
        record_date = datetime.date.fromisoformat(initial_date) if initial_date else datetime.date.today()
    except Exception:
        record_date = datetime.date.today()

    age_in_months   = calculate_age_in_months(active_baby.birthdaytime, record_date)
    relevant_courses = get_relevant_timecourses(age_in_months)

    # 排除已達成的里程碑
    achieved_ids = BabyStatus.objects.filter(
        babyrecord__baby=active_baby
    ).values_list('babygrowthmap_id', flat=True)

    if relevant_courses:
        all_milestones = BabyGrowthMap.objects.filter(
            timecourse__in=relevant_courses
        ).exclude(
            babygrowthmap_id__in=achieved_ids
        ).order_by('timecourse')
    else:
        # 月齡無法計算時顯示全部未達成里程碑
        all_milestones = BabyGrowthMap.objects.all().exclude(
            babygrowthmap_id__in=achieved_ids
        ).order_by('timecourse')

    return render(request, 'baby/add_baby_record.html', {
        'baby':          active_baby,
        'baby_list':     baby_list,
        'all_milestones': all_milestones,
        'form_data':     {'date': record_date.isoformat()},
        'milestones':    '',
    })


def edit_baby_record(request, babyrecord_id):
    """
    [編輯生長紀錄] 修改特定紀錄的日記、數值或里程碑。

    安全防護（水平越權）：
        只有紀錄所屬懷孕案例的擁有者或家庭成員可編輯，
        否則拋出 PermissionDenied（HTTP 403）。

    里程碑更新策略：
        先全量刪除再重新建立，確保結果與表單提交完全一致。

    Template:
        baby/edit_baby_record.html
    """
    from views.session_utils import get_current_user_profile
    from django.core.exceptions import PermissionDenied

    user = get_current_user_profile(request)
    if not user:
        return redirect('login')

    record = get_object_or_404(BabyRecord, babyrecord_id=babyrecord_id)
    case   = record.baby.pregnancycase

    is_owner  = (case.user_id == user.user_id)
    is_shared = FamilyMember.objects.filter(pregnancycase_id=case, user_id=user).exists()

    # 水平越權防護
    if not (is_owner or is_shared):
        raise PermissionDenied('您沒有權限編輯此紀錄')

    record.milestones, record.note_text = split_note_and_milestones(record)

    if request.method == 'POST':
        date = request.POST.get('date')
        if not date:
            return render(request, 'baby/edit_baby_record.html', {
                'record':             record,
                'error':              '請填寫紀錄日期',
                'form_data':          request.POST,
                'selected_milestones': request.POST.get('milestones', ''),
            })

        milestones_str = request.POST.get('milestones', '')

        record.date              = date
        record.record            = build_record_text(request.POST.get('record', ''), milestones_str)
        record.weight            = parse_float(request.POST.get('weight'))
        record.height            = parse_float(request.POST.get('height'))
        record.headcircumference  = parse_float(request.POST.get('headcircumference'))
        record.chestcircumference = parse_float(request.POST.get('chestcircumference'))

        # 只有新上傳照片才覆蓋舊照片
        photo_url = save_uploaded_image(request.FILES.get('photo'))
        if photo_url:
            record.photo = photo_url

        record.update_time = timezone.now()
        record.save()

        # 全量重建里程碑關聯（先刪除再建立）
        BabyStatus.objects.filter(babyrecord=record).delete()
        milestone_names = [m.strip() for m in milestones_str.split('|') if m.strip()]
        for m_name in milestone_names:
            growth_map = BabyGrowthMap.objects.filter(growthrecord=m_name).first()
            if growth_map:
                BabyStatus.objects.create(
                    babyrecord=record,
                    babygrowthmap=growth_map,
                )

        return redirect(url_with_active_selection(request, reverse('babyinformation')))

    # ---- GET：準備表單資料 ----
    baby        = record.baby
    record_date = record.date

    age_in_months    = calculate_age_in_months(baby.birthdaytime, record_date)
    relevant_courses = get_relevant_timecourses(age_in_months)

    # 排除「其他紀錄」已達成的里程碑（不排除本筆自身，避免已勾選項目消失）
    achieved_ids_other = BabyStatus.objects.filter(
        babyrecord__baby=baby
    ).exclude(
        babyrecord=record
    ).values_list('babygrowthmap_id', flat=True)

    if relevant_courses:
        # 月齡區間 + 本筆已勾選（聯集），排除其他天已達成的
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
        'record':              record,
        'all_milestones':      all_milestones,
        'form_data':           {'record': record.note_text},
        'selected_milestones': '|'.join(record.milestones),
    })


def delete_baby_record(request, babyrecord_id):
    """
    [刪除生長紀錄] 刪除已建立的特定生長紀錄。

    安全防護：
        1. 水平越權：只有案例擁有者或家庭成員可刪除
        2. 僅接受 POST，防止透過 GET 意外觸發刪除（回傳 405）
    """
    from views.session_utils import get_current_user_profile
    from django.core.exceptions import PermissionDenied
    from django.http import HttpResponseNotAllowed

    user = get_current_user_profile(request)
    if not user:
        return redirect('login')

    record = get_object_or_404(BabyRecord, babyrecord_id=babyrecord_id)
    case   = record.baby.pregnancycase

    is_owner  = (case.user_id == user.user_id)
    is_shared = FamilyMember.objects.filter(pregnancycase_id=case, user_id=user).exists()

    # 水平越權防護
    if not (is_owner or is_shared):
        raise PermissionDenied('您沒有權限刪除此紀錄')

    # 非 POST 請求回傳 405 Method Not Allowed
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    record.delete()
    return redirect(url_with_active_selection(request, reverse('babyinformation')))
