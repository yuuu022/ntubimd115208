from django.shortcuts import render, redirect
from django.db import ProgrammingError, transaction
from django.utils import timezone
import datetime

from core.models import Feeling, PhysicalCondition, PregnancyRecord, Prenatalrecord, Userfeeling, Userphysicalcondition


def _build_feelings():
    emoji_map = {
        '愉快': '😊',
        '平靜': '😌',
        '疲倦': '😴',
        '有感': '🤰',
        '壓力': '🤯',
        '活力': '⚡',
        '頭暈': '😵‍💫',
        '感性': '🥺',
        '興奮': '🥳',
        '思考': '🤔',
        '幸福': '🥰',
        '噁心': '🤢',
    }

    feelings = Feeling.objects.order_by('feeling_id').all()
    return [
        {
            'id': feeling.feeling_id,
            'name': feeling.feeling_name,
            'emoji': emoji_map.get(feeling.feeling_name, '🙂'),
        }
        for feeling in feelings
    ]


def _build_physical_conditions():
    try:
        physicalconditions = PhysicalCondition.objects.order_by('physicalcondition_id').all()
    except ProgrammingError:
        return []

    return [
        {
            'id': physicalcondition.physicalcondition_id,
            'name': physicalcondition.physicalcondition_name,
        }
        for physicalcondition in physicalconditions
    ]


def pregnancyrecord_add(request):
    if request.method == 'POST':
        with transaction.atomic():
            # PregnancyRecord fields
            weight = request.POST.get('weight') or None
            height = request.POST.get('height') or None
            record = request.POST.get('record') or ''

            try:
                weight_val = float(weight) if weight not in (None, '') else None
            except ValueError:
                weight_val = None

            try:
                height_val = float(height) if height not in (None, '') else None
            except ValueError:
                height_val = None

            preg = PregnancyRecord.objects.create(
                pregnancycase_id=1,
                check_date=timezone.now(),
                record=record,
                weight=weight_val,
                height=height_val,
            )

            # Prenatalrecord fields
            sbp = request.POST.get('sbp')
            dbp = request.POST.get('dbp')
            fetal = request.POST.get('fetal_heart_rate')
            urine_glucose_raw = request.POST.get('urine_glucose') or ''
            urine_protein_raw = request.POST.get('urine_protein') or ''
            edema_raw = request.POST.get('edema') or ''

            # Map marker values to Chinese descriptions
            marker_map = {
                '-': '陰性',
                '+': '陽性',
                '++': '中度',
                '+++': '高度嚴重',
                '++++': '極度嚴重',
            }

            urine_glucose = marker_map.get(urine_glucose_raw, '')
            urine_protein = marker_map.get(urine_protein_raw, '')
            edema = marker_map.get(edema_raw, '')

            uploaded_photo = request.FILES.get('photo')
            photo = uploaded_photo.name if uploaded_photo else (request.POST.get('photo') or '')

            def to_int(v):
                try:
                    return int(v) if v not in (None, '') else None
                except ValueError:
                    return None

            Prenatalrecord.objects.create(
                pregnancyrecord=preg,
                sbp=to_int(sbp) or 0,
                dbp=to_int(dbp) or 0,
                fetal_heart_rate=to_int(fetal) or 0,
                urine_glucose=urine_glucose,
                urine_protein=urine_protein,
                edema=edema,
                photo=photo,
            )

            # Save selected feelings (multiple)
            feelings_selected = request.POST.getlist('feelings')
            if feelings_selected:
                uf_objs = []
                for fid in feelings_selected:
                    try:
                        fid_int = int(fid)
                    except Exception:
                        continue
                    uf_objs.append(Userfeeling(pregnancyrecord=preg, feeling_id=fid_int))
                if uf_objs:
                    Userfeeling.objects.bulk_create(uf_objs)

            # Save selected physical conditions (multiple)
            phys_selected = request.POST.getlist('physical_conditions')
            if phys_selected:
                up_objs = []
                for pid in phys_selected:
                    try:
                        pid_int = int(pid)
                    except Exception:
                        continue
                    up_objs.append(Userphysicalcondition(pregnancyrecord=preg, physicalcondition_id=pid_int))
                if up_objs:
                    Userphysicalcondition.objects.bulk_create(up_objs)

        return redirect('/pregnancyrecord/')

    context = {
        'feelings': _build_feelings(),
        'physical_conditions': _build_physical_conditions(),
        'today': datetime.date.today().isoformat(),
    }
    return render(request, 'pregnancyrecordadd.html', context)
