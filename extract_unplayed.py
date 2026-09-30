# -*- coding: utf-8 -*-
"""
미플레이 곡 추출기 (곡 랜덤 선택기 - 기능 1 재료)

동작:
  1) Satellite_songs.csv + Insane_songs.csv 를 읽어 하나로 합친다
     - md5 기준으로 중복 제거 (sl 과 ★ 양쪽에 있는 곡은 1개만 남김)
  2) HANYUU.db 의 score 테이블에서 플레이한 곡 hash 를 읽는다
     - clear=0 (Failed) 도 '플레이한 곡'으로 간주 → 제외 대상
  3) 전체 곡 중 플레이 기록이 없는 곡만 뽑아 CSV 로 저장

실행:  python -E extract_unplayed.py
결과:  Unplayed_songs.csv  (컬럼: level, title, md5)

메모:
  - HANYUU.db 에는 곡 이름/난이도표 정보가 없다. 해시(md5)만 있으므로
    난이도표 판단과 곡 정보는 반드시 크롤러 CSV 와 조인해야 한다.
  - 곡 이름(title)이 두 표에서 미묘하게 다를 수 있으므로(공백 등),
    중복 판정은 title 이 아니라 md5 로만 한다.
"""
import csv
import os
import sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))

SAT_CSV = os.path.join(HERE, "Satellite_songs.csv")
INS_CSV = os.path.join(HERE, "Insane_songs.csv")
DB_PATH = os.path.join(HERE, "HANYUU.db")
OUT_CSV = os.path.join(HERE, "Unplayed_songs.csv")


def read_song_csv(path, source):
    """크롤러 CSV 를 읽어 (level, title, md5, source) 리스트로 만든다."""
    rows = []
    if not os.path.exists(path):
        print("[경고] 파일 없음: " + path)
        return rows
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            md5 = (r.get("md5") or "").strip().lower()
            if not md5:
                continue                      # md5 없으면 조인 불가 → 제외
            rows.append((
                (r.get("level") or "").strip(),
                (r.get("title") or "").strip(),
                md5,
                source,
            ))
    print("[" + source + "] " + str(len(rows)) + " 곡 로드")
    return rows


def merge_unique(*row_lists):
    """여러 (level, title, md5, source) 리스트를 md5 기준으로 합친다.
    같은 md5 가 여러 표에 있으면 처음 만난 것만 남기고,
    source 는 'sl+★' 처럼 합쳐서 표시한다.
    """
    seen = {}          # md5 -> [level, title, source_set]
    order = []         # md5 처음 등장 순서 유지
    for rows in row_lists:
        for level, title, md5, source in rows:
            if md5 not in seen:
                seen[md5] = [level, title, {source}]
                order.append(md5)
            else:
                seen[md5][2].add(source)
                # 제목이 비어있었다면 채워준다
                if not seen[md5][1] and title:
                    seen[md5][1] = title

    merged = []
    dup = 0
    for md5 in order:
        level, title, sources = seen[md5]
        if len(sources) > 1:
            dup += 1
        merged.append((level, title, md5, "+".join(sorted(sources))))
    return merged, dup


def read_played_hashes(db_path):
    """HANYUU.db 의 score 테이블에서 플레이한 곡 해시 집합을 읽는다.
    clear=0(Failed) 도 '플레이 기록'으로 포함한다.
    """
    if not os.path.exists(db_path):
        raise SystemExit("DB 를 찾을 수 없습니다: " + db_path)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT hash, clear FROM score")
    played = {h.strip().lower() for h, _ in cur.fetchall()}
    conn.close()
    print("[DB] 플레이 기록 " + str(len(played)) + " 곡 (clear=0 포함)")
    return played


def save_csv(rows, path, header):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    print("[저장] CSV → " + path + "  (" + str(len(rows)) + " 행)")


def main():
    # 1) 두 난이도표 합치기 (md5 중복 제거)
    sat = read_song_csv(SAT_CSV, "sl")
    ins = read_song_csv(INS_CSV, "★")
    merged, dup = merge_unique(sat, ins)
    print("[병합] 총 " + str(len(merged)) + " 곡 (중복 제거 " + str(dup) + " 곡)")

    # 2) 플레이한 곡 hash
    played = read_played_hashes(DB_PATH)

    # 3) 플레이 기록 없는 곡만 추출
    unplayed = [(level, title, md5) for level, title, md5, _ in merged if md5 not in played]
    played_in_pool = len(merged) - len(unplayed)

    print()
    print("=== 결과 ===")
    print("  전체 곡 풀 (sl+★) : " + str(len(merged)))
    print("  이미 플레이한 곡   : " + str(played_in_pool))
    print("  플레이 안 한 곡    : " + str(len(unplayed)))
    print()

    save_csv(unplayed, OUT_CSV, ["level", "title", "md5"])

    # 레벨별 요약 (sl / ★ 를 나눠서 보여준다)
    from collections import Counter
    sl_cnt = Counter(lv for lv, _, _ in unplayed if lv.startswith("sl"))
    st_cnt = Counter(lv for lv, _, _ in unplayed if lv.startswith("★"))
    def key(lv, sym):
        tail = lv[len(sym):]
        return (1, 0) if tail == "???" else (0, int(tail) if tail.isdigit() else 999)
    print("[요약 - Satellite(sl)]")
    for lv, n in sorted(sl_cnt.items(), key=lambda kv: key(kv[0], "sl")):
        print("  " + lv + " : " + str(n))
    print("[요약 - Insane(★)]")
    for lv, n in sorted(st_cnt.items(), key=lambda kv: key(kv[0], "★")):
        print("  " + lv + " : " + str(n))


if __name__ == "__main__":
    main()
