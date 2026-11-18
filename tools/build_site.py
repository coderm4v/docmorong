"""Dựng trang web tĩnh từ content/baidoc.json vào thư mục docs/ (GitHub Pages).

Cách chạy (từ thư mục dự án):  .venv/Scripts/python tools/build_site.py
"""
import html
import json
import shutil
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs"
RAW = ROOT / "raw"

SITE_TITLE = "Thư viện Đọc mở rộng"
COLORS = {  # màu chủ đạo của từng chủ đề, lấy theo áp phích
    "vu-tru": ("#5b3fd1", "#efeaff"),
    "robot-ai": ("#18884a", "#e3f6e9"),
    "nang-luong": ("#d4520f", "#fff0e5"),
    "suc-khoe": ("#0b7f7a", "#e0f5f3"),
}

FONT_LINK = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?family=Baloo+2:wght@600;700;800'
    '&family=Be+Vietnam+Pro:ital,wght@0,400;0,600;0,700;1,400&display=swap" rel="stylesheet">'
)

e = html.escape


def page(title, body, color, tint, depth, desc=""):
    up = "../" * depth
    return f"""<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc or SITE_TITLE)}">
<meta name="theme-color" content="{color}">
<link rel="icon" href="{up}favicon.svg" type="image/svg+xml">
{FONT_LINK}
<link rel="stylesheet" href="{up}style.css">
</head>
<body style="--c:{color};--tint:{tint}">
{body}
</body>
</html>
"""


def make_images():
    """Ảnh gốc PNG -> WebP: bản 'm' (900px, cho thẻ và trang bài) và 'l' (1800px, khi bấm phóng to)."""
    img_dir = OUT / "img"
    img_dir.mkdir(parents=True, exist_ok=True)
    sizes = {}
    for png in sorted(RAW.glob("*.png")):
        name = png.stem
        if name == "16-sieu-am":  # bản lỗi, đã thay bằng v2
            continue
        key = name.replace("-v2", "")
        im = Image.open(png).convert("RGB")
        for suffix, width in (("m", 900), ("l", 1800)):
            w = min(width, im.width)
            h = round(im.height * w / im.width)
            im.resize((w, h), Image.LANCZOS).save(img_dir / f"{key}-{suffix}.webp", "WEBP", quality=82, method=6)
            if suffix == "m":
                sizes[key] = (w, h)
    return sizes


def topic_page(t, sizes):
    color, tint = COLORS[t["slug"]]
    cards = []
    for n, a in enumerate(t["articles"], 1):
        w, h = sizes[a["image"]]
        cards.append(f"""
    <li>
      <a class="card" href="{a['slug']}.html">
        <img src="../img/{a['image']}-m.webp" width="{w}" height="{h}" alt="" {'fetchpriority="high"' if n == 1 else 'loading="lazy"'}>
        <span class="card-text"><span class="num">Bài {n}</span><span class="card-title">{e(a['title'])}</span></span>
      </a>
    </li>""")
    body = f"""
<header class="band">
  <div class="wrap">
    <a class="crumb" href="../">{e(SITE_TITLE)}</a>
    <h1>{e(t['name'])}</h1>
    <p class="sub">{e(t['subtitle'])}</p>
  </div>
</header>
<main class="wrap">
  <p class="hint">Chọn một bài để đọc nhé!</p>
  <ol class="cards">{''.join(cards)}
  </ol>
</main>
<footer class="foot wrap"><p>“Đọc hôm nay – Kiến tạo ngày mai!”</p></footer>
"""
    return page(f"{t['name']} – {SITE_TITLE}", body, color, tint, 1, t["subtitle"])


def article_page(t, i, sizes):
    color, tint = COLORS[t["slug"]]
    arts = t["articles"]
    a = arts[i]
    w, h = sizes[a["image"]]
    prev_a = arts[i - 1] if i > 0 else None
    next_a = arts[i + 1] if i + 1 < len(arts) else None
    think = "".join(f"<li>{e(q)}</li>" for q in a["think"])
    nav = []
    if prev_a:
        nav.append(f'<a class="pn prev" href="{prev_a["slug"]}.html"><small>Bài trước</small>{e(prev_a["title"])}</a>')
    else:
        nav.append('<span></span>')
    if next_a:
        nav.append(f'<a class="pn next" href="{next_a["slug"]}.html"><small>Bài tiếp theo</small>{e(next_a["title"])}</a>')
    else:
        nav.append(f'<a class="pn next" href="./"><small>Đọc xong rồi!</small>Về danh sách {e(t["name"])}</a>')
    src = a["source"]
    body = f"""
<header class="topbar">
  <div class="wrap">
    <a class="back" href="./"><span aria-hidden="true">‹</span> {e(t['name'])}</a>
    <span class="count">Bài {i + 1}/{len(arts)}</span>
  </div>
</header>
<main class="wrap article">
  <h1>{e(a['title'])}</h1>
  <a class="hero" href="../img/{a['image']}-l.webp" aria-label="Xem ảnh lớn: {e(a['title'])}">
    <img src="../img/{a['image']}-m.webp" srcset="../img/{a['image']}-m.webp 900w, ../img/{a['image']}-l.webp 1800w"
         sizes="(min-width: 760px) 720px, 100vw" width="{w}" height="{h}" alt="Hình minh họa: {e(a['title'])}" fetchpriority="high">
    <span class="zoom">Chạm để xem ảnh lớn</span>
  </a>
  <p class="question">{e(a['question'])}</p>
  <p class="text">{e(a['body'])}</p>

  <details class="box think">
    <summary>Cùng suy nghĩ nhé!</summary>
    <ol>{think}</ol>
  </details>
  <details class="box fun">
    <summary>Điều thú vị</summary>
    <p>{e(a['fun'])}</p>
  </details>

  <p class="source">Nguồn tham khảo: <a href="{e(src['url'])}" rel="noopener" target="_blank">{e(src['name'])}</a></p>

  <nav class="prevnext" aria-label="Chuyển bài">{''.join(nav)}</nav>
</main>
"""
    return page(f"{a['title']} – {t['name']}", body, color, tint, 1, a["question"])


def home_page(topics, sizes):
    items = []
    for n, t in enumerate(topics, 1):
        color, tint = COLORS[t["slug"]]
        a0 = t["articles"][0]
        w, h = sizes[a0["image"]]
        titles = "".join(f"<li>{e(a['title'])}</li>" for a in t["articles"])
        items.append(f"""
    <li style="--c:{color};--tint:{tint}">
      <a class="topic" href="{t['slug']}/">
        <img src="img/{a0['image']}-m.webp" width="{w}" height="{h}" alt="" loading="lazy">
        <span class="topic-text"><span class="topic-name">{e(t['name'])}</span><span class="topic-sub">{e(t['subtitle'])}</span>
        <ol class="mini">{titles}</ol></span>
      </a>
    </li>""")
    body = f"""
<header class="band home-band">
  <div class="wrap">
    <h1>{e(SITE_TITLE)}</h1>
    <p class="sub">Khám phá tri thức – Mở rộng thế giới!</p>
  </div>
</header>
<main class="wrap">
  <ul class="topics">{''.join(items)}
  </ul>
</main>
<footer class="foot wrap"><p>“Đọc hôm nay – Kiến tạo ngày mai!”</p></footer>
"""
    return page(SITE_TITLE, body, "#23307a", "#e8efff", 0, "16 bài đọc mở rộng khoa học dành cho học sinh lớp 4")


def main():
    data = json.loads((ROOT / "content" / "baidoc.json").read_text(encoding="utf-8"))
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    sizes = make_images()
    shutil.copy(ROOT / "tools" / "style.css", OUT / "style.css")
    shutil.copy(ROOT / "tools" / "favicon.svg", OUT / "favicon.svg")
    (OUT / ".nojekyll").write_text("")
    (OUT / "index.html").write_text(home_page(data["topics"], sizes), encoding="utf-8")
    for t in data["topics"]:
        d = OUT / t["slug"]
        d.mkdir()
        (d / "index.html").write_text(topic_page(t, sizes), encoding="utf-8")
        for i, a in enumerate(t["articles"]):
            (d / f"{a['slug']}.html").write_text(article_page(t, i, sizes), encoding="utf-8")
    print("Đã dựng xong", OUT)


if __name__ == "__main__":
    main()
