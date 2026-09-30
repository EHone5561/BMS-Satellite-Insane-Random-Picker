# -*- coding: utf-8 -*-
"""
DB 자동 인식 테스트 — 파일명 하드코딩 제거 검증

시나리오:
  1) 플레이어 이름이 HANYUU 가 아닌 DB (TAE1WON.db) → 인식되는가
  2) .db 가 여러 개일 때 (진짜 LR2 DB + 가짜 DB) → 진짜를 고르는가
  3) LR2 DB 가 아닌 .db 만 있을 때 → 걸러내는가
  4) --db 로 직접 지정 → 그걸 쓰는가
  5) --list-db → 목록을 보여주는가
"""
import os
import shutil
import sqlite3
import subprocess
import sys

SRC = r"C:\Suzuha\Satellite_Crawler"
TEST = os.path.join(SRC, "_test_dbname")
OPENLR2 = os.path.join(TEST, "OpenLR2")
SCORE = os.path.join(OPENLR2, "LR2files", "Database", "Score")

SRC_DB = os.path.join(SRC, "HANYUU.db")


def clean():
    if os.path.exists(TEST):
        shutil.rmtree(TEST)
    os.makedirs(SCORE, exist_ok=True)
    shutil.copy(os.path.join(SRC, "crawl_all.py"), os.path.join(OPENLR2, "crawl_all.py"))
    for j in ("score.json", "insane_data.json"):
        p = os.path.join(SRC, j)
        if os.path.exists(p):
            shutil.copy(p, os.path.join(OPENLR2, j))


def make_db_as(path, player):
    """SRC_DB 를 복사하고 player.name 을 바꾼 DB 를 만든다."""
    shutil.copy(SRC_DB, path)
    conn = sqlite3.connect(path)
    conn.execute("UPDATE player SET name=?", (player,))
    conn.commit()
    conn.close()


def make_fake_db(path):
    """LR2 DB 가 아닌 가짜 .db (score/player 테이블 없음)."""
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE something (x INT)")
    conn.commit()
    conn.close()


def run(args=None, list_only=False):
    env = dict(os.environ)
    env.pop("PYTHONHOME", None)
    cmd = [sys.executable, "crawl_all.py"] + (args or [])
    r = subprocess.run(cmd, cwd=OPENLR2, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=env, timeout=180)
    return r.stdout + ("\n[STDERR]\n" + r.stderr[-800:] if r.returncode else "")


def banner(t):
    print()
    print("=" * 62)
    print(" " + t)
    print("=" * 62)


def main():
    ok = True

    # ── 시나리오 1: HANYUU 가 아닌 이름 ──
    banner("1) 플레이어 이름이 다른 DB (TAE1WON.db)")
    clean()
    make_db_as(os.path.join(SCORE, "TAE1WON.db"), "TAE1WON")
    out = run()
    s1 = "플레이어 : TAE1WON" in out
    s2 = os.path.exists(os.path.join(SCORE, "Unplayed_songs.csv"))
    print("  [%s] TAE1WON.db 자동 인식" % ("O" if s1 else "X"))
    print("  [%s] CSV 생성됨" % ("O" if s2 else "X"))
    for line in out.splitlines():
        if any(k in line for k in ("DB 발견", "플레이어", "CSV 출력", "미플레이 ")):
            print("      " + line.strip())
    ok &= s1 and s2

    # ── 시나리오 2: 여러 DB (진짜 2개 + 가짜 1개) ──
    banner("2) .db 여러 개 (TAE1WON 30곡 / SUZUHA 204곡 / fake.db)")
    clean()
    # 기록 적은 DB (score 30행만 남김)
    p_small = os.path.join(SCORE, "TAE1WON.db")
    make_db_as(p_small, "TAE1WON")
    c = sqlite3.connect(p_small)
    c.execute("DELETE FROM score WHERE rowid NOT IN (SELECT rowid FROM score LIMIT 30)")
    c.commit()
    c.close()
    # 기록 많은 DB
    make_db_as(os.path.join(SCORE, "SUZUHA.db"), "SUZUHA")
    # 가짜 DB
    make_fake_db(os.path.join(SCORE, "fake.db"))

    out = run()
    s1 = "SUZUHA.db" in out and "← 사용" in out
    s2 = "TAE1WON.db" in out
    print("  [%s] 기록 많은 SUZUHA.db 선택" % ("O" if s1 else "X"))
    print("  [%s] TAE1WON.db 도 목록에 표시 (후순위)" % ("O" if s2 else "X"))
    print("  [%s] 가짜 fake.db 걸러짐" % ("O" if "fake.db" not in out else "X"))
    for line in out.splitlines():
        if any(k in line for k in ("알림", "사용", "곡)")):
            print("      " + line.strip())
    ok &= s1 and ("fake.db" not in out)

    # ── 시나리오 3: LR2 DB 가 아닌 것만 ──
    banner("3) LR2 DB 가 아닌 .db 만 있을 때")
    clean()
    make_fake_db(os.path.join(SCORE, "onlyfake.db"))
    out = run()
    s1 = "LR2 스코어 DB 가 아닙니다" in out
    print("  [%s] 가짜 DB 걸러내고 경고" % ("O" if s1 else "X"))
    for line in out.splitlines():
        if any(k in line for k in ("경고", "DB ", "실행 위치")):
            print("      " + line.strip())
    ok &= s1

    # ── 시나리오 4: --list-db ──
    banner("4) --list-db 옵션")
    clean()
    make_db_as(os.path.join(SCORE, "HANYUU.db"), "HANYUU")
    make_db_as(os.path.join(SCORE, "TAE1WON.db"), "TAE1WON")
    make_fake_db(os.path.join(SCORE, "fake.db"))
    out = run(["--list-db"])
    s1 = "발견한 LR2 DB" in out and "[O]" in out and "[X]" in out
    print("  [%s] 목록 표시 (진짜 2 + 가짜 1)" % ("O" if s1 else "X"))
    for line in out.splitlines():
        print("      " + line.rstrip())
    ok &= s1

    # ── 시나리오 5: --db 직접 지정 ──
    banner("5) --db 직접 지정")
    p = os.path.join(SCORE, "SUZUHA.db")
    out = run(["--db", p])
    s1 = "SUZUHA" in out
    print("  [%s] 지정한 DB 사용" % ("O" if s1 else "X"))
    for line in out.splitlines():
        if any(k in line for k in ("DB 발견", "플레이어")):
            print("      " + line.strip())
    ok &= s1

    # ── 결과 ──
    banner("결과: " + ("모두 통과" if ok else "실패 있음"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
