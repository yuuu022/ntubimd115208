"""Core URL routes."""

from django.urls import path
from . import views
from views.pre import qa

urlpatterns = [
    path('', views.add_user, name='add_user'),
    path('history/', views.history, name='history'),
    # 新的知識問答入口，會把問題轉送到 n8n Webhook
    path('qa/', qa.qa_conversation, name='qa_conversation'),
]
