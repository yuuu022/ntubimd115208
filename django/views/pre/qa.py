"""Django knowledge Q&A proxy for n8n RAG."""

import json
import os
from urllib import error, request as urlrequest

from django.shortcuts import render
from django.utils import timezone

from core.models import QAConversation, QAMessage, UserProfile


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
        return

    try:
        user = UserProfile.objects.first()
    except Exception:
        user = None

    if not user:
        return

    try:
        conversation = QAConversation.objects.create(
            user_id=user.user_id,
            title=(question_text[:250] or "孕期知識問答"),
            create_time=timezone.now(),
        )
        QAMessage.objects.create(
            qa_conversation=conversation,
            role="user",
            message=question_text,
            create_time=timezone.now(),
        )
        QAMessage.objects.create(
            qa_conversation=conversation,
            role="assistant",
            message=answer_text,
            create_time=timezone.now(),
        )
    except Exception:
        pass


def _load_recent_items(limit=20):
    items = []

    try:
        conversations = QAConversation.objects.order_by("-create_time")[:limit]
    except Exception:
        return items

    for conversation in conversations:
        try:
            messages = list(conversation.messages.order_by("create_time").all())
        except Exception:
            continue

        questions = [message for message in messages if message.role.lower() == "user"]
        answers = [message for message in messages if message.role.lower() != "user"]
        if not questions:
            continue

        items.append(
            {
                "question": questions[-1].message,
                "answers": [answer.message for answer in answers],
                "create_time": conversation.create_time,
            }
        )

    return items


def qa_conversation(request):
    recent_items = _load_recent_items()
    question = ""
    answer = ""
    error_message = ""
    sources = []

    if request.method == "POST":
        question = request.POST.get("question", "").strip()
        if question:
            payload, error_message = _post_to_n8n(question)
            if payload:
                answer = payload.get("answer") or ""
                sources = payload.get("sources") or []
                if answer:
                    _store_exchange(question, answer)
            else:
                answer = ""

    context = {
        "question": question,
        "answer": answer,
        "error_message": error_message,
        "sources": sources,
        "items": recent_items,
    }
    return render(request, "core/qa_conversation.html", context)
