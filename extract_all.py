# -*- coding: utf-8 -*-
"""
전체 곡 리스트 생성기 (곡 랜덤 선택기 - 기능 2 재료)

동작:
  Satellite_songs.csv + Insane_songs.csv 를 합쳐 md5 중복을 제거한
  '전체 곡 리스트' CSV 를 만든다. (플레이 여부와 무관하게 모든 곡)

실행:  python -E extract_all.py
결과:  All_songs.csv  (컬럼: level, title, md5)
"""
import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SAT_CSV = os.path.join(HERE, "Satellite_songs.csv")
INS_CSV = os.path.join(HERE, "Insane_songs.csv")
OUT_CSV = os.path.join(HERE, "All_songs.csv")


def read_song_csv(path, source):
    rows = []
    if not os.path.exists(path):
        print("[경고] 파일 없음: " + path)
        return rows
    with open(path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            md5 = (r.get("md5") or "").strip().lower()
            if not md5:
                continue
            rows.append(((r.get("level") or "").strip(),
                         (r.get("title") or "").strip(),
                         md5, source))
    print("[" + source + "] " + str(len(rows)) + " 곡 로드")
    return rows


def merge_unique(*row_lists):
    """md5 기준 중복 제거. 같은 곡이 sl/★ 양쪽에 있으면 처음 것만 남긴다."""
    seen = {}
    order = []
    for rows in row_lists:
        for level, title, md5, source in rows:
            if md5 not in seen:
                seen[md5] = [level, title, source]
                order.append(md5)
            elif not seen[md5][1] and title:
                seen[md5][1] = title
    return [(seen[m][0], seen[m][1], m) for m in order]


def main():
    sat = read_song_csv(SAT_CSV, "sl")
    ins = read_song_csv(INS_CSV, "★")
    merged = merge_unique(sat, ins)
    print("[병합] 총 " + str(len(merged)) + " 곡 (중복 제거 " + str(len(sat) + len(ins) - len(merged)) + ")")

    with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["level", "title", "md5"])
        w.writerows(merged)
    print("[저장] CSV → " + OUT_CSV + "  (" + str(len(merged)) + " 행)")


if __name__ == "__main__":
    main()
