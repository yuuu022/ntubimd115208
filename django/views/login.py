import json
import uuid

from django.conf import settings
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from google.oauth2 import id_token
from google.auth.transport import requests

from core.models import UserProfile


def login_page(request):
	return render(request, 'login.html')


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
	display_name = (name or email.split('@')[0])[:50]

	user_profile = UserProfile.objects.filter(email=email).first()
	if not user_profile:
		user_profile = UserProfile.objects.filter(line_name=email).first()
	if not user_profile:
		user_profile = UserProfile(
			user_id=str(uuid.uuid4()),
			line_name=display_name,
			avatar=picture or '',
			email=email,
			password='',
		)
		user_profile.save()

	update_fields = []
	if user_profile.email != email:
		user_profile.email = email
		update_fields.append('email')
	if user_profile.line_name != display_name:
		user_profile.line_name = display_name
		update_fields.append('line_name')
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


def logout_user(request):
	request.session.flush()
	return redirect('login')
