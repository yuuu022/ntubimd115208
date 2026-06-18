import datetime
from django.shortcuts import render, redirect
from django.utils import timezone
from core.models import BabyInformation
from views import baby_utils
from views.pregnancycase import resolve_active_pregnancy_case
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

        # ── 嚴格的出生時間多重防線驗證 ─────────────────────────────
        if b_time:
            birth_date = b_time.date()
            today = datetime.date.today()
            lmp = case.menstruation
            
            if birth_date > today:
                return render(request, 'baby/add_babyinformation.html', {
                    'error': '亂填數據警告：出生時間不能是未來日期', 
                    'case': case,
                    'form_data': request.POST
                })
            
            if lmp:
                delta_days = (birth_date - lmp).days
                if delta_days < 98:  # 14週
                    return render(request, 'baby/add_babyinformation.html', {
                        'error': '資料異常：出生日期不可早於懷孕中期(14週)，請檢查最後一次月經或出生日設定', 
                        'case': case,
                        'form_data': request.POST
                    })
                if delta_days > 301:  # 43週
                    return render(request, 'baby/add_babyinformation.html', {
                        'error': '資料異常：懷孕週數超過 43 週，不符合正常生理上限', 
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

        # ── 出生時間合理性驗證（同步改為 14w ~ 43w 醫學防線） ─────────────────────────────
        if new_birthdaytime:
            birth_date = new_birthdaytime.date()
            today = datetime.date.today()
            lmp = active_baby.pregnancycase.menstruation if active_baby.pregnancycase else None
            
            if birth_date > today:
                birth_error = '亂填數據警告：出生時間不能是未來日期'
            elif lmp and (birth_date - lmp).days < 98:  # 14週
                birth_error = '資料異常：出生日期不可早於懷孕中期(14週)，請檢查最後一次月經或出生日設定'
            elif lmp and (birth_date - lmp).days > 301:  # 43週
                birth_error = '資料異常：懷孕週數超過 43 週，不符合正常生理上限'
            else:
                birth_error = None
            
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