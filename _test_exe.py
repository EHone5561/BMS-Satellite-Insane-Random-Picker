# -*- coding: utf-8 -*-
"""
EXE 실제 실행 검증

  <test>\OpenLR2\
      BMS_Crawler.exe                  ← 여기 두고 실행
      BMS_RandomPicker.exe
      LR2files\Database\Score\HANYUU.db

크롤러 exe 가 상대 경로로 DB 를 찾아 CSV 를 Score 폴더에 만드는지 확인한다.
"""
import os
import shutil
import subprocess
import sys

SRC = r"C:\Suzuha\Satellite_Crawler"
DIST = os.path.join(SRC, "dist")
TEST = os.path.join(SRC, "_test_exe")
OPENLR2 = os.path.join(TEST, "OpenLR2")
SCORE = os.path.join(OPENLR2, "LR2files", "Database", "Score")


def setup():
    if os.path.exists(TEST):
        shutil.rmtree(TEST)
    os.makedirs(SCORE, exist_ok=True)

    shutil.copy(os.path.join(SRC, "HANYUU.db"), os.path.join(SCORE, "HANYUU.db"))
    for f in ("BMS_Crawler.exe", "BMS_RandomPicker.exe"):
        shutil.copy(os.path.join(DIST, f), os.path.join(OPENLR2, f))
    # json 캐시도 복사 → 네트워크 없이 빠르게 검증
    for j in ("score.json", "insane_data.json"):
        p = os.path.join(SRC, j)
        if os.path.exists(p):
            shutil.copy(p, os.path.join(OPENLR2, j))
    print("[준비] " + OPENLR2)
    print("[준비] Score 폴더에 HANYUU.db 배치")


def run_crawler():
    print()
    print("=" * 60)
    print(" BMS_Crawler.exe 실행 (cwd=OpenLR2)")
    print("=" * 60)
    r = subprocess.run([os.path.join(OPENLR2, "BMS_Crawler.exe")],
                       cwd=OPENLR2, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=300)
    print(r.stdout)
    if r.returncode != 0:
        print("[STDERR] " + r.stderr[-1500:])
    return r.returncode


def check():
    print("=" * 60)
    print(" 검증")
    print("=" * 60)
    ok = True
    names = ["Satellite_songs.csv", "Insane_songs.csv",
             "All_songs.csv", "Unplayed_songs.csv"]

    # 1) Score 폴더에 CSV 생성
    for n in names:
        p = os.path.join(SCORE, n)
        e = os.path.exists(p)
        rows = ""
        if e:
            with open(p, encoding="utf-8-sig") as f:
                rows = str(sum(1 for _ in f) - 1) + " 행"
        print(("  [O] " if e else "  [X] ") + n + ("  " + rows if e else ""))
        ok &= e

    # 2) exe 옆에 CSV 없어야 함
    for n in names:
        if os.path.exists(os.path.join(OPENLR2, n)):
            print("  [X] exe 옆에 CSV 생성됨: " + n)
            ok = False

    # 3) DB 원본 유지
    e = os.path.exists(os.path.join(SCORE, "HANYUU.db"))
    print(("  [O] " if e else "  [X] ") + "HANYUU.db 원본 유지")
    ok &= e

    # 4) 내용 일치
    print()
    for n in names:
        a = os.path.join(SRC, "_backup", n)
        b = os.path.join(SCORE, n)
        if os.path.exists(a) and os.path.exists(b):
            same = open(a, encoding="utf-8-sig").read() == open(b, encoding="utf-8-sig").read()
            print(("  [O] " if same else "  [X] ") + n + " 내용 일치")
            ok &= same

    print()
    print("=" * 60)
    print(" 결과: " + ("모두 통과" if ok else "실패 있음"))
    print("=" * 60)
    return ok


if __name__ == "__main__":
    setup()
    rc = run_crawler()
    ok = check()
    sys.exit(0 if (ok and rc == 0) else 1)
