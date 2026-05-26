"""Core URL routes."""

from django.urls import path
from django.views.generic import TemplateView
from views import test
from views import qa, babyinformation, index, pregnancyrecordadd, userprofile, care_record, pregnancycase

urlpatterns = [
	# 首頁
    path('', index.index, name='index'),
    path('home_baby/', TemplateView.as_view(template_name='home_baby.html'), name='home_baby'),
	path('add_care_reminder/', care_record.add_care_reminder, name='add_care_reminder'),
	# 登入
    path('add_user/', test.add_user, name='add_user'),

	# 孕期紀錄
    path('pregnancyrecord/add/', pregnancyrecordadd.pregnancyrecord_add, name='pregnancy_record_add'),
	path('pregnancyrecord/', pregnancyrecordadd.pregnancyrecord, name='pregnancyrecord'),
	path('pregnancyrecord_new/', pregnancyrecordadd.pregnancyrecord_new, name='pregnancy_record_new'),

    #懷孕胎數
    path('pregnancycase/', pregnancycase.pregnancy_case, name='pregnancy_case'),
    path('add_pregnancy_baby/', pregnancycase.add_pregnancy_case, name='add_pregnancy_case'),
    path('edit_pregnancy_case/', pregnancycase.edit_pregnancy_case, name='edit_pregnancy_case'),

    # 小孩記錄
    path('babyinformation/', babyinformation.baby, name='babyinformation'),
    path('add_baby_information/', babyinformation.add_baby_information, name='add_baby_information'),
    path('add_baby_record/', babyinformation.add_baby_record, name='add_baby_record'),
    path('babyrecord/<int:babyrecord_id>/edit/', babyinformation.edit_baby_record, name='edit_baby_record'),
    path('babyrecord/<int:babyrecord_id>/delete/', babyinformation.delete_baby_record, name='delete_baby_record'),
    path('edit_baby_information/', babyinformation.edit_baby_information, name='edit_baby_information'),

    # 成長地圖
    path('babygrowthmap/', test.baby_growthmap, name='baby_growthmap'),

    # 知識問答
    path('qa/', qa.qa_conversation, name='qa_conversation'),

    # 個人資料
    path('userprofile/', userprofile.userprofile, name='profile'),
    path('edit_userprofile/', userprofile.edit_userprofile, name='edit_userprofile'),
	path('edit_family_member/', userprofile.edit_family_member, name='edit_family_member'),


]
