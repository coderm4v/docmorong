"""Tạo 4 mã QR thật và ghép vào áp phích (thay 4 mã QR giả do AI vẽ).

Cách chạy: .venv/Scripts/python tools/make_qr.py
Kết quả:
  docs/qr/<chu-de>.png          mã QR rời (in hoặc dán vào slide)
  poster/ap-phich-qr.png        áp phích đã ghép mã QR thật (3072x2048)
"""
from pathlib import Path

import cv2
import numpy as np
import segno
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
BASE_URL = "https://coderm4v.github.io/docmorong/"
SCALE = 2  # phóng áp phích lên 2 lần cho nét khi chiếu

# (chủ đề, khung trắng trên áp phích gốc 1536x1024: x, y, rộng, cao)
SLOTS = [
    ("vu-tru", (508, 248, 220, 213)),
    ("robot-ai", (1268, 242, 218, 211)),
    ("nang-luong", (508, 630, 219, 211)),
    ("suc-khoe", (1268, 630, 218, 211)),
]


def qr_image(url, size):
    qr = segno.make(url, error="m", micro=False)
    n = qr.symbol_size(border=1)[0]
    scale = max(1, size // n)
    from io import BytesIO
    buf = BytesIO()
    qr.save(buf, kind="png", scale=scale, border=1, dark="#000000", light="#ffffff")
    buf.seek(0)
    im = Image.open(buf).convert("RGB")  # cạnh = n*scale (mọi ô đều nhau, không méo)
    canvas = Image.new("RGB", (size, size), "white")
    canvas.paste(im, ((size - im.width) // 2, (size - im.height) // 2))
    return canvas


def decode(im):
    arr = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)
    det = cv2.QRCodeDetector()
    found, texts, _, _ = det.detectAndDecodeMulti(arr)
    return sorted(t for t in texts if t) if found else []


def main():
    qr_dir = ROOT / "docs" / "qr"
    qr_dir.mkdir(parents=True, exist_ok=True)
    poster = Image.open(ROOT / "poster" / "ap-phich-goc.png").convert("RGB")
    poster = poster.resize((poster.width * SCALE, poster.height * SCALE), Image.LANCZOS)
    draw = ImageDraw.Draw(poster)

    urls = []
    for slug, (x, y, w, h) in SLOTS:
        url = f"{BASE_URL}{slug}/"
        urls.append(url)
        # mã rời, cỡ lớn để in
        qr_image(url, 1200).save(qr_dir / f"{slug}.png")
        # phủ trắng khung cũ rồi đặt mã mới vào giữa
        x, y, w, h = (v * SCALE for v in (x, y, w, h))
        pad = 4 * SCALE
        draw.rounded_rectangle((x + pad, y + pad, x + w - pad, y + h - pad), radius=10 * SCALE, fill="white")
        size = min(w, h) - 2 * pad
        q = qr_image(url, size)
        poster.paste(q, (x + (w - size) // 2, y + (h - size) // 2))

    out = ROOT / "poster" / "ap-phich-qr.png"
    poster.save(out, optimize=True)

    # tự kiểm tra: đọc lại từng mã rời và cả áp phích
    for slug, url in zip((s for s, _ in SLOTS), urls):
        got = decode(Image.open(qr_dir / f"{slug}.png"))
        assert got == [url], (slug, got)
    got = decode(poster)
    print("Áp phích đọc được", len(got), "mã:", *got, sep="\n  ")
    small = poster.resize((1280, 853), Image.LANCZOS)  # giả lập chiếu/chụp ở độ phân giải thấp
    print("Bản thu nhỏ 1280px đọc được", len(decode(small)), "mã")


if __name__ == "__main__":
    main()
