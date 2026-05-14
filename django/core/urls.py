from django.urls import path
from views.pre import views

urlpatterns = [
    path('', views.add_user, name='add_user'),
]
