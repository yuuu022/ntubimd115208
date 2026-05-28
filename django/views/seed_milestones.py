#!/usr/bin/env python
import os
import sys
import django

# 取得專案根目錄並加入 Python Path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 解決 Windows 主控台編碼問題
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# 初始化 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project115208.settings')
django.setup()

from core.models import BabyGrowthMap

# 定義最新的 0-3 歲（0-36 個月）兒童發育里程碑資料 (依據衛福部標準 PDF 整合版)
STANDARD_MILESTONES = [
    # 1 個月
    {"timecourse": 1, "growthrecord": "俯臥時骨盆平貼於床面 頭、臉部可抬離床面"},
    {"timecourse": 1, "growthrecord": "手會自動張開"},
    {"timecourse": 1, "growthrecord": "轉頭偏向音源"},
    {"timecourse": 1, "growthrecord": "逗他會微笑"},

    # 2 個月
    {"timecourse": 2, "growthrecord": "拉扶坐起,只有 輕微的頭部落後"},
    {"timecourse": 2, "growthrecord": "有人向他說話, 會咿呀作聲"},
    {"timecourse": 2, "growthrecord": "會對照顧者親切露出微笑"},

    # 3 個月
    {"timecourse": 3, "growthrecord": "俯臥時,能 抬頭至45度"},
    {"timecourse": 3, "growthrecord": "常舉手作 “凝視手部”"},
    {"timecourse": 3, "growthrecord": "雙眼可凝視人物 並追尋移動之物"},

    # 4 個月
    {"timecourse": 4, "growthrecord": "頭保持在中央"},
    {"timecourse": 4, "growthrecord": "坐姿扶持,頭部抱直時,脖子豎直俯臥時,會用兩隻前 臂將頭抬高至90度 幾乎一直抬起"},
    {"timecourse": 4, "growthrecord": "當搖鈴放到手中 會握住約1分鐘"},
    {"timecourse": 4, "growthrecord": "哭鬧時,會自己因 照顧者的安撫聲而停哭"},
    {"timecourse": 4, "growthrecord": "看他時,會 回看你的眼睛"},

    # 5 個月
    {"timecourse": 5, "growthrecord": "會自己翻身 (由俯臥成仰臥)"},
    {"timecourse": 5, "growthrecord": "雙手互握在一起"},
    {"timecourse": 5, "growthrecord": "手能伸向物體"},
    {"timecourse": 5, "growthrecord": "餵他吃時,會張口 或用其他的動作表示要吃"},

    # 6 個月
    {"timecourse": 6, "growthrecord": "可以自己坐在有 靠背的椅子上"},
    {"timecourse": 6, "growthrecord": "自己會拉開 在他臉上的手帕"},
    {"timecourse": 6, "growthrecord": "轉向聲源"},

    # 7 個月
    {"timecourse": 7, "growthrecord": "不需扶持 可以坐穩"},
    {"timecourse": 7, "growthrecord": "將東西由一手 换到另一手"},
    {"timecourse": 7, "growthrecord": "會發出單音"},
    {"timecourse": 7, "growthrecord": "自己能拿餅乾吃"},

    # 8 個月
    {"timecourse": 8, "growthrecord": "獨立自己爬 (腹部貼地、匍匐前進)"},
    {"timecourse": 8, "growthrecord": "用兩手拿小杯子"},
    {"timecourse": 8, "growthrecord": "會怕陌生人"},

    # 9 個月
    {"timecourse": 9, "growthrecord": "坐時,會移動身體 挪向所要的物體"},
    {"timecourse": 9, "growthrecord": "自己會抓住東西 往嘴裡送"},
    {"timecourse": 9, "growthrecord": "以揮手表示 “再見”"},

    # 10 個月
    {"timecourse": 10, "growthrecord": "拉着物體 自己站起來"},
    {"timecourse": 10, "growthrecord": "拍手"},
    {"timecourse": 10, "growthrecord": "會模仿簡單的聲音"},
    {"timecourse": 10, "growthrecord": "叫他,他會來"},

    # 11 個月
    {"timecourse": 11, "growthrecord": "雙手拉署 會移幾步"},
    {"timecourse": 11, "growthrecord": "會模仿簡單的聲音"},

    # 12 個月
    {"timecourse": 12, "growthrecord": "雙手扶著傢俱 會走幾步"},
    {"timecourse": 12, "growthrecord": "會用拇指和食 指捏起小東西"},
    {"timecourse": 12, "growthrecord": "會把一些小東西 放入杯子"},
    {"timecourse": 12, "growthrecord": "有意義的叫爸爸、媽媽"},
    {"timecourse": 12, "growthrecord": "會脫帽子"},

    # 18 個月
    {"timecourse": 18, "growthrecord": "走的很穩可以走的快"},
    {"timecourse": 18, "growthrecord": "牽著他或扶著欄杆 可以走上樓梯"},
    {"timecourse": 18, "growthrecord": "會自己上下樓梯"},
    {"timecourse": 18, "growthrecord": "會自己由椅子上爬下"},
    {"timecourse": 18, "growthrecord": "會撕紙"},
    {"timecourse": 18, "growthrecord": "會用筆亂塗"},
    {"timecourse": 18, "growthrecord": "會跟著或主動 說出一個單字"},
    {"timecourse": 18, "growthrecord": "會雙手端著杯子喝水"},
    {"timecourse": 18, "growthrecord": "幫他穿衣服會自動 的伸出胳臂或腿"},

    # 24 個月
    {"timecourse": 24, "growthrecord": "會踢球 (一腳站立另一腳踢)"},
    {"timecourse": 24, "growthrecord": "會手心朝下丟球或東西"},
    {"timecourse": 24, "growthrecord": "重疊兩塊積木"},
    {"timecourse": 24, "growthrecord": "會一頁一頁的翻圖畫書"},
    {"timecourse": 24, "growthrecord": "會將杯子的水 倒到另一個杯子"},
    {"timecourse": 24, "growthrecord": "會照著樣式 或模仿畫出垂直線"},
    {"timecourse": 24, "growthrecord": "會把瓶子 的蓋子打開"},
    {"timecourse": 24, "growthrecord": "能指出身體的一部分"},
    {"timecourse": 24, "growthrecord": "至少會講10個單字"},
    {"timecourse": 24, "growthrecord": "能正確地說出 身體六個部位名稱"},
    {"timecourse": 24, "growthrecord": "幼兒說話 半數讓人聽得懂"},
    {"timecourse": 24, "growthrecord": "自己會脫去衣服"},
    {"timecourse": 24, "growthrecord": "會打開糖果紙"},

    # 36 個月
    {"timecourse": 36, "growthrecord": "不扶東西, 能雙腳同時離地跳"},
    {"timecourse": 36, "growthrecord": "不用牽著他或扶著欄杆 可以自己上下樓梯"},
    {"timecourse": 36, "growthrecord": "能模仿別人做摺紙的動作"},
    {"timecourse": 36, "growthrecord": "能主動告知 想上廁所"},
    {"timecourse": 36, "growthrecord": "會講自己的 姓和名"},
    {"timecourse": 36, "growthrecord": "能正確的說出兩種 常見物品的用途"},
    {"timecourse": 36, "growthrecord": "能正確表達 “你的”、“我的”"},
    {"timecourse": 36, "growthrecord": "會自己穿脫 沒有鞋帶的鞋子"},
    {"timecourse": 36, "growthrecord": "能用湯匙喝東西"},
    {"timecourse": 36, "growthrecord": "會自己洗手並擦乾"},
    {"timecourse": 36, "growthrecord": "會自己穿衣服"},
    {"timecourse": 36, "growthrecord": "能和同伴們 一起玩遊戲"}
]

def seed_milestones():
    print("清除原有的成長里程碑數據...")
    try:
        # 清空原有的 babygrowthmap 紀錄，重建乾淨發育指標
        BabyGrowthMap.objects.all().delete()
        print("[OK] 原有數據清空成功。")
    except Exception as e:
        print(f"[FAIL] 清空數據失敗: {e}")

    print("開始導入最新 0-3 歲標準發育里程碑數據...")
    count_created = 0

    for milestone in STANDARD_MILESTONES:
        obj, created = BabyGrowthMap.objects.get_or_create(
            timecourse=milestone["timecourse"],
            growthrecord=milestone["growthrecord"]
        )
        if created:
            count_created += 1
            print(f"[OK] 成功導入: {milestone['timecourse']}個月 - {milestone['growthrecord']}")

    print("\n[DONE] 資料導入完成！")
    print(f"   共導入數據: {count_created} 筆")


if __name__ == "__main__":
    seed_milestones()
