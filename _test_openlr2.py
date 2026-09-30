# -*- coding: utf-8 -*-
"""
OpenLR2 구조 시뮬레이션 테스트

  <test>\OpenLR2\BMS_Crawler.exe       (실제로는 crawl_all.py)
  <test>\OpenLR2\LR2files\Database\Score\HANYUU.db

crawl_all.py 를 OpenLR2 폴더에서 실행했을 때
  - DB 를 상대 경로로 찾는지
  - CSV 를 Score 폴더에 만드는지
  - 기존 CSV 가 있으면 덮어쓰는지
를 검증한다.
"""
import csv
import os
import shutil
import subprocess
import sys

SRC = r"C:\Suzuha\Satellite_Crawler"
TEST = r"C:\Suzuha\Satellite_Crawler\_test_openlr2"

OPENLR2 = os.path.join(TEST, "OpenLR2")
SCORE = os.path.join(OPENLR2, "LR2files", "Database", "Score")


def setup():
    if os.path.exists(TEST):
        shutil.rmtree(TEST)
    os.makedirs(SCORE, exist_ok=True)

    # 실제 HANYUU.db 복사 (친구 파일 대신 내 것을 씀)
    shutil.copy(os.path.join(SRC, "HANYUU.db"), os.path.join(SCORE, "HANYUU.db"))
    # crawl_all.py 를 OpenLR2 폴더로 복사 (exe 대신 스크립트)
    shutil.copy(os.path.join(SRC, "crawl_all.py"), os.path.join(OPENLR2, "crawl_all.py"))
    # json 캐시도 같이 복사 (네트워크 요청 없이 테스트)
    for j in ("score.json", "insane_data.json"):
        p = os.path.join(SRC, j)
        if os.path.exists(p):
            shutil.copy(p, os.path.join(OPENLR2, j))
    print("[준비] " + OPENLR2)
    print("[준비] DB → " + os.path.join(SCORE, "HANYUU.db"))


def run():
    env = dict(os.environ)
    env.pop("PYTHONHOME", None)      # 이 환경의 PYTHONHOME 문제 회피
    r = subprocess.run([sys.executable, "crawl_all.py"],
                       cwd=OPENLR2, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=env)
    print(r.stdout)
    if r.returncode != 0:
        print("[STDERR] " + r.stderr[-2000:])
    return r.returncode


def check():
    print("=" * 60)
    print(" 검증")
    print("=" * 60)
    ok = True

    # 1) CSV 가 Score 폴더에 생겼는지
    names = ["Satellite_songs.csv", "Insane_songs.csv",
             "All_songs.csv", "Unplayed_songs.csv"]
    for n in names:
        p = os.path.join(SCORE, n)
        exists = os.path.exists(p)
        print(("  [O] " if exists else "  [X] ") + n +
              ("  (" + str(sum(1 for _ in open(p, encoding='utf-8-sig')) - 1) + " 행)" if exists else ""))
        ok &= exists

    # 2) exe 폴더에 CSV 가 없어야 함 (오염 방지)
    for n in names:
        p = os.path.join(OPENLR2, n)
        if os.path.exists(p):
            print("  [X] exe 옆에 CSV 가 생김: " + n)
            ok = False

    # 3) HANYUU.db 가 Score 폴더에 그대로 있는지 (읽기만)
    dbf = os.path.join(SCORE, "HANYUU.db")
    print(("  [O] " if os.path.exists(dbf) else "  [X] ") + "HANYUU.db 원본 유지")
    ok &= os.path.exists(dbf)

    # 4) 내용 비교 (원본 CSV 와 동일한지)
    print()
    for n in names:
        a = os.path.join(SRC, "_backup", n)
        b = os.path.join(SCORE, n)
        if os.path.exists(a) and os.path.exists(b):
            same = open(a, encoding="utf-8-sig").read() == open(b, encoding="utf-8-sig").read()
            print(("  [O] " if same else "  [X] ") + n + " 내용 일치 (원본 백업 대비)")
            ok &= same

    # 5) 덮어쓰기 확인: 더미 내용 넣고 재실행
    print()
    target = os.path.join(SCORE, "All_songs.csv")
    with open(target, "w", encoding="utf-8") as f:
        f.write("dummy\n")
    print("[덮어쓰기 테스트] All_songs.csv 에 더미 내용 기록")
    run()
    head = open(target, encoding="utf-8-sig").readline().strip()
    overwritten = head.startswith("level")
    print(("  [O] " if overwritten else "  [X] ") + "덮어쓰기 정상 (헤더: " + head + ")")
    ok &= overwritten

    print()
    print("=" * 60)
    print(" 결과: " + ("모두 통과" if ok else "실패 있음"))
    print("=" * 60)
    return ok


if __name__ == "__main__":
    setup()
    rc = run()
    ok = check()
    sys.exit(0 if (ok and rc == 0) else 1)
