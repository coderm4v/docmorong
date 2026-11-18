"""Slide chiếu 16:9 gồm cả 4 mã QR, bố cục theo áp phích (4 ô 2x2, tranh + mã QR + nút).
Vẽ trực tiếp ở đúng độ phân giải màn hình; mỗi ô của mã QR là số điểm ảnh nguyên → cạnh sắc.

Cách chạy: .venv/Scripts/python tools/make_slide.py
Kết quả trong qr-anh/:
  slide-4-ma-qr-fullhd.png   1920x1080 (máy chiếu, TV thông thường)
  slide-4-ma-qr-4k.png       3840x2160 (màn hình 4K)
  slide-4-ma-qr.pptx         1 slide PowerPoint dùng ảnh 4K, mở là chiếu được
"""
import math
from io import BytesIO
from pathlib import Path

import cv2
import numpy as np
import segno
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "tools" / "fonts"
ART = ROOT / "raw" / "poster"
OUT = ROOT / "qr-anh"
BASE_URL = "https://coderm4v.github.io/docmorong/"

NAVY = "#23307a"
SUN = "#ffc531"

# số, slug, tên, màu đậm (nhãn, nút), màu viền ô, màu nền cột QR, tranh
TOPICS = [
    ("01", "vu-tru", "Khám phá Vũ trụ", "#6a3fd6", "#b9a6f2", "#f1ecff", "p1-vu-tru"),
    ("02", "robot-ai", "Rô-bốt và AI", "#1f9a46", "#9fdcae", "#ecf8ee", "p2-robot-ai"),
    ("03", "nang-luong", "Năng lượng và Môi trường", "#e8621a", "#f6c39e", "#fff3ea", "p3-nang-luong"),
    ("04", "suc-khoe", "Khoa học và Sức khỏe", "#138a7e", "#9fd9d2", "#e8f7f5", "p4-suc-khoe"),
]


def baloo(size, weight="ExtraBold"):
    f = ImageFont.truetype(str(FONTS / "Baloo2.ttf"), size)
    f.set_variation_by_name(weight)
    return f


def vn(size):
    return ImageFont.truetype(str(FONTS / "BeVietnamPro-SemiBold.ttf"), size)


def rgb(hexcolor):
    return tuple(int(hexcolor[i:i + 2], 16) for i in (1, 3, 5))


def qr_img(url, module):
    qr = segno.make(url, error="m", micro=False)
    buf = BytesIO()
    qr.save(buf, kind="png", scale=module, border=0, dark="#000000", light="#ffffff")
    buf.seek(0)
    return Image.open(buf).convert("RGB")


def cover(im, w, h, ax=0.5, ay=0.5):
    r = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    x, y = round((im.width - w) * ax), round((im.height - h) * ay)
    return im.crop((x, y, x + w, y + h))


def rmask(w, h, r):
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), radius=r, fill=255)
    return m


def star(d, cx, cy, r, fill):
    pts = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5
        rr = r if k % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=fill)


def shadow(im, box, r, s, alpha=70, blur=14, dy=8):
    x0, y0, x1, y1 = (round(v) for v in box)
    pad = blur * 3 * s
    sh = Image.new("L", (x1 - x0 + 2 * pad, y1 - y0 + 2 * pad), 0)
    ImageDraw.Draw(sh).rounded_rectangle((pad, pad + dy * s, pad + x1 - x0, pad + y1 - y0 + dy * s), radius=r, fill=alpha)
    sh = sh.filter(ImageFilter.GaussianBlur(blur * s))
    im.paste(Image.new("RGB", sh.size, (30, 50, 110)), (x0 - pad, y0 - pad), sh)


def phone_icon(d, x, y, h, color):
    w = h * 0.58
    d.rounded_rectangle((x, y, x + w, y + h), radius=h * 0.16, fill="white")
    m = h * 0.09
    d.rounded_rectangle((x + m, y + m * 1.6, x + w - m, y + h - m * 1.8), radius=h * 0.06, fill=color)


def render(s):
    """s = 1 → 1920x1080; s = 2 → 3840x2160. Toạ độ viết theo khung 1920x1080 rồi nhân s."""
    S = lambda v: round(v * s)  # noqa: E731
    W, H = S(1920), S(1080)

    # nền trời xanh nhạt
    t = np.linspace(0, 1, H)[:, None]
    top, bot = np.array([214, 236, 255]), np.array([238, 247, 255])
    grad = (top * (1 - t) + bot * t).astype(np.uint8)
    im = Image.fromarray(np.repeat(grad[:, None, :], W, axis=1).reshape(H, W, 3))
    d = ImageDraw.Draw(im)
    # vệt sáng mềm
    glow = Image.new("L", (W, H), 0)
    gd = ImageDraw.Draw(glow)
    gd.ellipse((S(-300), S(820), S(900), S(1400)), fill=150)
    gd.ellipse((S(1100), S(-260), S(2300), S(260)), fill=120)
    glow = glow.filter(ImageFilter.GaussianBlur(S(80)))
    im.paste(Image.new("RGB", (W, H), "white"), (0, 0), glow)
    d = ImageDraw.Draw(im)

    # ---- tiêu đề: khung xanh đậm bo tròn ----
    hw, hh, hy = S(1080), S(122), S(10)
    hx = (W - hw) // 2
    shadow(im, (hx, hy, hx + hw, hy + hh), S(56), s, alpha=90)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((hx, hy, hx + hw, hy + hh), radius=S(56), fill=NAVY)
    f_t = baloo(S(56))
    a, b, c = "4 ", "Thư viện ", "Đọc Mở Rộng"
    total = sum(d.textlength(x, font=f_t) for x in (a, b, c))
    x = (W - total) / 2
    ty = hy - S(2)
    for part, col in ((a, SUN), (b, "white"), (c, SUN)):
        d.text((x, ty), part, font=f_t, fill=col)
        x += d.textlength(part, font=f_t)
    f_sub = vn(S(24))
    sub = "Khám phá tri thức – Mở rộng thế giới!"
    d.text(((W - d.textlength(sub, font=f_sub)) / 2, hy + S(80)), sub, font=f_sub, fill=(225, 232, 255))
    # sao trang trí
    for (cx, cy, r) in [(70, 60, 22), (175, 120, 12), (1790, 62, 26), (1870, 130, 14), (1700, 120, 11)]:
        star(d, S(cx), S(cy), S(r), SUN)

    # ---- 4 ô ----
    mx, gx, top_y, ph, gy = 26, 26, 150, 420, 18
    pw = (1920 - 2 * mx - gx) / 2  # 921
    module = 9 * s                  # 33 ô x 9 = 297 px (Full HD)
    qpad = S(14)
    urls = []
    for i, (num, slug, name, color, border, tint, art) in enumerate(TOPICS):
        url = f"{BASE_URL}{slug}/"
        urls.append(url)
        col, row = i % 2, i // 2
        x0 = S(mx + col * (pw + gx))
        y0 = S(top_y + row * (ph + gy))
        w, h = S(pw), S(ph)
        r = S(30)
        bw = S(6)

        shadow(im, (x0, y0, x0 + w, y0 + h), r, s, alpha=60)
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((x0, y0, x0 + w, y0 + h), radius=r, fill=border)

        # tranh nền + cột phải màu nhạt cho mã QR
        iw, ih = w - 2 * bw, h - 2 * bw
        q = qr_img(url, module)
        box = q.width + 2 * qpad
        colw = box + S(44)
        tr = rgb(tint)
        fade_w = S(70)
        vis_w = iw - colw + fade_w  # tranh chỉ chiếm phần bên trái → giữ trọn hình
        photo = Image.new("RGBA", (iw, ih), tr + (255,))
        photo.paste(cover(Image.open(ART / f"{art}.png").convert("RGB"), vis_w, ih), (0, 0))
        over = Image.new("RGBA", (iw, ih), (0, 0, 0, 0))
        od = ImageDraw.Draw(over)
        start = iw - colw - fade_w
        for k in range(fade_w):
            od.line([(start + k, 0), (start + k, ih)], fill=tr + (int(235 * k / fade_w),))
        od.rectangle((iw - colw, 0, iw, ih), fill=tr + (235,))
        photo = Image.alpha_composite(photo, over).convert("RGB")
        im.paste(photo, (x0 + bw, y0 + bw), rmask(iw, ih, r - bw))
        d = ImageDraw.Draw(im)

        # nhãn tên chủ đề (trên tranh, góc trái)
        label = f"{num}. {name}"
        maxw = iw - colw - S(40)
        size = 40
        while True:
            f_l = baloo(S(size))
            lw = d.textlength(label, font=f_l)
            if lw + S(48) <= maxw or size <= 26:
                break
            size -= 1
        lx, ly, lh = x0 + bw + S(18), y0 + bw + S(16), S(62)
        shadow(im, (lx, ly, lx + lw + S(48), ly + lh), lh // 2, s, alpha=70, blur=8, dy=4)
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((lx, ly, lx + lw + S(48), ly + lh), radius=lh // 2, fill=color, outline="white", width=S(3))
        asc, desc = f_l.getmetrics()
        d.text((lx + S(24), ly + (lh - asc - desc) / 2 + S(4)), label, font=f_l, fill="white")

        # khung trắng + mã QR
        cx0 = x0 + w - bw - colw
        bx = cx0 + (colw - box) // 2
        by = y0 + S(14)
        shadow(im, (bx, by, bx + box, by + box), S(18), s, alpha=55, blur=8, dy=4)
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((bx, by, bx + box, by + box), radius=S(18), fill="white", outline=border, width=S(3))
        im.paste(q, (bx + qpad, by + qpad))

        # nút "Quét mã để đọc ngay!" (1 dòng, nằm gọn trong ô)
        btw, bth = box, S(50)
        btx, bty = bx, by + box + S(8)
        d.rounded_rectangle((btx, bty, btx + btw, bty + bth), radius=bth // 2, fill=color)
        phone_icon(d, btx + S(18), bty + S(8), S(34), color)
        tx = btx + S(50)
        avail = btw - S(50) - S(16)
        fs = 28
        while d.textlength("Quét mã để đọc ngay!", font=baloo(S(fs), "Bold")) > avail and fs > 18:
            fs -= 1
        f_b = baloo(S(fs), "Bold")
        lwid = d.textlength("Quét mã để đọc ngay!", font=f_b)
        asc, desc = f_b.getmetrics()
        d.text((tx + (avail - lwid) / 2, bty + (bth - asc - desc) / 2 + S(3)), "Quét mã để đọc ngay!", font=f_b, fill="white")

    # ---- khẩu hiệu cuối ----
    f_s = baloo(S(46), "Bold")
    slogan = "“Đọc hôm nay – Kiến tạo ngày mai!”"
    sw = d.textlength(slogan, font=f_s)
    sy = S(top_y + 2 * ph + gy + 6)
    d.text(((W - sw) / 2, sy), slogan, font=f_s, fill=NAVY)
    star(d, (W - sw) / 2 - S(34), sy + S(36), S(18), SUN)
    star(d, (W + sw) / 2 + S(34), sy + S(36), S(18), SUN)
    return im, urls


def scan_each(im):
    """Đọc từng ô (2x2), mỗi ô có 1 mã."""
    a = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)
    h, w = a.shape[:2]
    out = []
    for k in range(4):
        cx, cy = k % 2, k // 2
        sub = a[cy * h // 2:(cy + 1) * h // 2, cx * w // 2:(cx + 1) * w // 2]
        txt, _, _ = cv2.QRCodeDetector().detectAndDecode(sub)
        out.append(txt)
    return out


def main():
    OUT.mkdir(exist_ok=True)
    paths = {}
    for s, tag in ((1, "fullhd"), (2, "4k")):
        im, urls = render(s)
        p = OUT / f"slide-4-ma-qr-{tag}.png"
        im.save(p, optimize=True)
        paths[tag] = p
        got = scan_each(im)
        assert got == urls, (tag, got)
        print("OK", p.name, im.size)

    # thử như khi chiếu: thu nhỏ còn 1280x720 và làm mờ nhẹ
    im = Image.open(paths["fullhd"]).resize((1280, 720), Image.LANCZOS).filter(ImageFilter.GaussianBlur(1.0))
    print("Giả lập máy chiếu 720p + mờ:", sum(bool(t) for t in scan_each(im)), "/ 4 mã đọc được")

    from pptx import Presentation
    from pptx.util import Emu
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(12192000), Emu(6858000)
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.shapes.add_picture(str(paths["4k"]), 0, 0, prs.slide_width, prs.slide_height)
    pptx = OUT / "slide-4-ma-qr.pptx"
    prs.save(pptx)
    print("OK", pptx.name)


if __name__ == "__main__":
    main()
