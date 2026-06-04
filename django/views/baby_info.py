"""
嬰幼兒基本資料管理
負責新增與編輯嬰幼兒資料（BabyInformation）。
"""

import datetime

from django.shortcuts import render, redirect
from django.utils import timezone

from core.models import BabyInformation

from views.baby_utils import (
    get_active_baby,
    get_baby_form_data,
    parse_float,
)

#新增嬰幼兒
def add_baby_information(request):

    from views.session_utils import get_current_user_profile
    from views.pregnancycase import resolve_active_pregnancy_case

    user = get_current_user_profile(request)
    if not user:
        return redirect('login')

    case = resolve_active_pregnancy_case(request, user)
    if not case:
        return redirect('pregnancy_case')

    if request.method == 'POST':
        baby_name = (request.POST.get('baby_name') or '').strip()

        # 解析生日時間（允許空白，出生前仍可建立紀錄）
        birthdaytime = None
        birthdaytime_str = (request.POST.get('birthdaytime') or '').strip()
        if birthdaytime_str:
            try:
                naive = datetime.datetime.strptime(birthdaytime_str, '%Y-%m-%dT%H:%M')
                birthdaytime = timezone.make_aware(naive)
            except Exception:
                pass  # 格式錯誤時保持 None，不阻斷建立流程

        new_baby = BabyInformation.objects.create(
            pregnancycase=case,
            name=baby_name or '小寶',
            birthdaytime=birthdaytime,
            baby_height=parse_float(request.POST.get('birth_height')),
            baby_weight=parse_float(request.POST.get('birth_weight')),
            babyheadcircumference=parse_float(request.POST.get('birth_head')),
            chestcircumference=parse_float(request.POST.get('birth_chest')),
            production_method=(request.POST.get('production_method') or '').strip(),
        )

        # 建立後立即切換 Session 至新嬰幼兒，避免使用者手動切換
        request.session['active_baby_id'] = new_baby.baby_id
        request.session.modified = True

        return redirect('babyinformation')

    return render(request, 'baby/add_baby_information.html', {
        'baby_form': get_baby_form_data(None),
        'baby':      None,
    })

#編輯嬰幼兒
def edit_baby_information(request):
    active_baby = get_active_baby(request)
    if active_baby is None:
        return redirect('pregnancy_case')

    if request.method == 'POST':
        baby_name = (request.POST.get('baby_name') or '').strip()
        if baby_name:
            active_baby.name = baby_name

        birthdaytime_str = (request.POST.get('birthdaytime') or '').strip()
        if birthdaytime_str:
            try:
                naive = datetime.datetime.strptime(birthdaytime_str, '%Y-%m-%dT%H:%M')
                active_baby.birthdaytime = timezone.make_aware(naive)
            except ValueError:
                pass  # 格式錯誤時保留原有值，不中斷儲存流程

        active_baby.baby_weight           = parse_float(request.POST.get('birth_weight'))
        active_baby.baby_height           = parse_float(request.POST.get('birth_height'))
        active_baby.babyheadcircumference = parse_float(request.POST.get('birth_head'))
        active_baby.chestcircumference    = parse_float(request.POST.get('birth_chest'))

        production_method = (request.POST.get('production_method') or '').strip()
        if production_method:
            active_baby.production_method = production_method

        active_baby.save()
        return redirect('pregnancy_case')

    return render(request, 'baby/edit_baby_information.html', {
        'baby_form': get_baby_form_data(active_baby),
        'baby':      active_baby,
    })
