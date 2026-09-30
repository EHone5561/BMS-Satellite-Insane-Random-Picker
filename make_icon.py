# -*- coding: utf-8 -*-
"""
노란 별 아이콘 생성기 (BMS 크롤러 exe 용)
- 다크 배경 + 노란 별(★) 을 그려서 .ico 로 저장
- 여러 해상도(16~256)를 한 파일에 담는다 (Windows exe 아이콘 규격)
"""
import os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_ICO = os.path.join(HERE, "star_yellow.ico")
OUT_PNG = os.path.join(HERE, "star_yellow.png")

BG = (23, 26, 36, 255)        # 짙은 남색 (앱 다크 테마 surface #171A24)
STAR = (255, 210, 74, 255)    # 노란 별 (#FFD24A, 다크모드 hint 색)
STAR_EDGE = (255, 232, 150, 255)

# 별 꼭짓점 비율 (5각별) — 바깥/안쪽 반지름
import math


def star_points(cx, cy, r_out, r_in, points=5, rot=-math.pi / 2):
    pts = []
    for i in range(points * 2):
        r = r_out if i % 2 == 0 else r_in
        a = rot + i * math.pi / points
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def make(size, rounding=True):
    # 4배 슈퍼샘플링 후 축소 → 계단 현상 제거
    S = size * 4
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # 배경 (둥근 사각형)
    pad = int(S * 0.02)
    radius = int(S * 0.22)
    d.rounded_rectangle([pad, pad, S - pad, S - pad], radius=radius, fill=BG)
    # 테두리 살짝
    d.rounded_rectangle([pad, pad, S - pad, S - pad], radius=radius,
                        outline=(60, 66, 84, 255), width=max(1, S // 128))

    # 별
    cx = cy = S / 2
    r_out = S * 0.36
    r_in = r_out * 0.42
    pts = star_points(cx, cy, r_out, r_in)
    d.polygon(pts, fill=STAR, outline=STAR_EDGE)

    return img.resize((size, size), Image.LANCZOS)


def main():
    sizes = [16, 24, 32, 48, 64, 128, 256]
    # 대표 이미지(256)로 PNG 저장
    big = make(256)
    big.save(OUT_PNG)
    # ICO: 여러 해상도 담기
    imgs = [make(s) for s in sizes]
    imgs[0].save(OUT_ICO, format="ICO",
                 sizes=[(s, s) for s in sizes], append_images=imgs[1:])
    print("[저장] " + OUT_ICO)
    print("[저장] " + OUT_PNG)
    print("[해상도] " + ", ".join(str(s) for s in sizes))


if __name__ == "__main__":
    main()
