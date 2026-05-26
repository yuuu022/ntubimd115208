import calendar
import datetime

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, redirect, get_object_or_404
from core.models import BabyInformation, BabyRecord
from django.utils import timezone

MILESTONE_PREFIX = '里程碑：'


def _parse_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _get_calendar_data(records, year, month):
    cal = calendar.Calendar(firstweekday=6)
    weeks = cal.monthdayscalendar(year, month)
    record_days = {}
    for record in records:
        if record.date.year == year and record.date.month == month:
            record_days.setdefault(record.date.day, 0)
            record_days[record.date.day] += 1

    today = datetime.date.today()
    return {
        'calendar_weeks': weeks,
        'selected_year': year,
        'selected_month': month,
        'selected_month_label': f'{year}年{month}月',
        'record_days': record_days,
        'today_day': today.day if today.year == year and today.month == month else None,
        'calendar_years': sorted({today.year, year} | {record.date.year for record in records}, reverse=True),
        'calendar_months': list(range(1, 13)),
    }


def _parse_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _save_uploaded_image(image_file):
    if not image_file:
        return None
    storage = FileSystemStorage(location=settings.MEDIA_ROOT, base_url=settings.MEDIA_URL)
    filename = storage.save(f'baby_records/{image_file.name}', image_file)
    return storage.url(filename)


def _split_note_and_milestones(text):
    if not text:
        return [], ''
    text = str(text)
    if text.startswith(MILESTONE_PREFIX):
        first_line, _, rest = text.partition('\n')
        milestones_part = first_line[len(MILESTONE_PREFIX):].strip()
        milestones = [m.strip() for m in milestones_part.split(',') if m.strip()]
        return milestones, rest.strip()
    return [], text


def _build_record_text(note, milestones):
    note = (note or '').strip()
    milestones = (milestones or '').strip()
    if milestones:
        return f"{MILESTONE_PREFIX}{milestones}\n\n{note}".strip()
    return note


def _format_birth_datetime(baby):
    if not baby or not baby.birthdaytime:
        return None
    return baby.birthdaytime.strftime('%Y.%m.%d %H:%M')


def _format_datetime_local(baby):
    if not baby or not baby.birthdaytime:
        return ''
    return baby.birthdaytime.strftime('%Y-%m-%dT%H:%M')


def _get_baby_form_data(baby):
    if not baby:
        return {
            'baby_name': '',
            'birthdaytime_value': '',
            'birth_week': '',
            'pregnancy_order': 1,
            'pregnancy_count': 1,
            'birth_weight': '',
            'birth_height': '',
            'birth_head': '',
            'birth_chest': '',
            'production_method': '',
            'join_code': '',
        }

    pregnancy_count = 1
    if getattr(baby, 'pregnancycase', None):
        pregnancy_count = baby.pregnancycase.babies.count() or 1

    return {
        'baby_name': baby.name or '',
        'birthdaytime_value': _format_datetime_local(baby),
        'birth_week': _get_birth_week(baby) or '',
        'pregnancy_order': 1,
        'pregnancy_count': pregnancy_count,
        'birth_weight': baby.baby_weight or '',
        'birth_height': baby.baby_height or '',
        'birth_head': baby.babyheadcircumference or '',
        'birth_chest': baby.chestcircumference or '',
        'production_method': baby.production_method or '',
        'join_code': baby.pregnancycase.code if getattr(baby, 'pregnancycase', None) else '',
    }


def _get_birth_week(baby):
    if not baby or not baby.birthdaytime or not baby.pregnancycase or not baby.pregnancycase.menstruation:
        return None
    delta = baby.birthdaytime.date() - baby.pregnancycase.menstruation
    if delta.days < 0:
        return None
    weeks = delta.days // 7
    days = delta.days % 7
    return f'{weeks}w{days}d' if days else f'{weeks}w'


def _get_baby_summary(baby):
    if not baby:
        return {
            'baby_name': '小寶',
            'birth_week': '-',
            'birth_method': '-',
            'birth_order': '-',
            'birth_time': '-',
            'birth_height': '-',
            'birth_weight': '-',
            'birth_head': '-',
            'birth_chest': '-',
            'photo_url': None,
        }

    baby_count = 1
    if baby.pregnancycase_id:
        baby_count = baby.pregnancycase.babies.count()

    return {
        'baby_name': baby.name or '小寶',
        'birth_week': _get_birth_week(baby) or '-',
        'birth_method': baby.production_method or '-',
        'birth_order': f'第{baby_count}胎',
        'birth_time': _format_birth_datetime(baby) or '-',
        'birth_height': baby.baby_height or '-',
        'birth_weight': baby.baby_weight or '-',
        'birth_head': baby.babyheadcircumference or '-',
        'birth_chest': baby.chestcircumference or '-',
        'photo_url': None,
    }


def _get_default_baby():
    return BabyInformation.objects.first()


def baby(request):
    baby = _get_default_baby()
    records = []
    if baby is not None:
        records = BabyRecord.objects.filter(baby=baby).order_by('-date')
        for record in records:
            record.milestones, record.note_text = _split_note_and_milestones(record.record)

    today = datetime.date.today()
    year = _parse_int(request.GET.get('year'), today.year)
    month = _parse_int(request.GET.get('month'), today.month)
    if month < 1 or month > 12:
        month = today.month

    summary = _get_baby_summary(baby)
    if records:
        summary['photo_url'] = records[0].photo or summary['photo_url']

    context = {
        'baby': baby,
        'records': records,
        'baby_summary': summary,
        'baby_form': _get_baby_form_data(baby),
    }
    context.update(_get_calendar_data(records, year, month))

    return render(request, 'baby/babyinformation.html', context)


def add_baby_information(request):
    baby = _get_default_baby()
    return render(request, 'baby/add_baby_information.html', {
        'baby_form': _get_baby_form_data(baby),
        'baby': baby,
    })


def edit_baby_information(request):
    baby = _get_default_baby()
    return render(request, 'baby/edit_baby_information.html', {
        'baby_form': _get_baby_form_data(baby),
        'baby': baby,
    })


def add_baby_record(request):
    baby = _get_default_baby()
    if baby is None:
        return render(request, 'baby/add_baby_record.html', {
            'error': '請先建立寶寶資料',
        })

    if request.method == 'POST':
        date = request.POST.get('date')
        if not date:
            return render(request, 'baby/add_baby_record.html', {
                'baby': baby,
                'error': '請填寫紀錄日期',
                'form_data': request.POST,
            })

        photo_url = _save_uploaded_image(request.FILES.get('photo'))
        record_text = _build_record_text(request.POST.get('record', ''), request.POST.get('milestones', ''))
        BabyRecord.objects.create(
            baby=baby,
            date=date,
            record=record_text,
            weight=_parse_float(request.POST.get('weight')),
            height=_parse_float(request.POST.get('height')),
            headcircumference=_parse_float(request.POST.get('headcircumference')),
            chestcircumference=_parse_float(request.POST.get('chestcircumference')),
            photo=photo_url,
        )
        return redirect('babyinformation')

    baby_list = BabyInformation.objects.all()
    return render(request, 'baby/add_baby_record.html', {
        'baby': baby,
        'baby_list': baby_list,
        'form_data': {},
        'milestones': '',
    })


def edit_baby_record(request, babyrecord_id):
    record = get_object_or_404(BabyRecord, babyrecord_id=babyrecord_id)
    record.milestones, record.note_text = _split_note_and_milestones(record.record)

    if request.method == 'POST':
        date = request.POST.get('date')
        if not date:
            return render(request, 'baby/edit_baby_record.html', {
                'record': record,
                'error': '請填寫紀錄日期',
                'form_data': request.POST,
                'selected_milestones': request.POST.get('milestones', ''),
            })

        record.date = date
        record.record = _build_record_text(request.POST.get('record', ''), request.POST.get('milestones', ''))
        record.weight = _parse_float(request.POST.get('weight'))
        record.height = _parse_float(request.POST.get('height'))
        record.headcircumference = _parse_float(request.POST.get('headcircumference'))
        record.chestcircumference = _parse_float(request.POST.get('chestcircumference'))
        photo_url = _save_uploaded_image(request.FILES.get('photo'))
        if photo_url:
            record.photo = photo_url
        record.update_time = timezone.now()
        record.save()
        return redirect('babyinformation')

    return render(request, 'baby/edit_baby_record.html', {
        'record': record,
        'form_data': {'record': record.note_text},
        'selected_milestones': ','.join(record.milestones),
    })


def delete_baby_record(request, babyrecord_id):
    record = get_object_or_404(BabyRecord, babyrecord_id=babyrecord_id)
    if request.method == 'POST':
        record.delete()
    return redirect('babyinformation')
