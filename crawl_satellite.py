# -*- coding: utf-8 -*-
"""
Satellite (stellabms.xyz) 곡 데이터 크롤러
- score.json 을 받아서 LV(level) 와 TITLE(title) 만 추출 → CSV 저장

실행:  python -E crawl_satellite.py
결과:  Satellite_songs.csv  (컬럼: level, title)

메모: 'Stella' 는 다른 난이도 체계의 용어라 혼선 방지를 위해 전부 'Satellite' 로 통일한다.
      (사이트 도메인 stellabms.xyz 는 고유 주소라 그대로 둔다)
"""
import csv
import json
import os
import time

import requests

# 데이터 출처 (header.json 의 data_url = score.json)
BASE = "https://stellabms.xyz/sl"
SCORE_URL = BASE + "/score.json"

HEADERS = {
    # UA 없으면 Cloudflare 가 막을 수 있어서 브라우저 UA 를 붙인다
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
}

HERE = os.path.dirname(os.path.abspath(__file__))
RAW_PATH = os.path.join(HERE, "score.json")     # 원본 캐시 (재요청 최소화)
CSV_PATH = os.path.join(HERE, "Satellite_songs.csv")


def fetch_score(use_cache=True):
    """score.json 을 받아온다. 이미 받아둔 캐시가 있으면 재사용."""
    if use_cache and os.path.exists(RAW_PATH):
        print("[캐시] 이미 받아둔 score.json 사용: " + RAW_PATH)
        with open(RAW_PATH, encoding="utf-8") as f:
            return json.load(f)

    print("[요청] " + SCORE_URL)
    resp = requests.get(SCORE_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()          # 200 아니면 예외

    with open(RAW_PATH, "w", encoding="utf-8") as f:
        f.write(resp.text)
    print("[저장] 원본 캐시 → " + RAW_PATH)
    return resp.json()


def to_rows(data):
    """LV 와 Title 만 뽑아서 (level, title, md5) 튜플 리스트로 만든다.
    level 은 'sl0' ~ 'sl12' 형태로 sl 접두사를 붙인다.
    md5 는 DB(HANYUU.db)의 hash 와 조인하기 위한 키.
    """
    rows = []
    for song in data:
        raw = str(song.get("level", "")).strip()
        title = str(song.get("title", "")).strip()
        md5 = str(song.get("md5", "")).strip().lower()
        level = ("sl" + raw) if raw != "" else ""
        if level == "" and title == "":
            continue                  # 빈 행 방지
        rows.append((level, title, md5))
    return rows


def save_csv(rows, path):
    # newline="" 은 csv 모듈 권장사항 (Windows 에서 빈 줄 방지)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["level", "title", "md5"])      # 헤더
        writer.writerows(rows)
    print("[저장] CSV → " + path + "  (" + str(len(rows)) + " 행)")


def main():
    t0 = time.time()

    data = fetch_score()
    print("[파싱] 총 " + str(len(data)) + " 곡")

    rows = to_rows(data)
    save_csv(rows, CSV_PATH)

    # 레벨별 개수 요약
    from collections import Counter
    cnt = Counter(level for level, _, _ in rows)
    ordered = sorted(cnt.items(), key=lambda kv: int(kv[0][2:]) if kv[0][2:].isdigit() else 999)
    print("[요약] 레벨별 곡 수")
    for level, n in ordered:
        print("  " + level + " : " + str(n))

    print("[완료] " + format(time.time() - t0, ".1f") + "초")


if __name__ == "__main__":
    main()
