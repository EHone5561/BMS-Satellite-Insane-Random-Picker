# -*- coding: utf-8 -*-
"""
DARKSABUN 発狂BMS難易度表 (insane) 크롤러
- data.json 을 받아서 Level 과 Title 만 추출 → CSV 저장
- 형식은 Satellite 크롤러와 동일: (level, title) 2컬럼
- level 은 '★1' ~ '★25' 형태로 ★ 접두사를 붙인다 (header.json 의 symbol)

실행:  python -E crawl_insane.py
결과:  Insane_songs.csv  (컬럼: level, title)
"""
import csv
import json
import os
import time

import requests

# 데이터 출처
BASE = "https://darksabun.club/table/archive/insane1"
HEADER_URL = BASE + "/header.json"
DATA_URL = BASE + "/data.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
}

HERE = os.path.dirname(os.path.abspath(__file__))
RAW_PATH = os.path.join(HERE, "insane_data.json")      # 원본 캐시
CSV_PATH = os.path.join(HERE, "Insane_songs.csv")

SYMBOL_FALLBACK = "★"     # header.json 을 못 받았을 때 기본값


def fetch_json(url, cache_path=None):
    """JSON 을 받아온다. cache_path 가 있고 파일이 있으면 캐시를 재사용."""
    if cache_path and os.path.exists(cache_path):
        print("[캐시] 이미 받아둔 파일 사용: " + cache_path)
        with open(cache_path, encoding="utf-8") as f:
            return json.load(f)

    print("[요청] " + url)
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    if cache_path:
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(resp.text)
        print("[저장] 원본 캐시 → " + cache_path)
    return resp.json()


def get_symbol():
    """header.json 에서 난이도 기호('★')를 가져온다. 실패하면 기본값."""
    try:
        header = fetch_json(HEADER_URL)          # 헤더는 캐시하지 않고 매번 읽음(가벼움)
        sym = str(header.get("symbol", "")).strip()
        if sym:
            print("[기호] header.json symbol = " + sym)
            return sym
    except Exception as e:
        print("[경고] header.json 실패 → 기본 기호 사용: " + str(e))
    return SYMBOL_FALLBACK


def to_rows(data, symbol):
    """Level 과 Title, md5 를 뽑아서 (level, title, md5) 튜플 리스트로 만든다.
    level 은 '★1' ~ '★25' 형태로 기호 접두사를 붙인다. ('???' 레벨도 '★???')
    md5 는 DB(HANYUU.db)의 hash 와 조인하기 위한 키.
    """
    rows = []
    for song in data:
        raw = str(song.get("level", "")).strip()
        title = str(song.get("title", "")).strip()
        md5 = str(song.get("md5", "")).strip().lower()
        level = (symbol + raw) if raw != "" else ""
        if level == "" and title == "":
            continue
        rows.append((level, title, md5))
    return rows


def save_csv(rows, path):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["level", "title", "md5"])
        writer.writerows(rows)
    print("[저장] CSV → " + path + "  (" + str(len(rows)) + " 행)")


def main():
    t0 = time.time()

    symbol = get_symbol()
    data = fetch_json(DATA_URL, RAW_PATH)
    print("[파싱] 총 " + str(len(data)) + " 곡")

    rows = to_rows(data, symbol)
    save_csv(rows, CSV_PATH)

    # 레벨별 요약 (숫자 레벨 → 오름차순, '???' 는 마지막)
    from collections import Counter
    cnt = Counter(level for level, _, _ in rows)
    def sort_key(item):
        lv = item[0][len(symbol):]           # 기호 떼고 숫자만
        return (1, 0) if lv == "???" else (0, int(lv) if lv.isdigit() else 999)
    print("[요약] 레벨별 곡 수")
    for level, n in sorted(cnt.items(), key=sort_key):
        print("  " + level + " : " + str(n))

    print("[완료] " + format(time.time() - t0, ".1f") + "초")


if __name__ == "__main__":
    main()
