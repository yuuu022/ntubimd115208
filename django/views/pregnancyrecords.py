from core.models import PregnancyRecord
 
 
def records_for_case(pregnancy_case):
    if not pregnancy_case or not pregnancy_case.user_id:
        return PregnancyRecord.objects.none()
 
    return PregnancyRecord.objects.filter(user_id=pregnancy_case.user_id)