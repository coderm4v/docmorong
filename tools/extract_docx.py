"""Đọc file Word 16 bài đọc và xuất ra content/baidoc.json.

Cách chạy: python -I tools/extract_docx.py <đường-dẫn-document.xml> <file-json-ra>
"""
import json
import re
import sys

TOPICS = [
    # slug, tên hiển thị (theo áp phích), màu
    ("vu-tru", "Khám phá Vũ trụ"),
    ("robot-ai", "Rô-bốt và AI"),
    ("nang-luong", "Năng lượng và Môi trường"),
    ("suc-khoe", "Khoa học và Sức khỏe"),
]

ARTICLE_SLUGS = [
    "tau-tham-do-sao-hoa", "he-mat-troi", "kinh-thien-van-hubble", "tram-vu-tru-quoc-te",
    "canh-tay-robot", "robot-benh-vien", "robot-hut-bui", "tri-tue-nhan-tao",
    "dien-mat-troi", "dien-gio", "xe-buyt-dien", "ngoi-nha-tiet-kiem-nang-luong",
    "kinh-hien-vi", "may-mri", "vac-xin", "may-sieu-am",
]

IMAGES = [
    "01-sao-hoa", "02-he-mat-troi", "03-hubble", "04-tram-vu-tru",
    "05-canh-tay-robot", "06-robot-benh-vien", "07-robot-hut-bui", "08-tri-tue-nhan-tao",
    "09-dien-mat-troi", "10-dien-gio", "11-xe-buyt-dien", "12-ngoi-nha-xanh",
    "13-kinh-hien-vi", "14-may-mri", "15-vac-xin", "16-sieu-am",
]

PLACEHOLDER = "[VỊ TRÍ CHÈN ẢNH MINH HỌA]"


def paragraphs(xml):
    out = []
    for p in re.findall(r"<w:p[ >].*?</w:p>", xml, re.S):
        t = "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", p))
        t = (t.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
              .replace("&quot;", '"').replace("&apos;", "'")).strip()
        if t:
            out.append(t)
    return out


def parse_source(line):
    body = line.split(":", 1)[1].strip()
    m = re.search(r"(https?://\S+)$", body)
    url = m.group(1) if m else ""
    name = body[: m.start()].rstrip(" –-") if m else body
    return {"name": name.strip(), "url": url}


def main(src, dst):
    lines = paragraphs(open(src, encoding="utf-8").read())
    topics = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.isupper() and i + 1 < len(lines):
            slug, name = TOPICS[len(topics)]
            topics.append({"slug": slug, "name": name, "subtitle": lines[i + 1], "articles": []})
            i += 2
            continue
        if i + 1 < len(lines) and lines[i + 1] == PLACEHOLDER:
            n = sum(len(t["articles"]) for t in topics)
            art = {
                "slug": ARTICLE_SLUGS[n],
                "image": IMAGES[n],
                "title": line,
                "question": lines[i + 2],
                "body": lines[i + 3],
            }
            assert lines[i + 4] == "Cùng suy nghĩ nhé!", lines[i + 4]
            art["think"] = [re.sub(r"^\d+\.\s*", "", lines[i + 5]), re.sub(r"^\d+\.\s*", "", lines[i + 6])]
            assert lines[i + 7].startswith("Điều thú vị:"), lines[i + 7]
            art["fun"] = lines[i + 7].split(":", 1)[1].strip()
            assert lines[i + 8].startswith("Nguồn tham khảo:"), lines[i + 8]
            art["source"] = parse_source(lines[i + 8])
            topics[-1]["articles"].append(art)
            i += 9
            continue
        raise SystemExit(f"Dòng không nhận ra: {line!r}")

    assert len(topics) == 4 and all(len(t["articles"]) == 4 for t in topics)
    with open(dst, "w", encoding="utf-8") as f:
        json.dump({"topics": topics}, f, ensure_ascii=False, indent=2)
    print("OK", sum(len(t["articles"]) for t in topics), "bài")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
