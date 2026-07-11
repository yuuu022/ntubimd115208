import datetime
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from core.models import BabyInformation
from views import baby_utils
from views.pregnancycase import resolve_active_pregnancy_case, validate_birth_datetime
from views.session_utils import get_current_user_profile

# ==================== 1. 新增功能 ====================
def add_baby_information(request):
    user = get_current_user_profile(request)
    if not user: 
        return redirect('login')
    case = resolve_active_pregnancy_case(request, user)
    if not case: 
        return redirect('pregnancy_case')

    if request.method == 'POST':
        b_time = None
        if (request.POST.get('birthdaytime') or '').strip():
            try: 
                b_time = timezone.make_aware(datetime.datetime.strptime(request.POST.get('birthdaytime').strip(), '%Y-%m-%dT%H:%M'))
            except ValueError:
                return render(request, 'baby/add_babyinformation.html', {
                    'error': '日期時間格式不正確', 
                    'case': case,
                    'form_data': request.POST
                })

        # ── 嚴格的出生時間多重防線驗證（共用 pregnancycase.validate_birth_datetime） ──
        birth_error = validate_birth_datetime(case.menstruation, b_time)
        if birth_error:
            return render(request, 'baby/add_babyinformation.html', {
                'error': birth_error,
                'case': case,
                'form_data': request.POST
            })
        
        # 驗證通過，建立新資料
        new_baby = BabyInformation.objects.create(
            pregnancycase=case,
            name=(request.POST.get('baby_name') or '').strip() or '小寶',
            birthdaytime=b_time,
            baby_height=baby_utils.parse_float(request.POST.get('birth_height')),
            baby_weight=baby_utils.parse_float(request.POST.get('birth_weight')),
            babyheadcircumference=baby_utils.parse_float(request.POST.get('birth_head')),
            chestcircumference=baby_utils.parse_float(request.POST.get('birth_chest')),
            production_method=(request.POST.get('production_method') or '').strip(),
        )
        request.session['active_baby_id'] = new_baby.baby_id
        request.session.modified = True
        return redirect('babyinformation')

    return render(request, 'baby/add_babyinformation.html', {'case': case})

def delete_baby_information(request):
    """刪除單一寶寶，不影響同一 case 底下的其他寶寶／懷孕紀錄本身。"""
    if request.method != 'POST':
        return redirect('pregnancy_case')

    user = get_current_user_profile(request)
    if not user:
        return redirect('login')

    baby_id = request.POST.get('baby_id')
    baby = get_object_or_404(BabyInformation, baby_id=baby_id)
    case = baby.pregnancycase

    if not case or case.user_id != user.user_id:
        return redirect('pregnancy_case')

    if request.session.get('active_baby_id') == baby.baby_id:
        request.session.pop('active_baby_id', None)
        request.session.modified = True

    baby.delete()
    return redirect('pregnancy_case')

# ==================== 2. 編輯功能 ====================
def edit_baby_information(request):
    # 從 URL 參數強制切換 active_baby（供 pregnancycase 頁面的登記出生按鈕使用）
    baby_id_param = request.GET.get('baby_id')
    if baby_id_param:
        try:
            baby_obj = BabyInformation.objects.filter(baby_id=int(baby_id_param)).first()
            if baby_obj:
                request.session['active_baby_id'] = baby_obj.baby_id
                request.session.modified = True
        except (ValueError, TypeError):
            pass
            
    active_baby = baby_utils.get_active_baby(request)
    if active_baby is None: 
        return redirect('pregnancy_case')

    if request.method == 'POST':
        # 修正原先程式漏掉的縮排
        if (request.POST.get('baby_name') or '').strip(): 
            active_baby.name = request.POST.get('baby_name').strip()

        new_birthdaytime = None
        if (request.POST.get('birthdaytime') or '').strip():
            try: 
                new_birthdaytime = timezone.make_aware(datetime.datetime.strptime(request.POST.get('birthdaytime').strip(), '%Y-%m-%dT%H:%M'))
            except ValueError: 
                return render(request, 'baby/edit_babyinformation.html', {
                    'baby': active_baby,
                    'error': '日期時間格式不正確',
                    'birthdaytime_value': request.POST.get('birthdaytime'),
                    'join_code': getattr(active_baby.pregnancycase, 'code', '') if active_baby.pregnancycase_id else '',
                    'lmp_date_value': active_baby.pregnancycase.menstruation.strftime('%Y-%m-%d') if active_baby.pregnancycase and active_baby.pregnancycase.menstruation else '',
                    'birth_weeks_value': '',
                })

        # ── 出生時間合理性驗證（共用 pregnancycase.validate_birth_datetime，14w~43w 醫學防線） ──
        if new_birthdaytime:
            lmp = active_baby.pregnancycase.menstruation if active_baby.pregnancycase else None
            birth_error = validate_birth_datetime(lmp, new_birthdaytime)

            if birth_error:
                lmp_date_value = lmp.strftime('%Y-%m-%d') if lmp else ''
                return render(request, 'baby/edit_babyinformation.html', {
                    'baby': active_baby,
                    'error': birth_error,
                    'birthdaytime_value': request.POST.get('birthdaytime'),
                    'join_code': getattr(active_baby.pregnancycase, 'code', '') if active_baby.pregnancycase_id else '',
                    'lmp_date_value': lmp_date_value,
                    'birth_weeks_value': '',
                })
            
            active_baby.birthdaytime = new_birthdaytime
            
        # 無論有沒有改 birthdaytime，其餘體徵欄位皆同步更新
        active_baby.baby_weight           = baby_utils.parse_float(request.POST.get('birth_weight'))
        active_baby.baby_height           = baby_utils.parse_float(request.POST.get('birth_height'))
        active_baby.babyheadcircumference = baby_utils.parse_float(request.POST.get('birth_head'))
        active_baby.chestcircumference    = baby_utils.parse_float(request.POST.get('birth_chest'))
        if (request.POST.get('production_method') or '').strip(): 
            active_baby.production_method = request.POST.get('production_method').strip()
        
        active_baby.save()
        return redirect('babyinformation')
    
    # ── GET 請求階段資料渲染 ──────────────────────────────────────────
    lmp_date_value = ''
    birth_weeks_value = ''

    if active_baby.pregnancycase and active_baby.pregnancycase.menstruation:
        lmp_date_value = active_baby.pregnancycase.menstruation.strftime('%Y-%m-%d')

    if active_baby.birthdaytime and active_baby.pregnancycase and active_baby.pregnancycase.menstruation:
        # 呼叫重構後的共用核心，確保前後端計算完全一致
        birth_weeks_value = baby_utils.get_birth_week(active_baby) or ''

    birthdaytime_value = active_baby.birthdaytime.strftime('%Y-%m-%dT%H:%M') if active_baby.birthdaytime else ''
    join_code = getattr(active_baby.pregnancycase, 'code', '') if active_baby.pregnancycase_id else ''

    return render(request, 'baby/edit_babyinformation.html', { 
        'baby': active_baby,
        'birthdaytime_value': birthdaytime_value,
        'join_code': join_code,
        'lmp_date_value':    lmp_date_value,  
        'birth_weeks_value': birth_weeks_value, 
    })



