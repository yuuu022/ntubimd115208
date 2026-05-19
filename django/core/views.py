from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from .forms import UserProfileForm
from .models import QAConversation, QAMessage, UserProfile, BabyGrowthMap, BabyStatus, BabyRecord, BabyInformation
import os
try:
    import openai
except Exception:
    openai = None
try:
    import psycopg2
except Exception:
    psycopg2 = None

def add_user(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'User successfully created!')
                return redirect('add_user')
            except Exception as e:
                messages.error(request, f'Error creating user: {e}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserProfileForm()

    return render(request, 'core/add_user.html', {'form': form})


#成長地圖畫面
def history(request):
    """成長地圖畫面 - 顯示寶寶的成長進度"""
    # 獲取所有成長地圖，按時間軸排序
    growth_maps = BabyGrowthMap.objects.all().order_by('timecourse')
    
    # 構建詳細的成長數據
    growth_timeline = []
    for growth_map in growth_maps:
        # 獲取該成長地圖關聯的所有寶寶狀態
        baby_statuses = BabyStatus.objects.filter(babygrowthmap=growth_map)
        
        status_details = []
        for status in baby_statuses:
            try:
                baby_record = status.babyrecord
                baby_info = baby_record.baby
                
                status_detail = {
                    'status_id': status.babystatus_id,
                    'baby_name': baby_info.name,
                    'record_date': baby_record.date,
                    'weight': baby_record.weight,
                    'height': baby_record.height,
                    'headcircumference': baby_record.headcircumference,
                    'chestcircumference': baby_record.chestcircumference,
                    'record': baby_record.record,
                    'photo': baby_record.photo,
                }
                status_details.append(status_detail)
            except Exception as e:
                # 如果缺少關聯數據，跳過
                continue
        
        # 構建時間軸項目
        timeline_item = {
            'map_id': growth_map.babygrowthmap_id,
            'timecourse': growth_map.timecourse,
            'growthrecord': growth_map.growthrecord,
            'baby_statuses': status_details,
            'status_count': len(status_details),
        }
        growth_timeline.append(timeline_item)
    
    context = {
        'growth_timeline': growth_timeline,
        'total_maps': len(growth_timeline),
    }
    return render(request, 'core/history.html', context)


def _get_answer_from_supabase(question_text: str) -> str:
    # Read connection info from env (with sensible defaults from provided details)
    host = os.getenv('SUPABASE_PG_HOST', 'aws-1-ap-southeast-2.pooler.supabase.com')
    port = int(os.getenv('SUPABASE_PG_PORT', 5432))
    dbname = os.getenv('SUPABASE_PG_DB', 'postgres')
    user = os.getenv('SUPABASE_PG_USER', 'postgres.phxlwzxabxeqjuaianpn')
    password = os.getenv('SUPABASE_PG_PASSWORD')

    if psycopg2 is None:
        return 'Server 尚未安裝 psycopg2，無法連線 Supabase。請安裝 psycopg2 或 psycopg[binary]。'

    conn = None
    try:
        conn = psycopg2.connect(host=host, port=port, dbname=dbname, user=user, password=password)
        cur = conn.cursor()

        # If OpenAI is available and key present, create embedding and use pgvector similarity
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai and openai_key:
            openai.api_key = openai_key
            try:
                emb_resp = openai.Embedding.create(model='text-embedding-3-small', input=question_text)
                emb = emb_resp['data'][0]['embedding']
                emb_str = '[' + ','.join(map(str, emb)) + ']'
                sql = "SELECT text FROM docs_vectors ORDER BY embedding <-> %s::vector LIMIT 5;"
                cur.execute(sql, (emb_str,))
                rows = cur.fetchall()
                if rows:
                    return '\n\n---\n\n'.join(r[0] for r in rows if r[0])
            except Exception:
                # fallback to keyword search if embedding or query fails
                pass

        # Fallback: simple keyword match on content
        kw = '%' + question_text.replace('%', '') + '%'
        cur.execute("SELECT text FROM docs_vectors WHERE text ILIKE %s LIMIT 5;", (kw,))
        rows = cur.fetchall()
        if rows:
            return '\n\n---\n\n'.join(r[0] for r in rows if r[0])

        return '找不到相關內容，請稍微改寫問題或確認資料已上傳到 docs_vectors。'
    except Exception as e:
        return f'查詢 Supabase 時發生錯誤：{e}'
    finally:
        if conn:
            conn.close()


def qa_conversation(request):
    if request.method == 'POST':
        q_text = request.POST.get('question', '').strip()
        if q_text:
            a_text = _get_answer_from_supabase(q_text)
            # Try to persist into existing qa_conversation / qa_message tables if a user exists
            try:
                user = UserProfile.objects.first()
            except Exception:
                user = None

            if user:
                try:
                    conv = QAConversation(user_id=user.user_id, title=(q_text[:250] or '問答'), create_time=timezone.now())
                    conv.save()
                    msg_user = QAMessage(qa_conversation=conv, role='user', message=q_text, create_time=timezone.now())
                    msg_user.save()
                    msg_assist = QAMessage(qa_conversation=conv, role='assistant', message=a_text, create_time=timezone.now())
                    msg_assist.save()
                except Exception:
                    # ignore persistence errors and proceed to show result
                    pass
            return redirect('qa_conversation')
    # Build display list from existing conversations (if any)
    items = []
    try:
        convs = QAConversation.objects.order_by('-create_time')[:20]
        for c in convs:
            # get messages for conversation
            msgs = list(c.messages.order_by('create_time').all())
            # identify user's question(s) and assistant answers
            questions = [m for m in msgs if m.role.lower() == 'user']
            answers = [m for m in msgs if m.role.lower() != 'user']
            if questions:
                items.append({'question': questions[-1].message, 'answers': [a.message for a in answers]})
    except Exception:
        items = []

    context = {'items': items}
    return render(request, 'core/qa_conversation.html', context)
