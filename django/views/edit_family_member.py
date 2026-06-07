from django.shortcuts import render, redirect

from core.models import FamilyMember, BabyInformation, UserProfile
from core import join_requests_manager
from views.pregnancycase import resolve_active_pregnancy_case
from views.session_utils import get_current_user_profile

ALLOWED_ROLES = {'caregiver', 'viewer'}
ROLE_LABEL = {'caregiver': '照顧者', 'viewer': '觀看者', 'mom': '養育者'}


def edit_family_member(request):
    current_user = get_current_user_profile(request)
    if not current_user:
        return redirect('login')

    case = resolve_active_pregnancy_case(request, current_user)

    babies = list(BabyInformation.objects.filter(pregnancycase=case).order_by('baby_id')) if case else []
    members = list(
        FamilyMember.objects
        .filter(pregnancycase_id=case)
        .select_related('user')
        .order_by('join_time')
    ) if case else []

    # Get pending requests from JSON
    pending_members = []
    if case and case.user == current_user:
        pending_reqs = join_requests_manager.get_pending_requests(case.pregnancycase_id)
        for pr in pending_reqs:
            u = UserProfile.objects.filter(user_id=pr['user_id']).first()
            if u:
                class PendingMember:
                    def __init__(self, user_profile):
                        self.user_id = user_profile
                        self.familymember_id = user_profile.user_id
                pending_members.append(PendingMember(u))

    # 判斷目前選中的嬰幼兒
    baby_id = request.GET.get('baby_id') or request.POST.get('baby_id')
    selected_baby = None
    if baby_id:
        selected_baby = next((b for b in babies if str(b.baby_id) == str(baby_id)), None)
    if selected_baby is None and babies:
        selected_baby = babies[0]

    # 判斷目前選中的協助者
    member_id = request.GET.get('member_id') or request.POST.get('member_id')
    selected_member = None
    if member_id:
        selected_member = next(
            (m for m in members if str(m.familymember_id) == str(member_id)), None
        )
    if selected_member is None and members:
        selected_member = members[0]

    add_error = None
    add_success = None
    search_results = []

    if request.method == 'POST':
        action = request.POST.get('action', '')

        # ── 搜尋使用者 ────────────────────────────────────────
        if action == 'search':
            query = request.POST.get('search_query', '').strip()
            if query:
                search_results = list(
                    UserProfile.objects
                    .filter(name__icontains=query)
                    .exclude(user_id=current_user.user_id)
                    .order_by('name')[:10]
                )
                if not search_results:
                    add_error = f'找不到使用者「{query}」'
            else:
                add_error = '請輸入姓名或 Email 搜尋'

        # ── 新增協助者 ────────────────────────────────────────
        elif action == 'add_member':
            target_user_id = request.POST.get('target_user_id', '').strip()
            role = request.POST.get('new_role', 'caregiver').strip()
            if role not in ALLOWED_ROLES:
                role = 'caregiver'

            if not target_user_id:
                add_error = '請先搜尋並選擇使用者'
            elif not case:
                add_error = '找不到目前的胎數，無法新增協助者'
            else:
                target_user = UserProfile.objects.filter(user_id=target_user_id).first()
                if not target_user:
                    add_error = '找不到此使用者'
                elif FamilyMember.objects.filter(
                    pregnancycase_id=case, user_id=target_user
                ).exists():
                    add_error = f'「{target_user.name}」已經是此胎數的協助者'
                else:
                    FamilyMember.objects.create(
                        pregnancycase_id=case,
                        user_id=target_user,
                        role=role,
                    )
                    role_label = ROLE_LABEL.get(role, role)
                    add_success = f'已成功將「{target_user.name}」以「{role_label}」身份加入！'
                    # 重新讀取成員清單
                    members = list(
                        FamilyMember.objects
                        .filter(pregnancycase_id=case)
                        .select_related('user')
                        .order_by('join_time')
                    )

        # ── 同意加入申請 ──────────────────────────────────────
        elif action == 'approve_request':
            req_id = request.POST.get('request_id')
            role = request.POST.get('role', 'caregiver').strip()
            if role not in ALLOWED_ROLES:
                role = 'caregiver'

            if req_id and case:
                if join_requests_manager.has_pending_request(case.pregnancycase_id, req_id):
                    target_user = UserProfile.objects.filter(user_id=req_id).first()
                    if target_user:
                        FamilyMember.objects.create(
                            pregnancycase_id=case,
                            user_id=target_user,
                            role=role
                        )
                        join_requests_manager.remove_request(case.pregnancycase_id, req_id)
                        role_label = ROLE_LABEL.get(role, role)
                        add_success = f'已同意「{target_user.name}」以「{role_label}」身份加入！'

                        # 重新讀取名單
                        members = list(
                            FamilyMember.objects
                            .filter(pregnancycase_id=case)
                            .select_related('user')
                            .order_by('join_time')
                        )
                        # 重新讀取申請名單
                        pending_members = []
                        pending_reqs = join_requests_manager.get_pending_requests(case.pregnancycase_id)
                        for pr in pending_reqs:
                            u = UserProfile.objects.filter(user_id=pr['user_id']).first()
                            if u:
                                class PendingMember:
                                    def __init__(self, user_profile):
                                        self.user_id = user_profile
                                        self.familymember_id = user_profile.user_id
                                pending_members.append(PendingMember(u))
                    else:
                        add_error = '找不到該筆申請紀錄'
                else:
                    add_error = '找不到該筆申請紀錄'

        # ── 拒絕加入申請 ──────────────────────────────────────
        elif action == 'reject_request':
            req_id = request.POST.get('request_id')
            if req_id and case:
                if join_requests_manager.has_pending_request(case.pregnancycase_id, req_id):
                    target_user = UserProfile.objects.filter(user_id=req_id).first()
                    applicant_name = target_user.name if target_user else "申請者"
                    join_requests_manager.remove_request(case.pregnancycase_id, req_id)
                    add_success = f'已拒絕「{applicant_name}」的加入申請。'

                    # 重新讀取名單
                    members = list(
                        FamilyMember.objects
                        .filter(pregnancycase_id=case)
                        .select_related('user')
                        .order_by('join_time')
                    )
                    # 重新讀取申請名單
                    pending_members = []
                    pending_reqs = join_requests_manager.get_pending_requests(case.pregnancycase_id)
                    for pr in pending_reqs:
                        u = UserProfile.objects.filter(user_id=pr['user_id']).first()
                        if u:
                            class PendingMember:
                                def __init__(self, user_profile):
                                    self.user_id = user_profile
                                    self.familymember_id = user_profile.user_id
                            pending_members.append(PendingMember(u))
                else:
                    add_error = '找不到該筆申請紀錄'

        # ── 更新現有協助者 role ───────────────────────────────
        elif action == 'save_role':
            new_role = request.POST.get('role', '').strip()
            if selected_member and new_role in ALLOWED_ROLES:
                selected_member.role = new_role
                selected_member.save(update_fields=['role'])
            return redirect('profile')

    return render(request, 'user/edit_family_member.html', {
        'pregnancy_case': case,
        'babies': babies,
        'selected_baby': selected_baby,
        'family_members': members,
        'pending_members': pending_members,
        'selected_member': selected_member,
        'add_error': add_error,
        'add_success': add_success,
        'search_results': search_results,
        'role_label': ROLE_LABEL,
    })
