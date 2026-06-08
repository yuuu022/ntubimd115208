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
            except Exception: 
                pass

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

    return render(request, 'baby/add_babyinformation.html')


# ==================== 2. 編輯功能 ====================
def edit_baby_information(request):
    active_baby = baby_utils.get_active_baby(request)
    if active_baby is None: 
        return redirect('pregnancy_case')

    if request.method == 'POST':
        if (request.POST.get('baby_name') or '').strip(): 
            active_baby.name = request.POST.get('baby_name').strip()
        if (request.POST.get('birthdaytime') or '').strip():
            try: 
                active_baby.birthdaytime = timezone.make_aware(datetime.datetime.strptime(request.POST.get('birthdaytime').strip(), '%Y-%m-%dT%H:%M'))
            except ValueError: 
                pass
        active_baby.baby_weight           = baby_utils.parse_float(request.POST.get('birth_weight'))
        active_baby.baby_height           = baby_utils.parse_float(request.POST.get('birth_height'))
        active_baby.babyheadcircumference = baby_utils.parse_float(request.POST.get('birth_head'))
        active_baby.chestcircumference    = baby_utils.parse_float(request.POST.get('birth_chest'))
        if (request.POST.get('production_method') or '').strip(): 
            active_baby.production_method = request.POST.get('production_method').strip()
        
        active_baby.save()
        return redirect('babyinformation')

    # GET 階段：將時間與加入碼格式化直接傳給 Template 渲染
    birthdaytime_value = active_baby.birthdaytime.strftime('%Y-%m-%dT%H:%M') if active_baby.birthdaytime else ''
    join_code = getattr(active_baby.pregnancycase, 'code', '') if active_baby.pregnancycase_id else ''

    return render(request, 'baby/edit_babyinformation.html', { 
        'baby': active_baby,
        'birthdaytime_value': birthdaytime_value,
        'join_code': join_code,
    })