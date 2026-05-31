from core.models import UserProfile


def get_current_user_profile(request):
	user_id = request.session.get('user_id')
	if not user_id:
		return None

	# ensure user_id is numeric (database uses AutoField)
	try:
		user_id_int = int(user_id)
	except (TypeError, ValueError):
		# clear invalid user_id from session to avoid repeated errors
		try:
			request.session.pop('user_id', None)
		except Exception:
			pass
		return None

	return UserProfile.objects.filter(user_id=user_id_int).first()