import json
import os
from django.conf import settings
from django.utils import timezone

JSON_PATH = os.path.join(settings.BASE_DIR, 'core', 'join_requests.json')

def _load_requests():
    if not os.path.exists(JSON_PATH):
        return []
    try:
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

def _save_requests(requests):
    try:
        # Ensure directories exist
        os.makedirs(os.path.dirname(JSON_PATH), exist_ok=True)
        with open(JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(requests, f, indent=4, ensure_ascii=False)
    except Exception:
        pass

def add_request(case_id, user_id):
    requests = _load_requests()
    # Check if duplicate
    for r in requests:
        if int(r['case_id']) == int(case_id) and int(r['user_id']) == int(user_id):
            return False
    requests.append({
        'case_id': int(case_id),
        'user_id': int(user_id),
        'join_time': timezone.now().isoformat()
    })
    _save_requests(requests)
    return True

def remove_request(case_id, user_id):
    requests = _load_requests()
    new_requests = [
        r for r in requests 
        if not (int(r['case_id']) == int(case_id) and int(r['user_id']) == int(user_id))
    ]
    _save_requests(new_requests)

def get_pending_requests(case_id):
    requests = _load_requests()
    return [r for r in requests if int(r['case_id']) == int(case_id)]

def has_pending_request(case_id, user_id):
    requests = _load_requests()
    return any(int(r['case_id']) == int(case_id) and int(r['user_id']) == int(user_id) for r in requests)
