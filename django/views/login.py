import json
import logging

from django.conf import settings
from django.db import transaction
from django.db.models import Max
from django.dispatch import receiver
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from google.auth.transport import requests
from google.oauth2 import id_token
from allauth.account.signals import user_logged_in
from allauth.socialaccount.models import SocialAccount

from core.models import UserProfile

logger = logging.getLogger(__name__)

def login_page(request):
    return render(request, 'login.html')

def _next_user_id():
    max_user_id = UserProfile.objects.aggregate(max_user_id=Max('user_id')).get('max_user_id')
    return (max_user_id or 0) + 1

@receiver(user_logged_in)
def handle_allauth_login_success(request, user, **kwargs):
    social_account = SocialAccount.objects.filter(user=user).first()
    if not social_account:
        return

    provider = str(social_account.provider)
    extra_data = social_account.extra_data

    email = ''
    raw_name = ''
    picture = ''
    line_user_id = ''

    # 🌟 智慧判斷來源，不再死守 'line' 字串
    is_google = (provider == 'google')
    is_line = (provider == 'line' or provider == '2010267631' or extra_data.get('iss') == 'https://access.line.me')

    if is_google:
        email = extra_data.get('email', '')
        raw_name = extra_data.get('name', '')
        picture = extra_data.get('picture', '')
    elif is_line:
        email = extra_data.get('email', '')
        # 🎯 根據 Log 顯示，這裡直接抓 'name' 跟 'picture' 才是對的！
        raw_name = extra_data.get('name', '')
        picture = extra_data.get('picture', '')
        line_user_id = extra_data.get('sub') or social_account.uid

    if not email:
        email = f"{line_user_id or social_account.uid}@line.platform"
    display_name = (raw_name or email.split('@')[0])[:50]

    try:
        with transaction.atomic():
            user_profile = UserProfile.objects.filter(email=email).first()
            if not user_profile and is_line:
                user_profile = UserProfile.objects.filter(line_id=line_user_id).first()

            if not user_profile:
                user_profile = UserProfile(
                    user_id=_next_user_id(),
                    line_id=line_user_id if is_line else '',
                    name=display_name,
                    avatar=picture or '',
                    email=email,
                )
                user_profile.save(force_insert=True)
            else:
                update_fields = []
                if user_profile.email != email and is_google:
                    user_profile.email = email
                    update_fields.append('email')
                if user_profile.name != display_name:
                    user_profile.name = display_name
                    update_fields.append('name')
                if is_line and user_profile.line_id != line_user_id:
                    user_profile.line_id = line_user_id
                    update_fields.append('line_id')
                if picture and user_profile.avatar != picture:
                    user_profile.avatar = picture
                    update_fields.append('avatar')
                if update_fields:
                    user_profile.save(update_fields=update_fields)

        # 🎯 寫入系統 Session
        request.session['user_id'] = str(user_profile.user_id)
        request.session['user_email'] = email
        request.session['user_name'] = display_name
        request.session['user_avatar'] = picture or ''
        request.session.pop('active_case_id', None)
        request.session.pop('active_baby_id', None)
        request.session.modified = True

    except Exception as e:
        logger.error(f"社交登入同步至 UserProfile 失敗，原因: {str(e)}", exc_info=True)
        print(f"======= 🔴 LINE/Google 登入同步失敗: {str(e)} =======")
        raise e

# ==========================================
# 舊有的原生 Google 登入 API
# ==========================================
@csrf_exempt
def google_auth_login(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

    is_json_request = (request.content_type or '').startswith('application/json')
    if is_json_request:
        try:
            payload = json.loads(request.body.decode('utf-8') or '{}')
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    else:
        payload = request.POST

    token = payload.get('token') or payload.get('credential')
    if not token:
        return JsonResponse({'status': 'error', 'message': 'Missing token'}, status=400)

    client_id = getattr(settings, 'GOOGLE_CLIENT_ID', '')
    if not client_id:
        return JsonResponse({'status': 'error', 'message': 'Google client id is not configured'}, status=500)

    try:
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), client_id)
    except ValueError:
        return JsonResponse({'status': 'error', 'message': 'Invalid token'}, status=401)

    email = idinfo.get('email', '')
    if not email:
        return JsonResponse({'status': 'error', 'message': 'Email not found in token'}, status=400)

    name = idinfo.get('name') or email
    picture = idinfo.get('picture', '')
    name = (name or email.split('@')[0])[:50]

    with transaction.atomic():
        # find existing user by email or by line id
        user_profile = UserProfile.objects.filter(email=email).first()
        if not user_profile:
            user_profile = UserProfile.objects.filter(line_id=email).first()

        if not user_profile:
            # unmanaged table: assign the next numeric user_id manually
            user_profile = UserProfile(
                user_id=_next_user_id(),
                line_id='',
                name=name,
                avatar=picture or '',
                email=email,
            )
            user_profile.save(force_insert=True)

        update_fields = []
        if user_profile.email != email:
            user_profile.email = email
            update_fields.append('email')
        if user_profile.name != name:
            user_profile.name = name
            update_fields.append('name')
        # keep line_id empty for Google-based accounts
        if user_profile.line_id not in (None, ''):
            user_profile.line_id = ''
            update_fields.append('line_id')
        if picture and user_profile.avatar != picture:
            user_profile.avatar = picture
            update_fields.append('avatar')
        if update_fields:
            user_profile.save(update_fields=update_fields)

    request.session['user_id'] = str(user_profile.user_id)
    request.session['user_email'] = email
    request.session['user_name'] = name
    request.session['user_avatar'] = picture
    request.session.pop('active_case_id', None)
    request.session.pop('active_baby_id', None)
    request.session.modified = True

    if is_json_request:
        return JsonResponse({
            'status': 'success',
            'email': email,
            'name': name,
            'user_id': str(user_profile.user_id),
            'redirect_url': reverse('index'),
        })

    return HttpResponseRedirect(reverse('index'))

@require_POST
def logout_user(request):
    request.session.flush()
    return redirect('login')
