# -*- coding: utf-8 -*-
"""
새 exe 실전 검증 — DB 파일명 자동 인식

  <test>\OpenLR2\
      BMS_Crawler.exe
      BMS_RandomPicker.exe
      LR2files\Database\Score\PLAYER_TAEWON.db   ← HANYUU 아님!

크롤러 exe 가 이 DB 를 자동 인식하는지 확인한다.
"""
import os
import shutil
import sqlite3
import subprocess
import sys

SRC = r"C:\Suzuha\Satellite_Crawler"
DIST = os.path.join(SRC, "dist")
TEST = os.path.join(SRC, "_test_exe2")
OPENLR2 = os.path.join(TEST, "OpenLR2")
SCORE = os.path.join(OPENLR2, "LR2files", "Database", "Score")

DB_NAME = "PLAYER_TAEWON.db"


def setup():
    if os.path.exists(TEST):
        shutil.rmtree(TEST)
    os.makedirs(SCORE, exist_ok=True)

    # DB 를 다른 이름으로 복사 + player 이름 변경
    dst = os.path.join(SCORE, DB_NAME)
    shutil.copy(os.path.join(SRC, "HANYUU.db"), dst)
    conn = sqlite3.connect(dst)
    conn.execute("UPDATE player SET name=?", ("PLAYER_TAEWON",))
    conn.commit()
    conn.close()

    for f in ("BMS_Crawler.exe", "BMS_RandomPicker.exe"):
        shutil.copy(os.path.join(DIST, f), os.path.join(OPENLR2, f))
    for j in ("score.json", "insane_data.json"):
        p = os.path.join(SRC, j)
        if os.path.exists(p):
            shutil.copy(p, os.path.join(OPENLR2, j))
    print("[준비] DB 이름: " + DB_NAME + " (HANYUU 아님)")


def run():
    print()
    print("=" * 62)
    print(" BMS_Crawler.exe 실행")
    print("=" * 62)
    r = subprocess.run([os.path.join(OPENLR2, "BMS_Crawler.exe")],
                       cwd=OPENLR2, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=300)
    out = r.stdout
    # 요약만 출력
    for line in out.splitlines():
        s = line.strip()
        if not s:
            continue
        # 레벨별 곡 수 나열은 생략
        if any(s.startswith(p) for p in ("sl", "★")) and " : " in s:
            continue
        print(line)
    if r.returncode != 0:
        print("[STDERR] " + r.stderr[-1200:])
    return r.returncode


def check():
    print("=" * 62)
    print(" 검증")
    print("=" * 62)
    ok = True
    names = ["Satellite_songs.csv", "Insane_songs.csv",
             "All_songs.csv", "Unplayed_songs.csv"]
    for n in names:
        p = os.path.join(SCORE, n)
        e = os.path.exists(p)
        print(("  [O] " if e else "  [X] ") + n +
              ("  " + str(sum(1 for _ in open(p, encoding="utf-8-sig")) - 1) + " 행" if e else ""))
        ok &= e

    # 원본 DB 유지
    e = os.path.exists(os.path.join(SCORE, DB_NAME))
    print(("  [O] " if e else "  [X] ") + DB_NAME + " 원본 유지")
    ok &= e

    # 내용 일치
    print()
    for n in names:
        a = os.path.join(SRC, "_backup", n)
        b = os.path.join(SCORE, n)
        if os.path.exists(a) and os.path.exists(b):
            same = open(a, encoding="utf-8-sig").read() == open(b, encoding="utf-8-sig").read()
            print(("  [O] " if same else "  [X] ") + n + " 내용 일치")
            ok &= same

    print()
    print("=" * 62)
    print(" 결과: " + ("모두 통과" if ok else "실패 있음"))
    print("=" * 62)
    return ok


if __name__ == "__main__":
    setup()
    rc = run()
    ok = check()
    sys.exit(0 if (ok and rc == 0) else 1)
