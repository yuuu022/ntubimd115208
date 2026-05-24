# -*- coding: utf-8 -*-
import os
import sys
import re
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

WORKSPACE_ROOT = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PDF = os.path.join(WORKSPACE_ROOT, 'chinese_texts.pdf')

def find_txt_files(root):
    out = []
    # exclude the .venv under RAG 資料/output
    exclude_dir = os.path.normpath(os.path.join(root, 'RAG 資料', 'output', '.venv')).lower()
    for r, dirs, files in os.walk(root):
        normr = os.path.normpath(r).lower()
        if exclude_dir and exclude_dir in normr:
            continue
        for f in files:
            if f.lower().endswith('.txt'):
                out.append(os.path.join(r, f))
    out.sort()
    return out

def read_file_text(path):
    for enc in ('utf-8', 'utf-8-sig', 'big5', 'cp950', 'latin-1'):
        try:
            with open(path, 'r', encoding=enc, errors='strict') as fh:
                return fh.read()
        except Exception:
            continue
    # fallback
    with open(path, 'r', encoding='utf-8', errors='replace') as fh:
        return fh.read()

def extract_chinese(text):
    # Keep CJK unified ideographs, digits, range markers, and common CJK punctuation.
    pattern = re.compile(r'[\u4e00-\u9fff0-9~～\-\u3000-\u303f\uff00-\uffef\u2000-\u206f\n\r，。！？；：、—–“”‘’「」『』（）《》〈〉·]+')
    parts = pattern.findall(text)
    if not parts:
        return ''
    s = ''.join(parts)
    # collapse multiple blank lines
    s = re.sub(r'\n{3,}', '\n\n', s)
    return s.strip()

def arabic_to_chinese(num_text):
    num = int(num_text)
    digits = '零一二三四五六七八九'
    units = ['', '十', '百', '千']
    big_units = ['', '萬', '億', '兆']

    if num == 0:
        return '零'

    def four_digits_to_chinese(n, omit_leading_one_for_ten=False):
        parts = []
        zero_pending = False
        divisors = [1000, 100, 10, 1]
        for divisor, unit in zip(divisors, ['千', '百', '十', '']):
            d = n // divisor
            n %= divisor
            if d:
                if zero_pending:
                    parts.append('零')
                    zero_pending = False
                if unit == '十' and d == 1 and not parts and omit_leading_one_for_ten:
                    parts.append('十')
                else:
                    parts.append(digits[d] + unit)
            elif parts and n:
                zero_pending = True
        return ''.join(parts) if parts else '零'

    chunks = []
    group_index = 0
    while num > 0:
        chunk = num % 10000
        chunks.append(chunk)
        num //= 10000
        group_index += 1

    result_parts = []
    pending_zero = False
    total_groups = len(chunks)
    for idx in range(total_groups - 1, -1, -1):
        group = chunks[idx]
        if group == 0:
            if result_parts:
                pending_zero = True
            continue

        group_text = four_digits_to_chinese(group, omit_leading_one_for_ten=(idx == total_groups - 1 and group < 20))
        if result_parts and (pending_zero or group < 1000):
            result_parts.append('零')
        result_parts.append(group_text)
        if idx > 0:
            result_parts.append(big_units[idx])
        pending_zero = False

    result = ''.join(result_parts)
    result = re.sub(r'零+', '零', result)
    result = result.rstrip('零')
    return result

def convert_numbers_to_chinese(text):
    def replace_range(match):
        left = arabic_to_chinese(match.group(1))
        right = arabic_to_chinese(match.group(2))
        return f'{left}到{right}'

    text = re.sub(r'(?<!\d)(\d+)\s*[~～-]\s*(\d+)(?!\d)', replace_range, text)
    text = re.sub(r'(?<!\d)(\d+)(?!\d)', lambda m: arabic_to_chinese(m.group(1)), text)
    return text

def insert_zwsp_for_cjk(s):
    # insert zero-width space after CJK ideographs to allow breaking
    return re.sub(r'([\u4e00-\u9fff])', lambda m: m.group(1) + '\u200b', s)

def escape_html(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def register_font():
    windir = os.environ.get('WINDIR', r'C:\\Windows')
    fonts_dir = os.path.join(windir, 'Fonts')
    candidates = ['msjh.ttf', 'msjhbd.ttf', 'mingliu.ttc', 'mingliu.ttf', 'arialuni.ttf']
    for fn in candidates:
        p = os.path.join(fonts_dir, fn)
        if os.path.exists(p):
            try:
                pdfmetrics.registerFont(TTFont('CJK', p))
                return 'CJK'
            except Exception:
                continue
    return 'Helvetica'

def build_pdf(pairs, output_path):
    font_name = register_font()
    styles = getSampleStyleSheet()
    normal = ParagraphStyle('NormalCJK', parent=styles['Normal'], fontName=font_name, fontSize=11, leading=14)
    heading = ParagraphStyle('HeadingCJK', parent=styles['Heading2'], fontName=font_name, fontSize=12, leading=14)
    story = []
    for relpath, text in pairs:
        filename = os.path.splitext(os.path.basename(relpath))[0]
        story.append(Paragraph(f'來源：{filename}', heading))
        if not text:
            story.append(Paragraph('(無中文內容)', normal))
        else:
            text = convert_numbers_to_chinese(text)
            # escape HTML, preserve line breaks with <br/>, and insert zero-width spaces to allow CJK wrapping
            t = escape_html(text)
            t = t.replace('\r\n', '\n').replace('\r', '\n')
            t = t.replace('\n', '<br/>')
            t = insert_zwsp_for_cjk(t)
            story.append(Paragraph(t, normal))
        story.append(Spacer(1, 12))
    doc = SimpleDocTemplate(output_path, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    doc.build(story)

def main():
    txts = find_txt_files(WORKSPACE_ROOT)
    if not txts:
        print('未找到任何 .txt 檔案')
        sys.exit(0)
    pairs = []
    for p in txts:
        rel = os.path.relpath(p, WORKSPACE_ROOT)
        text = read_file_text(p)
        chinese = extract_chinese(text)
        pairs.append((rel, chinese))
    print('產生 PDF，檔案數：', len(pairs))
    build_pdf(pairs, OUTPUT_PDF)
    print('完成，輸出：', OUTPUT_PDF)

if __name__ == '__main__':
    main()
