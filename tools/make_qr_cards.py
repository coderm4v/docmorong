"""Tạo ảnh thẻ QR cho 4 chủ đề (mỗi thẻ một file) và 1 tờ gộp cả 4 thẻ.

Cách chạy: .venv/Scripts/python tools/make_qr_cards.py
Kết quả trong thư mục qr-anh/:
  01-vu-tru.png ... 04-suc-khoe.png   thẻ rời 1200x1600 (dán slide, in A5/A6)
  tong-hop-4-ma-qr.png                tờ A4 dọc gộp 4 thẻ 2x2 (2480x3508, 300 dpi)
"""
from io import BytesIO
from pathlib import Path

import cv2
import numpy as np
import segno
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "tools" / "fonts"
OUT = ROOT / "qr-anh"
BASE_URL = "https://coderm4v.github.io/docmorong/"

TOPICS = [
    ("01", "vu-tru", "Khám phá Vũ trụ", "#5b3fd1", "#efeaff", "01-sao-hoa"),
    ("02", "robot-ai", "Rô-bốt và AI", "#16884a", "#e2f5e8", "05-canh-tay-robot"),
    ("03", "nang-luong", "Năng lượng và Môi trường", "#d4520f", "#fff0e4", "10-dien-gio"),
    ("04", "suc-khoe", "Khoa học và Sức khỏe", "#0b7f7a", "#dff4f2", "13-kinh-hien-vi"),
]

W, H = 1200, 1600


def baloo(size, weight="ExtraBold"):
    f = ImageFont.truetype(str(FONTS / "Baloo2.ttf"), size)
    f.set_variation_by_name(weight)
    return f


def vn(size, bold=False):
    name = "BeVietnamPro-SemiBold.ttf" if bold else "BeVietnamPro-Regular.ttf"
    return ImageFont.truetype(str(FONTS / name), size)


def qr_block(url, size):
    qr = segno.make(url, error="m", micro=False)
    n = qr.symbol_size(border=0)[0]
    scale = size // n
    buf = BytesIO()
    qr.save(buf, kind="png", scale=scale, border=0, dark="#111827", light="#ffffff")
    buf.seek(0)
    return Image.open(buf).convert("RGB")


def cover(im, w, h):
    """Cắt ảnh cho vừa khung w x h (giữ tỉ lệ, cắt giữa)."""
    r = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def rounded_mask(w, h, r):
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), radius=r, fill=255)
    return m


def center_text(d, y, text, font, fill, width=W):
    tw = d.textlength(text, font=font)
    d.text(((width - tw) / 2, y), text, font=font, fill=fill)


def card(num, slug, name, color, tint, image):
    url = f"{BASE_URL}{slug}/"
    im = Image.new("RGB", (W, H), color)
    d = ImageDraw.Draw(im)

    # ảnh minh họa phía trên, bo góc dưới
    photo_h = 400
    photo = cover(Image.open(ROOT / "raw" / f"{image}.png").convert("RGB"), W, photo_h)
    im.paste(photo, (0, 0))
    # dải màu mờ dần ở mép dưới ảnh để chữ nổi
    fade = Image.new("RGBA", (W, 200))
    fd = ImageDraw.Draw(fade)
    rgb = tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))
    for k in range(200):
        fd.line([(0, k), (W, k)], fill=rgb + (int(255 * (k / 199) ** 1.6),))
    im.paste(fade, (0, photo_h - 200), fade)

    # dòng tiêu đề trên nền màu, ngay dưới ảnh: [ô số] Tên chủ đề — căn giữa, cỡ chữ tự co cho vừa 1 dòng
    badge = 112
    gap = 28
    size = 96
    while True:
        f_title = baloo(size)
        tw = d.textlength(name, font=f_title)
        if badge + gap + tw <= W - 120 or size <= 56:
            break
        size -= 2
    total = badge + gap + tw
    bx = (W - total) / 2
    by = photo_h + 20
    d.rounded_rectangle((bx, by, bx + badge, by + badge), radius=30, fill="#ffc531")
    f_num = baloo(76)
    nw = d.textlength(num, font=f_num)
    d.text((bx + (badge - nw) / 2, by + 8), num, font=f_num, fill="#1b2140")
    asc, desc = f_title.getmetrics()
    d.text((bx + badge + gap, by + badge / 2 - (asc + desc) / 2 + 6), name, font=f_title, fill="white")

    # khung trắng chứa mã QR
    box = 720
    qx, qy = (W - box) // 2, by + badge + 50
    d.rounded_rectangle((qx + 10, qy + 14, qx + box + 10, qy + box + 14), radius=48, fill=(0, 0, 0))  # bóng
    shadow = im.crop((qx - 20, qy - 20, qx + box + 40, qy + box + 40))
    im.paste(Image.blend(shadow, Image.new("RGB", shadow.size, color), 0.75), (qx - 20, qy - 20))
    d.rounded_rectangle((qx, qy, qx + box, qy + box), radius=48, fill="white")
    q = qr_block(url, box - 120)
    im.paste(q, (qx + (box - q.width) // 2, qy + (box - q.height) // 2))

    # nút "Quét mã để đọc ngay!"
    f_btn = baloo(64, "Bold")
    label = "Quét mã để đọc ngay!"
    lw = d.textlength(label, font=f_btn)
    pw, ph = lw + 120, 112
    px, py = (W - pw) / 2, qy + box + 56
    d.rounded_rectangle((px, py, px + pw, py + ph), radius=ph / 2, fill="#ffc531")
    d.text((px + 60, py + 14), label, font=f_btn, fill="#1b2140")

    # chân thẻ
    center_text(d, H - 92, "Thư viện Đọc mở rộng", vn(40, bold=True), tint)

    # bo góc cả thẻ, nền trong suốt
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.paste(im, (0, 0), rounded_mask(W, H, 64))
    return out, url


def decode_all(im):
    arr = cv2.cvtColor(np.array(im.convert("RGB")), cv2.COLOR_RGB2BGR)
    ok, texts, _, _ = cv2.QRCodeDetector().detectAndDecodeMulti(arr)
    return sorted(t for t in texts if t) if ok else []


def main():
    OUT.mkdir(exist_ok=True)
    cards = []
    for num, slug, name, color, tint, image in TOPICS:
        c, url = card(num, slug, name, color, tint, image)
        path = OUT / f"{num}-{slug}.png"
        c.save(path, optimize=True)
        got = decode_all(c)
        assert got == [url], (slug, got)
        cards.append(c)
        print("OK", path.name, "->", url)

    # tờ A4 dọc 300 dpi (2480x3508), 4 thẻ xếp 2 x 2
    SW, SH = 2480, 3508
    sheet = Image.new("RGB", (SW, SH), "#f2f5fb")
    d = ImageDraw.Draw(sheet)
    center_text(d, 90, "4 Thư viện Đọc mở rộng", baloo(140), "#23307a", SW)
    center_text(d, 270, "Mở camera điện thoại, quét mã của chủ đề em muốn đọc", vn(54), "#4b5274", SW)
    cw, ch = 1020, 1360  # giữ tỉ lệ 3:4 của thẻ
    gx = (SW - 2 * cw) // 3
    top = 400
    gy = 80
    for i, c in enumerate(cards):
        small = c.resize((cw, ch), Image.LANCZOS)
        x = gx + (i % 2) * (cw + gx)
        y = top + (i // 2) * (ch + gy)
        sheet.paste(small, (x, y), small)
    center_text(d, top + 2 * ch + gy + 90, "“Đọc hôm nay – Kiến tạo ngày mai!”", baloo(90, "Bold"), "#4b5274", SW)
    sheet_path = OUT / "tong-hop-4-ma-qr.png"
    sheet.save(sheet_path, dpi=(300, 300), optimize=True)
    print("Tờ gộp đọc được", len(decode_all(sheet)), "mã")


if __name__ == "__main__":
    main()
