from datetime import timedelta

from django.shortcuts import render, redirect
from django.utils import timezone

from core.models import BabyInformation, BabyRecord, FamilyMember, PregnancyCase, PregnancyRecord
from core import join_requests_manager
from .pregnancyrecords import records_for_case
from views.pregnancycase import (
    get_lmp_date,
    is_pregnancy_ongoing,
    resolve_active_baby,
    resolve_active_pregnancy_case,
    sync_active_selection_from_request,
)
from views.session_utils import get_current_user_profile
from django.conf import settings
import os
from django.contrib import messages
from django.db import IntegrityError


# 圖片儲存目標目錄（相對於 BASE_DIR）
AVATAR_SAVE_DIR = os.path.join(settings.BASE_DIR, 'core', 'static', 'media', 'user')
AVATAR_URL_PREFIX = '/static/media/user/'


def _format_number(value):
    if value is None:
        return '-'
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _latest_weight_for_selection(request, user):
    record = (
        PregnancyRecord.objects.filter(user=user)
        .exclude(weight__isnull=True)
        .order_by('-check_date', '-pregnancyrecord_id')
        .first()
    )
    if record and record.weight is not None:
        return record.weight
    return '-'


def _build_selected_child_info(request, current_user):
    sync_active_selection_from_request(request, current_user)
    today = timezone.now().date()
    case = resolve_active_pregnancy_case(request, current_user)

    # 修正：先判斷 case 層級狀態。只要這個 case 底下還有寶寶沒出生，
    # 就跟首頁/切換器一致顯示「懷孕卡」，不能只看 session 裡
    # active_baby_id 對應的那個寶寶自己是否出生。
    if case and is_pregnancy_ongoing(case):
        menstruation_date = get_lmp_date(case)
        pregnancy_month_text = '-'
        remaining_days_text = '-'
        progress_percent = 0
        if menstruation_date:
            elapsed_days = max(0, (today - menstruation_date).days)
            pregnancy_month_text = f'第 {int(elapsed_days / 30.4375) + 1} 個月'
            expected_date = case.expecteddate or (menstruation_date + timedelta(days=280))
            remaining_days = max(0, (expected_date - today).days)
            remaining_days_text = f'剩餘 {remaining_days} 天'
            progress_percent = min(100, int((elapsed_days / 280) * 100))

        return {
            'type': 'pregnancy',
            'name': getattr(case, 'order_name', case.code),
            'icon': 'pregnant_woman',
            'subtitle': case.code,
            'pregnancy_month_text': pregnancy_month_text,
            'remaining_days_text': remaining_days_text,
            'progress_percent': progress_percent,
            'menstruation_text': menstruation_date.strftime('%Y / %m / %d') if menstruation_date else '-',
            'expecteddate_text': case.expecteddate.strftime('%Y / %m / %d') if case.expecteddate else '-',
        }

    # case 已全員出生（或找不到 case），才顯示 baby 卡
    baby = resolve_active_baby(request, current_user, fallback=True)
    if baby and baby.birthdaytime:
        birth_date = baby.birthdaytime.date()
        age_days = max(0, (today - birth_date).days)
        age_weeks = age_days // 7
        age_days_remainder = age_days % 7
        age_text = f'第 {age_weeks} 週 {age_days_remainder} 天'
        age_percent = min(100, int((age_days / 364) * 100))

        latest_baby_weight = '-'
        latest_baby_height = '-'
        weight_rec = BabyRecord.objects.filter(baby=baby).exclude(weight__isnull=True).order_by('-date', '-babyrecord_id').first()
        if weight_rec and weight_rec.weight is not None:
            latest_baby_weight = _format_number(weight_rec.weight)
        height_rec = BabyRecord.objects.filter(baby=baby).exclude(height__isnull=True).order_by('-date', '-babyrecord_id').first()
        if height_rec and height_rec.height is not None:
            latest_baby_height = _format_number(height_rec.height)

        return {
            'type': 'baby',
            'name': baby.name,
            'icon': 'face',
            'subtitle': baby.pregnancycase.code if baby.pregnancycase else '嬰兒資訊',
            'age_text': age_text,
            'age_percent': age_percent,
            'birth_date': birth_date.strftime('%Y / %m / %d'),
            'birth_height': _format_number(baby.baby_height),
            'birth_weight': _format_number(baby.baby_weight),
            'birth_head_circumference': _format_number(baby.babyheadcircumference),
            'latest_weight': latest_baby_weight,
            'latest_height': latest_baby_height,
        }

    return None


def userprofile(request):
    current_user = get_current_user_profile(request)
    if not current_user:
        return redirect('login')

    latest_weight = _latest_weight_for_selection(request, current_user)
    selected_child_info = _build_selected_child_info(request, current_user)

    case = resolve_active_pregnancy_case(request, current_user)
    family_members = []
    pending_count = 0
    if case:
        family_members = list(
            FamilyMember.objects
            .filter(pregnancycase_id=case)
            .select_related('user')
            .order_by('join_time')
        )
        if case.user == current_user:
            pending_count = len(join_requests_manager.get_pending_requests(case.pregnancycase_id))

    return render(request, 'user/userprofile.html', {
        'current_user': current_user,
        'latest_weight': latest_weight,
        'selected_child_info': selected_child_info,
        'family_members': family_members,
        'pending_count': pending_count,
    })


def join_family(request):
    current_user = get_current_user_profile(request)
    if not current_user:
        return redirect('login')

    if request.method != 'POST':
        return redirect('profile')

    join_code = request.POST.get('join_code', '').strip()
    join_error = None
    join_success = None

    if not join_code:
        join_error = '請輸入加入碼'
    else:
        case = PregnancyCase.objects.filter(code=join_code).first()
        if not case:
            join_error = f'找不到加入碼「{join_code}」，請確認是否正確'
        else:
            if case.user == current_user:
                join_error = '您是此胎數的建立者，無需申請。'
            else:
                membership = FamilyMember.objects.filter(
                    pregnancycase_id=case,
                    user_id=current_user
                ).first()
                if membership:
                    role_map = {'caregiver': '照顧者', 'viewer': '觀看者', 'mom': '養育者'}
                    role_label = role_map.get(membership.role, membership.role)
                    join_success = f'已確認！您以「{role_label}」身份加入此胎數'
                elif join_requests_manager.has_pending_request(case.pregnancycase_id, current_user.user_id):
                    join_success = '您已送出加入申請，請等待養育者審核同意。'
                else:
                    join_requests_manager.add_request(case.pregnancycase_id, current_user.user_id)
                    join_success = '已成功送出加入申請，請等待養育者審核同意！'

    latest_weight = _latest_weight_for_selection(request, current_user)
    selected_child_info = _build_selected_child_info(request, current_user)
    active_case = resolve_active_pregnancy_case(request, current_user)
    family_members = []
    pending_count = 0
    if active_case:
        family_members = list(
            FamilyMember.objects
            .filter(pregnancycase_id=active_case)
            .select_related('user')
            .order_by('join_time')
        )
        if active_case.user == current_user:
            pending_count = len(join_requests_manager.get_pending_requests(active_case.pregnancycase_id))

    return render(request, 'user/userprofile.html', {
        'current_user': current_user,
        'latest_weight': latest_weight,
        'selected_child_info': selected_child_info,
        'family_members': family_members,
        'join_error': join_error,
        'join_success': join_success,
        'pending_count': pending_count,
    })


def edit_userprofile(request):
    current_user = get_current_user_profile(request)
    if not current_user:
        return redirect('login')

    return render(request, 'user/edit_userprofile.html', {
        'current_user': current_user,
    })


def update_profile(request):
    current_user = get_current_user_profile(request)
    if not current_user:
        return redirect('login')

    if request.method != 'POST':
        return redirect('edit_userprofile')

    name = request.POST.get('name', '').strip()
    email = request.POST.get('email', '').strip()
    avatar_file = request.FILES.get('avatar_file')

    if name:
        current_user.name = name
    current_user.email = email or ''

    if avatar_file:
        try:
            # 確保目標目錄存在
            os.makedirs(AVATAR_SAVE_DIR, exist_ok=True)

            # 固定檔名為 user_id.jpg，每次上傳直接覆蓋舊檔
            filename = f'{current_user.user_id}.jpg'
            save_path = os.path.join(AVATAR_SAVE_DIR, filename)

            # 寫入檔案
            with open(save_path, 'wb') as f:
                for chunk in avatar_file.chunks():
                    f.write(chunk)

            current_user.avatar = AVATAR_URL_PREFIX + filename

        except Exception as e:
            messages.error(request, f'上傳頭像失敗：{e}')

    try:
        current_user.save()
        messages.success(request, '個人資料已儲存')
    except IntegrityError as ie:
        messages.error(request, f'儲存失敗：{ie}')
    except Exception as e:
        messages.error(request, f'儲存發生錯誤：{e}')

    return redirect('profile')
