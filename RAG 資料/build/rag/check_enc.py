from pathlib import Path
p=Path(r"C:\Users\Kathy\Desktop\ntubimd115208\RAG 資料\build\rag\chinese_texts.jsonl")
b=p.read_bytes()
print('bytes', len(b))
print('bom_utf8', b.startswith(b'\xef\xbb\xbf'))
print('bom_utf16le', b.startswith(b'\xff\xfe'))
print('bom_utf16be', b.startswith(b'\xfe\xff'))
for enc in ['utf-8','utf-8-sig','cp950','big5','utf-16','utf-16le','utf-16be']:
    try:
        b.decode(enc)
        print(enc, 'OK')
    except Exception as e:
        print(enc, 'FAIL', type(e).__name__)
