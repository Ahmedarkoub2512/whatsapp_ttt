import json
import os
import uuid
import textwrap

# =============== SETTINGS ===============
INPUT_FILE = "/home/user/whatsapp_ttt/whatsapp_ttt/data/chunks_new.json"      # اسم ملف JSON الأصلي
OUTPUT_DIR = "/home/user/whatsapp_ttt/whatsapp_ttt/data"      # فولدر الشنكات
CHUNK_SIZE = 900              # حجم كل شنك بالحروف
OVERLAP = 100                 # تداخل بين الشنكات (مهم للـ RAG)
# ========================================


def format_markdown(item):
    """حول عنصر JSON واحد إلى Markdown منسق"""

    md = []
    md.append(f"# Category: {item['metadata'].get('category', '')}")
    md.append(f"## Parent: {item['metadata'].get('parent_category', '')}")
    md.append(f"### Content Block\n")
    md.append(item["content"])
    md.append("\n---\n")
    return "\n".join(md)


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=OVERLAP):
    """قطع النص إلى Chunks مع تداخل"""
    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap  # التداخل
        if start < 0:
            start = 0

    return chunks


def main():
    # تحميل JSON
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    total_files = 0

    for idx, item in enumerate(data, 1):
        md_text = format_markdown(item)

        # تقسيم الشنكات
        chunks = chunk_text(md_text)

        # حفظ كل شنك في ملف
        for c_i, chunk in enumerate(chunks, 1):
            file_id = str(uuid.uuid4())[:8]
            file_path = os.path.join(
                OUTPUT_DIR,
                f"item{idx}_chunk{c_i}_{file_id}.md"
            )

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(chunk)

            total_files += 1

    print(f"✓ Done: Generated {total_files} markdown chunks in '{OUTPUT_DIR}/'.")


if __name__ == "__main__":
    main()
