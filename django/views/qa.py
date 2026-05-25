import json
import os
from urllib import error, request as urlrequest

from django.db.models import Max
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils import timezone
from django.urls import reverse

from core.models import QAConversation, QAMessage, UserProfile


ACTIVE_CONVERSATION_SESSION_KEY = "qa_active_conversation_id"


def _get_webhook_url():
    return "http://localhost:5678/webhook-test/django-rag-chat"


def _get_timeout_seconds():
    raw_timeout = os.getenv("N8N_RAG_TIMEOUT_SECONDS", "60").strip()
    try:
        return max(5, int(raw_timeout))
    except ValueError:
        return 60


def _stringify_source(source_item):
    if isinstance(source_item, str):
        return source_item.strip()

    if isinstance(source_item, dict):
        title = source_item.get("title") or source_item.get("source") or source_item.get("name")
        page = source_item.get("page") or source_item.get("page_number")
        excerpt = source_item.get("excerpt") or source_item.get("content") or source_item.get("text")

        parts = []
        if title:
            parts.append(str(title))
        if page is not None and str(page).strip():
            parts.append(f"第 {page} 頁")
        if excerpt:
            parts.append(str(excerpt).strip())

        if parts:
            return "｜".join(parts)

        return json.dumps(source_item, ensure_ascii=False)

    return str(source_item).strip()


def _extract_response_data(raw_body):
    try:
        data = json.loads(raw_body)
    except json.JSONDecodeError:
        return {"answer": raw_body, "sources": [], "raw": raw_body}

    if isinstance(data, list):
        data = data[0] if data else {}

    if not isinstance(data, dict):
        return {"answer": raw_body, "sources": [], "raw": data}

    answer = data.get("answer") or data.get("text") or data.get("output") or data.get("response") or ""
    if not answer and len(data) == 1:
        only_value = next(iter(data.values()))
        if isinstance(only_value, (str, int, float, bool)):
            answer = only_value

    if not answer:
        answer = json.dumps(data, ensure_ascii=False)

    sources = data.get("sources") or data.get("context") or data.get("documents") or []
    if isinstance(sources, dict):
        sources = [sources]
    elif isinstance(sources, str):
        sources = [sources]
    elif not isinstance(sources, list):
        sources = [sources] if sources else []

    normalized_sources = []
    for source_item in sources:
        source_text = _stringify_source(source_item)
        if source_text:
            normalized_sources.append(source_text)

    return {"answer": str(answer).strip(), "sources": normalized_sources, "raw": data}


def _post_to_n8n(question_text):
    webhook_url = _get_webhook_url()
    if not webhook_url:
        return None, "請先設定 N8N_RAG_WEBHOOK_URL，讓 Django 可以呼叫 n8n Webhook。"

    payload = json.dumps({"message": question_text, "question": question_text}).encode("utf-8")
    req = urlrequest.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlrequest.urlopen(req, timeout=_get_timeout_seconds()) as response:
            raw_body = response.read().decode("utf-8").strip()
            if not raw_body:
                return None, "n8n 回傳了空結果。"

            data = _extract_response_data(raw_body)
            return data, None
    except error.HTTPError as exc:
        return None, f"n8n Webhook 回應失敗：{exc.code} {exc.reason}"
    except error.URLError as exc:
        return None, f"無法連線到 n8n Webhook：{exc.reason}"


def _store_exchange(question_text, answer_text):
    if not question_text or not answer_text:
        return None

    try:
        user = UserProfile.objects.first()
    except Exception:
        user = None

    if not user:
        return None

    try:
        now = timezone.now()
        with transaction.atomic():
            conversation = QAConversation.objects.create(
                user_id=user.user_id,
                title=(question_text[:250] or "孕期知識問答"),
                create_time=now,
            )
            QAMessage.objects.create(
                qa_conversation=conversation,
                role="user",
                message=question_text,
                create_time=now,
            )
            QAMessage.objects.create(
                qa_conversation=conversation,
                role="assistant",
                message=answer_text,
                create_time=now,
            )
        return conversation
    except Exception:
        return None


def _append_message(conversation, role, message_text):
    if not conversation or not message_text:
        return

    try:
        with transaction.atomic():
            QAMessage.objects.create(
                qa_conversation=conversation,
                role=role,
                message=message_text,
                create_time=timezone.now(),
            )
    except Exception:
        return


def _get_conversation_by_id(conversation_id):
    if not conversation_id:
        return None

    return QAConversation.objects.filter(qa_conversation_id=conversation_id).first()


def _get_current_conversation_id(request):
    request_conversation_id = request.GET.get("conversation_id") or request.POST.get("conversation_id")
    if request_conversation_id:
        return request_conversation_id

    return request.session.get(ACTIVE_CONVERSATION_SESSION_KEY)


def _set_current_conversation_id(request, conversation_id):
    if conversation_id:
        request.session[ACTIVE_CONVERSATION_SESSION_KEY] = str(conversation_id)
    else:
        request.session.pop(ACTIVE_CONVERSATION_SESSION_KEY, None)


def _load_conversation_messages(conversation):
    if not conversation:
        return []

    try:
        messages = list(conversation.messages.order_by("create_time", "serno").all())
    except Exception:
        return []

    return [
        {
            "role": message.role,
            "message": message.message,
            "create_time": message.create_time,
            "is_user": str(message.role).lower() == "user",
        }
        for message in messages
    ]


def _build_conversation_item(conversation, active_conversation_id=None):
    messages = _load_conversation_messages(conversation)
    user_messages = [message for message in messages if message["is_user"]]
    assistant_messages = [message for message in messages if not message["is_user"]]

    latest_message_time = messages[-1]["create_time"] if messages else None

    return {
        "id": conversation.qa_conversation_id,
        "title": conversation.title,
        "create_time": conversation.create_time,
        "latest_message_time": latest_message_time,
        "question": user_messages[-1]["message"] if user_messages else conversation.title,
        "answers": [message["message"] for message in assistant_messages],
        "messages": messages,
        "is_active": str(conversation.qa_conversation_id) == str(active_conversation_id),
    }


def _load_recent_items(limit=20):
    items = []

    try:
        conversations = list(
            QAConversation.objects.annotate(latest_message_time=Max("messages__create_time")).order_by(
                "-latest_message_time", "-create_time"
            )[:limit]
        )
    except Exception:
        return items

    for conversation in conversations:
        item = _build_conversation_item(conversation)
        if not item["messages"]:
            continue

        items.append(item)

    return items


def _normalize_answer_text(answer_text, sources=None):
    if answer_text:
        normalized = str(answer_text).strip()
        if normalized and normalized != "目前知識庫沒有相關資訊":
            return normalized

    if sources:
        return ""

    return "目前資料庫沒有此資訊"


def qa_conversation(request):
    error_message = ""
    sources = []

    if request.method == "POST" and request.POST.get("action") == "new_conversation":
        _set_current_conversation_id(request, None)
        request.session["qa_skip_auto_load"] = True
        request.session.modified = True
        return redirect(reverse("qa_conversation"))

    if request.method == "POST":
        question = request.POST.get("question", "").strip()
        if question:
            payload, error_message = _post_to_n8n(question)
            if payload:
                sources = payload.get("sources") or []
                answer = _normalize_answer_text(payload.get("answer") or "", sources)
                if answer:
                    current_conversation_id = _get_current_conversation_id(request)
                    conversation = _get_conversation_by_id(current_conversation_id)

                    if not conversation:
                        conversation = _store_exchange(question, answer)
                    else:
                        _append_message(conversation, "user", question)
                        _append_message(conversation, "assistant", answer)

                    if conversation:
                        _set_current_conversation_id(request, conversation.qa_conversation_id)
                        request.session.modified = True
                        return redirect(f"{reverse('qa_conversation')}?conversation_id={conversation.qa_conversation_id}")

    current_conversation_id = _get_current_conversation_id(request)
    current_conversation = _get_conversation_by_id(current_conversation_id)
    skip_auto_load = request.session.pop("qa_skip_auto_load", False)

    if not current_conversation and not skip_auto_load:
        try:
            current_conversation = (
                QAConversation.objects.annotate(latest_message_time=Max("messages__create_time"))
                .order_by("-latest_message_time", "-create_time")
                .first()
            )
        except Exception:
            current_conversation = None

    if current_conversation:
        _set_current_conversation_id(request, current_conversation.qa_conversation_id)

    active_conversation_id = request.session.get(ACTIVE_CONVERSATION_SESSION_KEY)
    recent_items = _load_recent_items()
    for item in recent_items:
        item["is_active"] = str(item["id"]) == str(active_conversation_id)

    current_messages = _load_conversation_messages(current_conversation)
    current_item = _build_conversation_item(current_conversation, active_conversation_id) if current_conversation else None

    context = {
        "error_message": error_message,
        "sources": sources,
        "items": recent_items,
        "current_conversation": current_conversation,
        "current_conversation_id": active_conversation_id,
        "current_item": current_item,
        "current_messages": current_messages,
    }
    return render(request, "base/qa_conversation.html", context)
