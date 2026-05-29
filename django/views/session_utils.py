from core.models import UserProfile


def get_current_user_profile(request):
	user_id = request.session.get('user_id')
	if not user_id:
		return None

	return UserProfile.objects.filter(user_id=user_id).first()