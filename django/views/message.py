from django.http import HttpResponseRedirect


class LoginRequiredMessage:

	def __init__(self, get_response):
		self.get_response = get_response

	def __call__(self, request):
		path = request.path_info
		allowed_paths = {
			'/login/',
			'/google_auth_login/',
			'/google_auth_login',
			'/api/auth/google/',
			'/logout/',
			'/favicon.ico',
		}

		if path.startswith('/static/') or path.startswith('/media/') or path.startswith('/logo/') or path.startswith('/admin/'):
			return self.get_response(request)

		if path not in allowed_paths and not request.session.get('user_id'):
			return HttpResponseRedirect('/login/?notice=login_required')

		return self.get_response(request)
