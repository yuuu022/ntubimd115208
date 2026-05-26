import datetime
from django.utils import timezone
from core.models import UserProfile, PregnancyCase, BabyInformation

def baby_switcher(request):
    """Dynamic context processor to populate the baby/pregnancy case switcher in base.html."""
    user = UserProfile.objects.filter(user_id='test_user_001').first()
    if not user:
        user = UserProfile.objects.first()
    if not user:
        return {}  # No user, return empty context

    # Retrieve all pregnancy cases for this user, ordered by creation time
    cases = list(PregnancyCase.objects.filter(user=user).order_by('create_time'))

    # Calculate ordinal names
    CHINESE_NUMS = ["", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
    for idx, case in enumerate(cases):
        order = idx + 1
        if 1 <= order <= 10:
            case.order_name = f"第{CHINESE_NUMS[order]}胎"
        else:
            case.order_name = f"第{order}胎"

    switcher_items = []
    current_date = timezone.now().date()

    for case in cases:
        babies = list(case.babies.all())
        is_active = False
        if not babies:
            is_active = True
        else:
            if any(b.birthdaytime is None for b in babies):
                is_active = True

        if is_active:
            # Active pregnancy case
            menstruation_date = case.menstruation
            if not menstruation_date and case.expecteddate:
                menstruation_date = case.expecteddate - timezone.timedelta(days=280)

            if menstruation_date:
                delta = current_date - menstruation_date
                weeks = delta.days // 7
                gestation_text = f"懷孕中 ({weeks}w)"
            else:
                gestation_text = "懷孕中"

            switcher_items.append({
                'is_baby': False,
                'name': case.order_name,
                'desc': gestation_text,
                'url': '/pregnancyrecord/',  # mom's record listing
                'icon': 'pregnant_woman',
                'case_id': case.pregnancycase_id,
            })
        else:
            # Born babies
            for baby in babies:
                if baby.birthdaytime:
                    switcher_items.append({
                        'is_baby': True,
                        'name': baby.name,
                        'desc': case.order_name,
                        'url': f'/babyinformation/?baby_id={baby.baby_id}',  # baby information page
                        'icon': 'face',
                        'baby_id': baby.baby_id,
                        'case_id': case.pregnancycase_id,
                    })

    # Try to extract selected baby from URL parameters and save in session
    baby_id_param = request.GET.get('baby_id')

    if baby_id_param:
        try:
            request.session['active_baby_id'] = int(baby_id_param)
        except (ValueError, TypeError):
            pass

    # Retrieve active selection from session
    active_baby_id = request.session.get('active_baby_id')

    # Determine which switcher item is "currently active/selected"
    active_item = None
    path = request.path

    if '/babyinformation' in path or '/add_baby_record' in path or '/edit_baby_record' in path or '/edit_baby_information' in path:
        if active_baby_id:
            active_item = next((item for item in switcher_items if item['is_baby'] and item['baby_id'] == active_baby_id), None)
        if not active_item:
            active_item = next((item for item in switcher_items if item['is_baby']), None)
    elif '/pregnancyrecord' in path:
        active_item = next((item for item in switcher_items if not item['is_baby']), None)

    # Fallback to the first item if no preference matched
    if not active_item and switcher_items:
        active_item = switcher_items[0]

    return {
        'switcher_items': switcher_items,
        'switcher_active_item': active_item,
    }

