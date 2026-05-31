"""Query helpers for pregnancy records (linked to user, not pregnancy case)."""

from core.models import PregnancyRecord
from views.pregnancycase import get_lmp_date


def records_for_case(pregnancy_case):
    """
    Pregnancy records belong to the account (user). When the case has an LMP,
    only include entries on or after that date so a new pregnancy is not mixed
    with an earlier one.
    """
    if not pregnancy_case or not pregnancy_case.user_id:
        return PregnancyRecord.objects.none()

    qs = PregnancyRecord.objects.filter(user_id=pregnancy_case.user_id)
    lmp = get_lmp_date(pregnancy_case)
    if lmp:
        qs = qs.filter(check_date__date__gte=lmp)
    return qs
