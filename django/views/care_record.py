import datetime

from django.shortcuts import render, redirect
from django.utils import timezone
from zoneinfo import ZoneInfo

from core.models import CareStatus, CareRecord, UserProfile
from django.db import transaction, models as djmodels
from views.session_utils import get_current_user_profile


DEFAULT_USER_ID = 'ab63df64-b61f-480e-a61c-d54b851d2b5e'


def _parse_selected_date(raw):
    try:
        return datetime.date.fromisoformat(raw) if raw else timezone.localdate()
    except Exception:
        return timezone.localdate()


def add_care_reminder(request):
    selected_date = _parse_selected_date(request.GET.get('date'))
    error_message = None
    form_data = {}

    if request.method == 'POST':
        form_data = {
            'record_date': request.POST.get('record_date', ''),
            'record_time': request.POST.get('record_time', ''),
            'carestatus_id': request.POST.get('carestatus_id', ''),
            'content': request.POST.get('content', ''),
        }

        try:
            rd = datetime.date.fromisoformat(form_data['record_date'])
            rt = datetime.time.fromisoformat(form_data['record_time'])
            record_dt = datetime.datetime.combine(rd, rt)
        except Exception:
            error_message = '請提供有效的日期與時間。'

        carestatus = None
        if not error_message:
            carestatus = CareStatus.objects.filter(carestatus_id=form_data['carestatus_id']).first()
            if not carestatus:
                error_message = '請選擇有效的類別。'

        current_user = get_current_user_profile(request)
        if not error_message and not current_user:
            error_message = '找不到對應的使用者。'

        if not error_message:
            # Some environments have carerecord_id without a DB default/sequence.
            # Ensure we provide a non-null PK by selecting max+1 inside a transaction.
            with transaction.atomic():
                max_row = CareRecord.objects.aggregate(max_id=djmodels.Max('carerecord_id'))
                next_id = (max_row.get('max_id') or 0) + 1
                CareRecord.objects.create(
                    carerecord_id=next_id,
                    user=current_user,
                    carestatus=carestatus,
                    recordtime=record_dt,
                    content=form_data['content'][:255],
                    create_time=datetime.datetime.now(ZoneInfo('Asia/Taipei')).replace(tzinfo=None),
                )
            return redirect(f"/?date={form_data['record_date']}")

    carestatus_list = list(CareStatus.objects.all())
    return render(request, 'index/add_care_reminder.html', {
        'selected_date_iso': selected_date.isoformat(),
        'selected_date_label': selected_date.strftime('%Y年%m月%d日'),
        'carestatus_list': carestatus_list,
        'error_message': error_message,
        'form_data': form_data,
    })


def set_care_status(request):
    if request.method != 'POST':
        return redirect('/')

    selected_date = _parse_selected_date(request.POST.get('selected_date'))
    care_id = request.POST.get('carerecord_id')
    new_state = request.POST.get('state') in ('1', 'true', 'True', 'on')

    current_user = get_current_user_profile(request)
    if care_id and current_user:
        care_record = CareRecord.objects.filter(carerecord_id=care_id, user=current_user).first()
        if care_record:
            care_record.state = new_state
            care_record.save(update_fields=['state'])

    return redirect(f'/?date={selected_date.isoformat()}')
