"""Dựng trang web tĩnh từ content/baidoc.json vào thư mục docs/ (GitHub Pages).

Giao diện dùng Tailwind CSS (biên dịch sẵn thành 1 file), biểu tượng Lucide,
và GLightbox để phóng to ảnh.

Cách chạy (từ thư mục dự án):
    .venv/Scripts/python tools/build_site.py
    npx tailwindcss -i tools/input.css -o docs/assets/site.css --minify
"""
import html
import json
import re
import shutil
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
OUT = ROOT / "docs"
RAW = ROOT / "raw"

SITE_TITLE = "Thư viện Đọc mở rộng"
SLOGAN = "“Đọc hôm nay – Kiến tạo ngày mai!”"

# màu chủ đạo (theo áp phích), màu nền nhạt, biểu tượng
THEME = {
    "vu-tru": ("#5b3fd1", "#efeaff", "rocket"),
    "robot-ai": ("#16884a", "#e2f5e8", "bot"),
    "nang-luong": ("#d4520f", "#fff0e4", "leaf"),
    "suc-khoe": ("#0b7f7a", "#dff4f2", "heart-pulse"),
}

e = html.escape


def icon(name, cls="size-5"):
    svg = (TOOLS / "icons" / f"{name}.svg").read_text(encoding="utf-8")
    svg = re.sub(r"<!--.*?-->", "", svg, flags=re.S).strip()
    svg = re.sub(r'\s(class|width|height)="[^"]*"', "", svg)
    svg = svg.replace("<svg", f'<svg class="{cls}" aria-hidden="true"', 1)
    return re.sub(r"\s*\n\s*", " ", svg)


def page(title, body, color, tint, depth, desc="", lightbox=False):
    up = "../" * depth
    lb_css = f'<link rel="stylesheet" href="{up}assets/glightbox.min.css">' if lightbox else ""
    lb_js = (
        f'<script src="{up}assets/glightbox.min.js"></script>'
        "<script>GLightbox({selector:'.glightbox',touchNavigation:true,zoomable:true,openEffect:'zoom',closeEffect:'fade'});</script>"
        if lightbox else ""
    )
    return f"""<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc or SITE_TITLE)}">
<meta name="theme-color" content="{color}">
<link rel="icon" href="{up}favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Baloo+2:wght@600;700;800&family=Be+Vietnam+Pro:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{up}assets/site.css">
{lb_css}
</head>
<body class="min-h-dvh bg-paper font-body text-ink antialiased" style="--c:{color};--tint:{tint}">
{body}
{lb_js}
</body>
</html>
"""


def make_images():
    """PNG gốc -> WebP: 'm' (900px, cho thẻ và trang bài) và 'l' (1800px, khi phóng to)."""
    img_dir = OUT / "img"
    img_dir.mkdir(parents=True, exist_ok=True)
    sizes = {}
    for png in sorted(RAW.glob("*.png")):
        if png.stem == "16-sieu-am":  # bản lỗi, đã thay bằng v2
            continue
        key = png.stem.replace("-v2", "")
        im = Image.open(png).convert("RGB")
        for suffix, width in (("m", 900), ("l", 1800)):
            w = min(width, im.width)
            h = round(im.height * w / im.width)
            im.resize((w, h), Image.LANCZOS).save(img_dir / f"{key}-{suffix}.webp", "WEBP", quality=82, method=6)
            if suffix == "m":
                sizes[key] = (w, h)
    return sizes


FOOTER = f"""
<footer class="mx-auto max-w-3xl px-5 pt-10 pb-12 text-center">
  <p class="font-display text-lg font-bold text-ink-soft">{e(SLOGAN)}</p>
</footer>"""


def topic_page(t, sizes):
    color, tint, ic = THEME[t["slug"]]
    cards = []
    for n, a in enumerate(t["articles"], 1):
        w, h = sizes[a["image"]]
        load = 'fetchpriority="high"' if n == 1 else 'loading="lazy"'
        cards.append(f"""
    <li>
      <a href="{a['slug']}.html" class="group block overflow-hidden rounded-3xl bg-white shadow-[0_6px_0_var(--tint)] ring-2 ring-(--tint) transition active:translate-y-1 active:shadow-[0_2px_0_var(--tint)] hover:ring-(--c)">
        <div class="relative">
          <img src="../img/{a['image']}-m.webp" width="{w}" height="{h}" alt="" {load} class="aspect-[16/9] w-full object-cover transition duration-500 group-hover:scale-[1.03]">
          <span class="absolute top-3 left-3 rounded-full bg-white/95 px-3 py-1 text-sm font-bold text-(--c) shadow">Bài {n}</span>
        </div>
        <div class="flex items-center gap-3 px-5 py-4">
          <h2 class="flex-1 font-display text-[1.4rem] leading-tight font-bold text-balance">{e(a['title'])}</h2>
          <span class="grid size-11 shrink-0 place-items-center rounded-full bg-(--c) text-white transition group-hover:translate-x-1">{icon('arrow-right', 'size-5')}</span>
        </div>
      </a>
    </li>""")
    body = f"""
<header class="relative overflow-hidden rounded-b-[2.5rem] bg-(--c) pb-16 text-white">
  <span class="stars pointer-events-none absolute inset-0"></span>
  <div class="relative mx-auto max-w-3xl px-5 pt-5">
    <a href="../" class="inline-flex items-center gap-1.5 rounded-full bg-white/15 py-1.5 pr-4 pl-2.5 text-sm font-semibold backdrop-blur hover:bg-white/25">{icon('house', 'size-4')} {e(SITE_TITLE)}</a>
    <div class="mt-6 flex items-center gap-4">
      <span class="grid size-16 shrink-0 place-items-center rounded-2xl bg-white text-(--c) shadow-lg">{icon(ic, 'size-9')}</span>
      <div>
        <h1 class="font-display text-[2.1rem] leading-[1.05] font-extrabold sm:text-5xl">{e(t['name'])}</h1>
        <p class="mt-1 text-white/90">{e(t['subtitle'])}</p>
      </div>
    </div>
  </div>
</header>
<main class="mx-auto -mt-9 max-w-3xl px-5">
  <p class="relative inline-flex items-center gap-2 rounded-full bg-white px-5 py-2.5 font-display text-lg font-bold text-(--c) shadow-md ring-2 ring-(--c)">{icon('book-open-text', 'size-5')} Chọn một bài để đọc nhé!</p>
  <ol class="mt-6 grid gap-6 sm:grid-cols-2">{''.join(cards)}
  </ol>
</main>
{FOOTER}
"""
    return page(f"{t['name']} – {SITE_TITLE}", body, color, tint, 1, t["subtitle"])


def article_page(t, i, sizes):
    color, tint, ic = THEME[t["slug"]]
    arts = t["articles"]
    a = arts[i]
    w, h = sizes[a["image"]]
    prev_a = arts[i - 1] if i > 0 else None
    next_a = arts[i + 1] if i + 1 < len(arts) else None

    dots = "".join(
        f'<a href="{x["slug"]}.html" aria-label="Bài {k + 1}" class="block h-2 rounded-full transition-all '
        + ("w-6 bg-white" if k == i else "w-2 bg-white/45 hover:bg-white/70") + '"></a>'
        for k, x in enumerate(arts)
    )
    think = "".join(
        f'<li class="flex gap-3"><span class="grid size-8 shrink-0 place-items-center rounded-full bg-(--tint) font-bold text-(--c)">{k}</span><span class="pt-0.5">{e(q)}</span></li>'
        for k, q in enumerate(a["think"], 1)
    )

    if prev_a:
        prev_html = f"""<a href="{prev_a['slug']}.html" class="flex items-center gap-2 rounded-2xl bg-white p-4 ring-2 ring-(--tint) hover:ring-(--c)">
      <span class="text-(--c)">{icon('chevron-left', 'size-6')}</span>
      <span><span class="block text-sm font-semibold text-(--c)">Bài trước</span><span class="font-display text-[1.05rem] leading-snug font-bold">{e(prev_a['title'])}</span></span></a>"""
    else:
        prev_html = "<span></span>"
    if next_a:
        nhref, nlabel, ntitle = f"{next_a['slug']}.html", "Bài tiếp theo", next_a["title"]
    else:
        nhref, nlabel, ntitle = "./", "Đọc xong rồi!", f"Về {t['name']}"
    next_html = f"""<a href="{nhref}" class="flex items-center justify-end gap-2 rounded-2xl bg-(--c) p-4 text-right text-white shadow-lg shadow-(color:--tint) hover:brightness-110">
      <span><span class="block text-sm font-semibold text-white/85">{nlabel}</span><span class="font-display text-[1.05rem] leading-snug font-bold">{e(ntitle)}</span></span>
      {icon('chevron-right', 'size-6')}</a>"""

    src = a["source"]
    body = f"""
<header class="sticky top-0 z-20 bg-(--c) text-white shadow-md">
  <div class="mx-auto flex h-14 max-w-3xl items-center justify-between gap-3 px-3">
    <a href="./" class="inline-flex items-center gap-1 rounded-full py-2 pr-3 pl-1 font-semibold hover:bg-white/15">{icon('chevron-left', 'size-6')}<span class="truncate">{e(t['name'])}</span></a>
    <nav class="flex items-center gap-1.5" aria-label="Các bài trong chủ đề">{dots}</nav>
  </div>
</header>

<main class="mx-auto max-w-3xl px-5 pt-6 pb-4">
  <div class="flex items-center gap-2 text-sm font-semibold text-(--c)">
    <span class="grid size-7 place-items-center rounded-lg bg-(--tint)">{icon(ic, 'size-4')}</span>
    Bài {i + 1} / {len(arts)}
  </div>
  <h1 class="mt-2 font-display text-[2.2rem] leading-[1.08] font-extrabold text-balance text-(--c) sm:text-5xl">{e(a['title'])}</h1>

  <a href="../img/{a['image']}-l.webp" class="glightbox group relative mt-5 -mx-2 block overflow-hidden rounded-3xl bg-(--tint) shadow-xl ring-4 ring-white sm:mx-0" data-title="{e(a['title'])}" aria-label="Xem ảnh lớn">
    <img src="../img/{a['image']}-m.webp" srcset="../img/{a['image']}-m.webp 900w, ../img/{a['image']}-l.webp 1800w"
         sizes="(min-width: 768px) 720px, 100vw" width="{w}" height="{h}" alt="Hình minh họa: {e(a['title'])}" fetchpriority="high" class="w-full">
    <span class="absolute right-3 bottom-3 inline-flex items-center gap-1.5 rounded-full bg-black/60 px-3 py-1.5 text-sm font-semibold text-white backdrop-blur">{icon('expand', 'size-4')} Chạm để phóng to</span>
  </a>

  <div class="mt-7 flex gap-3 rounded-2xl bg-(--tint) p-4 sm:p-5">
    <span class="grid size-10 shrink-0 place-items-center rounded-full bg-white text-(--c) shadow-sm">{icon('circle-help', 'size-6')}</span>
    <p class="text-[1.15rem] leading-relaxed font-semibold">{e(a['question'])}</p>
  </div>

  <p class="mt-6 text-[1.2rem] leading-[1.8] text-pretty">{e(a['body'])}</p>

  <div class="mt-8 space-y-3">
    <details class="group rounded-2xl bg-white ring-2 ring-(--tint) open:ring-(--c)">
      <summary class="flex min-h-16 cursor-pointer items-center gap-3 px-4 py-3">
        <span class="grid size-10 shrink-0 place-items-center rounded-full bg-(--tint) text-(--c)">{icon('lightbulb', 'size-5')}</span>
        <span class="flex-1 font-display text-xl font-bold">Cùng suy nghĩ nhé!</span>
        <span class="text-(--c) transition-transform duration-300 group-open:rotate-180">{icon('chevron-down', 'size-6')}</span>
      </summary>
      <ol class="space-y-3 px-4 pb-5 text-[1.1rem] leading-relaxed">{think}</ol>
    </details>
    <details class="group rounded-2xl bg-white ring-2 ring-amber-100 open:bg-amber-50 open:ring-amber-400">
      <summary class="flex min-h-16 cursor-pointer items-center gap-3 px-4 py-3">
        <span class="grid size-10 shrink-0 place-items-center rounded-full bg-amber-100 text-amber-500">{icon('sparkles', 'size-5')}</span>
        <span class="flex-1 font-display text-xl font-bold">Điều thú vị</span>
        <span class="text-amber-600 transition-transform duration-300 group-open:rotate-180">{icon('chevron-down', 'size-6')}</span>
      </summary>
      <p class="px-4 pb-5 pl-[4.25rem] text-[1.1rem] leading-relaxed">{e(a['fun'])}</p>
    </details>
  </div>

  <p class="mt-7 text-sm leading-relaxed break-words text-ink-soft">Nguồn tham khảo: <a href="{e(src['url'])}" target="_blank" rel="noopener" class="underline decoration-1 underline-offset-2">{e(src['name'])}</a></p>

  <nav class="mt-8 grid grid-cols-2 gap-3" aria-label="Chuyển bài">
    {prev_html}
    {next_html}
  </nav>
</main>
{FOOTER}
"""
    return page(f"{a['title']} – {t['name']}", body, color, tint, 1, a["question"], lightbox=True)


def home_page(topics, sizes):
    items = []
    for t in topics:
        color, tint, ic = THEME[t["slug"]]
        a0 = t["articles"][0]
        w, h = sizes[a0["image"]]
        titles = "".join(
            f'<li class="flex items-start gap-2"><span class="mt-2.5 size-1.5 shrink-0 rounded-full bg-(--c)"></span>{e(a["title"])}</li>'
            for a in t["articles"]
        )
        items.append(f"""
    <li style="--c:{color};--tint:{tint}">
      <a href="{t['slug']}/" class="group block h-full overflow-hidden rounded-3xl bg-white shadow-[0_6px_0_var(--tint)] ring-2 ring-(--tint) transition hover:ring-(--c) active:translate-y-1">
        <div class="relative">
          <img src="img/{a0['image']}-m.webp" width="{w}" height="{h}" alt="" loading="lazy" class="aspect-[16/8] w-full object-cover">
          <span class="absolute -bottom-6 left-5 grid size-14 place-items-center rounded-2xl bg-(--c) text-white shadow-lg ring-4 ring-white">{icon(ic, 'size-7')}</span>
        </div>
        <div class="px-5 pt-9 pb-5">
          <h2 class="font-display text-[1.6rem] leading-tight font-extrabold text-(--c)">{e(t['name'])}</h2>
          <p class="text-ink-soft">{e(t['subtitle'])}</p>
          <ul class="mt-3 space-y-1 text-[1.02rem]">{titles}</ul>
          <span class="mt-4 inline-flex items-center gap-2 rounded-full bg-(--c) px-5 py-2.5 font-semibold text-white">Vào đọc 4 bài {icon('arrow-right', 'size-5')}</span>
        </div>
      </a>
    </li>""")
    body = f"""
<header class="relative overflow-hidden rounded-b-[2.5rem] bg-gradient-to-br from-[#1f2a72] to-[#3b52c9] pb-16 text-white">
  <span class="stars pointer-events-none absolute inset-0"></span>
  <div class="relative mx-auto max-w-3xl px-5 pt-10">
    <span class="grid size-14 place-items-center rounded-2xl bg-sun text-[#1f2a72] shadow-lg">{icon('book-open-text', 'size-8')}</span>
    <h1 class="mt-4 font-display text-[2.6rem] leading-[1.02] font-extrabold text-sun sm:text-6xl">{e(SITE_TITLE)}</h1>
    <p class="mt-2 text-lg text-white/90">Khám phá tri thức – Mở rộng thế giới!</p>
  </div>
</header>
<main class="mx-auto -mt-8 max-w-3xl px-5">
  <ul class="grid gap-6 sm:grid-cols-2">{''.join(items)}
  </ul>
</main>
{FOOTER}
"""
    return page(SITE_TITLE, body, "#23307a", "#e8efff", 0, "16 bài đọc mở rộng khoa học dành cho học sinh lớp 4")


def main():
    data = json.loads((ROOT / "content" / "baidoc.json").read_text(encoding="utf-8"))
    keep_qr = OUT / "qr"
    qr_backup = None
    if keep_qr.exists():  # giữ lại mã QR đã tạo
        qr_backup = ROOT / ".qr_backup"
        shutil.rmtree(qr_backup, ignore_errors=True)
        shutil.copytree(keep_qr, qr_backup)
    OUT.mkdir(exist_ok=True)
    for child in OUT.iterdir():  # xóa nội dung cũ (giữ thư mục, có thể đang được mở)
        shutil.rmtree(child) if child.is_dir() else child.unlink()
    if qr_backup:
        shutil.copytree(qr_backup, keep_qr)
        shutil.rmtree(qr_backup)
    sizes = make_images()
    (OUT / "assets").mkdir()
    for f in ("glightbox.min.js", "glightbox.min.css"):
        shutil.copy(TOOLS / "vendor" / f, OUT / "assets" / f)
    shutil.copy(TOOLS / "favicon.svg", OUT / "favicon.svg")
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
