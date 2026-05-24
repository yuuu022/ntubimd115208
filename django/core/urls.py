"""Core URL routes."""

from django.urls import path
from django.views.generic import TemplateView
from views import test
from views.pre import qa

urlpatterns = [
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
    path('add_user/', test.add_user, name='add_user'),
    path('history/', test.history, name='history'),
    # 新的知識問答入口，會把問題轉送到 n8n Webhook
    path('qa/', qa.qa_conversation, name='qa_conversation'),
]
