# -*- coding: utf-8 -*-
"""
BMS 곡 데이터 크롤러 (통합)  ·  Satellite(sl) + Insane(★)

한 번 실행으로 아래를 전부 처리한다.

  1) stellabms.xyz  에서 Satellite(sl) 난이도표 크롤링   → Satellite_songs.csv
  2) darksabun.club 에서 Insane(★)  난이도표 크롤링   → Insane_songs.csv
  3) 두 표를 md5 기준으로 병합(중복 제거)              → All_songs.csv
  4) <플레이어명>.db 와 대조해 미플레이 곡 추출(Failed 포함) → Unplayed_songs.csv

출력 CSV 형식: level,title,md5   (utf-8-sig, 엑셀 호환)

실행:
  python crawl_all.py                 # 캐시 있으면 재사용
  python crawl_all.py --refresh       # 강제 재다운로드
  python crawl_all.py --db <경로>     # DB 경로 직접 지정
  python crawl_all.py --list-db       # 발견한 DB 목록만 보기

메모:
  - 플레이 기록 DB 는 파일명을 가정하지 않는다. LR2 는 <플레이어명>.db 를 만들므로
    Score 폴더의 *.db 를 스캔해 score/player 테이블이 있는 것을 고른다.
    여러 개면 플레이 기록이 가장 많은 DB 를 쓴다. (바꾸려면 --db)
  - DB 에는 곡 이름/난이도표 정보가 없다. 해시(md5)만 있으므로
    난이도표 판단과 곡 정보는 반드시 크롤러 CSV 와 조인해야 한다.
  - 같은 곡이 sl/★ 양쪽에 있으면 md5 로 중복 판정한다. (제목 공백 차이 무시)
  - clear=0(Failed) 도 '플레이한 곡'으로 간주해 미플레이에서 제외한다.
  - 'Stella' 는 다른 난이도 체계 용어라 전부 'Satellite' 로 통일.
"""
import argparse
import csv
import json
import os
import sqlite3
import sys
import time

import requests

# ----------------------------------------------------------------------------
# 경로
# ----------------------------------------------------------------------------
def app_dir():
    """스크립트/exe 옆 폴더 (PyInstaller onefile 대응)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


HERE = app_dir()

# CSV 출력 위치는 'DB 를 찾은 폴더' 로 결정된다 (아래 resolve_output_dir 참고).
# 실제 전역 변수는 main() 에서 채워진다.
SAT_CSV = None
INS_CSV = None
ALL_CSV = None
UNP_CSV = None

# 원본 json 캐시는 exe 옆에 둔다 (CSV 출력 폴더를 더럽히지 않기 위해)
SAT_RAW = os.path.join(HERE, "score.json")
INS_RAW = os.path.join(HERE, "insane_data.json")

# ── DB 탐색 규칙 (경로/파일명 하드코딩 없이 exe 위치 기준 상대 탐색) ──
#  LR2 는 플레이어 이름을 따라 <플레이어명>.db 를 만든다.
#  (예: HANYUU.db, TAE1WON.db, player.db ...)
#  그래서 특정 이름을 박지 않고 Score 폴더의 *.db 를 전부 찾아 쓴다.
#  1) exe 폴더 기준 상대 후보를 먼저 본다
#  2) 없으면 exe 폴더 아래를 재귀 탐색한다
#  → OpenLR2 폴더를 어디에 두든(다른 드라이브여도) 찾아간다.
DB_GLOB = "*.db"

# LR2 DB 로 인정하려면 이 테이블들이 있어야 한다 (오탐 방지: 다른 프로그램의 .db 걸러냄)
DB_REQUIRED_TABLES = ("score", "player")

# 상대 후보: (기준폴더, 하위경로)
DB_RELATIVE_CANDIDATES = [
    "",                                                    # exe 옆
    os.path.join("LR2files", "Database", "Score"),         # OpenLR2 표준
    os.path.join("..", "LR2files", "Database", "Score"),
    os.path.join("..", "..", "LR2files", "Database", "Score"),
    os.path.join(".."),
]

# 재귀 탐색 시 무시할 폴더 (속도/오탐 방지)
DB_SKIP_DIRS = {"_build", "build", ".git", "__pycache__", "node_modules"}

# ----------------------------------------------------------------------------
# 데이터 출처
# ----------------------------------------------------------------------------
SAT_BASE = "https://stellabms.xyz/sl"
SAT_URL = SAT_BASE + "/score.json"

INS_BASE = "https://darksabun.club/table/archive/insane1"
INS_HEADER_URL = INS_BASE + "/header.json"
INS_DATA_URL = INS_BASE + "/data.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
}

SYMBOL_FALLBACK = "★"


def log(msg):
    print(msg, flush=True)


def step(n, total, title):
    log("")
    log("[" + str(n) + "/" + str(total) + "] " + title)
    log("-" * 56)


# ----------------------------------------------------------------------------
# 공통 유틸
# ----------------------------------------------------------------------------
def fetch_json(url, cache_path=None, refresh=False):
    """JSON 다운로드. cache_path 파일이 있고 refresh=False 면 캐시 재사용."""
    if cache_path and not refresh and os.path.exists(cache_path):
        log("  (캐시 사용) " + os.path.basename(cache_path))
        with open(cache_path, encoding="utf-8") as f:
            return json.load(f)

    log("  (요청) " + url)
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    if cache_path:
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(resp.text)
        log("  (저장) " + os.path.basename(cache_path))
    return resp.json()


def save_csv(rows, path):
    """CSV 저장. 같은 이름이 있으면 덮어쓴다."""
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)
    existed = os.path.exists(path)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["level", "title", "md5"])
        w.writerows(rows)
    log("  (저장) " + os.path.basename(path) + "  " + str(len(rows)) + " 행"
        + ("  [덮어쓰기]" if existed else ""))


def level_key(level, symbol):
    """레벨 정렬 키: 숫자는 오름차순, '???' 는 마지막."""
    tail = level[len(symbol):]
    if tail == "???":
        return (1, 0)
    return (0, int(tail) if tail.isdigit() else 999)


def print_level_summary(rows, symbol, indent="    "):
    from collections import Counter
    cnt = Counter(lv for lv, _, _ in rows)
    for lv, n in sorted(cnt.items(), key=lambda kv: level_key(kv[0], symbol)):
        log(indent + lv + " : " + str(n))


# ----------------------------------------------------------------------------
# 1) Satellite (sl)
# ----------------------------------------------------------------------------
def crawl_satellite(refresh=False):
    step(1, 4, "Satellite (sl) 크롤링 — stellabms.xyz")
    data = fetch_json(SAT_URL, SAT_RAW, refresh)
    if not isinstance(data, list):
        # score.json 이 dict 로 감싸진 경우 대비
        data = data.get("data", data.get("songs", []))
    log("  총 " + str(len(data)) + " 곡 수신")

    rows = []
    for song in data:
        raw = str(song.get("level", "")).strip()
        title = str(song.get("title", "")).strip()
        md5 = str(song.get("md5", "")).strip().lower()
        level = ("sl" + raw) if raw else ""
        if not level and not title:
            continue
        rows.append((level, title, md5))

    save_csv(rows, SAT_CSV)
    print_level_summary(rows, "sl")
    return rows


# ----------------------------------------------------------------------------
# 2) Insane (★)
# ----------------------------------------------------------------------------
def get_symbol(refresh=False):
    try:
        header = fetch_json(INS_HEADER_URL, None, refresh)
        sym = str(header.get("symbol", "")).strip()
        if sym:
            log("  난이도 기호: " + sym)
            return sym
    except Exception as e:
        log("  (경고) header.json 실패 → 기본 기호 '" + SYMBOL_FALLBACK + "' 사용")
    return SYMBOL_FALLBACK


def crawl_insane(refresh=False):
    step(2, 4, "Insane (★) 크롤링 — darksabun.club")
    symbol = get_symbol(refresh)
    data = fetch_json(INS_DATA_URL, INS_RAW, refresh)
    if not isinstance(data, list):
        data = data.get("data", data.get("songs", []))
    log("  총 " + str(len(data)) + " 곡 수신")

    rows = []
    for song in data:
        raw = str(song.get("level", "")).strip()
        title = str(song.get("title", "")).strip()
        md5 = str(song.get("md5", "")).strip().lower()
        level = (symbol + raw) if raw else ""
        if not level and not title:
            continue
        rows.append((level, title, md5))

    save_csv(rows, INS_CSV)
    print_level_summary(rows, symbol)
    return rows, symbol


# ----------------------------------------------------------------------------
# 3) 병합 (All)
# ----------------------------------------------------------------------------
def read_csv(path, source):
    rows = []
    if not os.path.exists(path):
        log("  (경고) 파일 없음: " + os.path.basename(path))
        return rows
    with open(path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            md5 = (r.get("md5") or "").strip().lower()
            if not md5:
                continue
            rows.append(((r.get("level") or "").strip(),
                         (r.get("title") or "").strip(),
                         md5, source))
    return rows


def merge_unique(*row_lists):
    """md5 기준 중복 제거. 같은 곡이 sl/★ 양쪽이면 처음 것만 남김."""
    seen = {}
    order = []
    for rows in row_lists:
        for level, title, md5, source in rows:
            if md5 not in seen:
                seen[md5] = [level, title, source]
                order.append(md5)
            elif not seen[md5][1] and title:
                seen[md5][1] = title
    merged = [(seen[m][0], seen[m][1], m) for m in order]
    return merged


def build_all():
    step(3, 4, "전체 곡 리스트 병합 (sl + ★, md5 중복 제거)")
    sat = read_csv(SAT_CSV, "sl")
    ins = read_csv(INS_CSV, "★")
    log("  sl " + str(len(sat)) + "곡 + ★ " + str(len(ins)) + "곡")
    merged = merge_unique(sat, ins)
    dup = len(sat) + len(ins) - len(merged)
    log("  병합 결과 " + str(len(merged)) + "곡 (중복 제거 " + str(dup) + "곡)")
    save_csv(merged, ALL_CSV)
    return merged


# ----------------------------------------------------------------------------
# 4) 미플레이 추출
# ----------------------------------------------------------------------------
def is_lr2_db(path):
    """LR2 스코어 DB 인지 확인한다. (score/player 테이블 존재 여부)

    같은 폴더에 다른 프로그램의 .db 가 있어도 걸러내기 위한 검증.
    """
    try:
        conn = sqlite3.connect(path)
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")
            tables = {str(r[0]).lower() for r in cur.fetchall()}
        finally:
            conn.close()
        return all(t in tables for t in DB_REQUIRED_TABLES)
    except Exception:
        return False


def player_name(db_path):
    """DB 의 player 테이블에서 플레이어 이름을 읽는다. 실패하면 파일명."""
    try:
        conn = sqlite3.connect(db_path)
        try:
            row = conn.execute("SELECT name FROM player LIMIT 1").fetchone()
        finally:
            conn.close()
        if row and row[0]:
            return str(row[0]).strip()
    except Exception:
        pass
    return os.path.splitext(os.path.basename(db_path))[0]


def _scan_candidates():
    """후보 .db 경로를 찾는다 (중복 제거).

    순서: exe 옆 → 상대 후보 폴더들 → 하위 재귀 탐색.
    """
    found = []
    seen = set()

    def add(p):
        ap = os.path.abspath(p)
        if ap not in seen:
            seen.add(ap)
            found.append(ap)

    # 1) exe 옆 + 상대 후보 폴더들
    for rel in DB_RELATIVE_CANDIDATES:
        d = os.path.normpath(os.path.join(HERE, rel))
        if not os.path.isdir(d):
            continue
        try:
            for fn in os.listdir(d):
                if fn.lower().endswith(".db"):
                    add(os.path.join(d, fn))
        except OSError:
            pass

    # 2) 하위 재귀 탐색 (아직 못 찾았을 때만 — 느리므로)
    if not found:
        log("  (탐색) exe 폴더 하위에서 .db 를 찾는 중...")
        for root, dirs, files in os.walk(HERE):
            dirs[:] = [d for d in dirs if d not in DB_SKIP_DIRS]
            for fn in files:
                if fn.lower().endswith(".db"):
                    add(os.path.join(root, fn))
    return found


def find_db(explicit=None):
    """플레이 기록 DB 를 찾는다. 파일명을 하드코딩하지 않는다.

    순서:
      0) --db 로 직접 지정한 경로
      1) exe 기준 상대 후보 폴더의 *.db
      2) exe 하위 재귀 탐색의 *.db
    여러 개면 LR2 DB(score+player 테이블)만 남기고,
    그래도 여러 개면 첫 번째를 쓰고 목록을 보여준다.
    못 찾으면 None.
    """
    if explicit:
        if not os.path.exists(explicit):
            raise SystemExit("지정한 DB 를 찾을 수 없습니다: " + explicit)
        if not is_lr2_db(explicit):
            log("  (경고) LR2 DB 로 보이지 않습니다 (score/player 테이블 없음)")
            log("         그래도 지정하신 파일을 사용합니다: "
                + os.path.basename(explicit))
        return os.path.abspath(explicit)

    cands = _scan_candidates()
    if not cands:
        return None

    # LR2 DB 만 남긴다
    valid = [p for p in cands if is_lr2_db(p)]
    if not valid:
        log("  (경고) .db 를 찾았지만 LR2 스코어 DB 가 아닙니다:")
        for p in cands:
            log("         - " + os.path.basename(p))
        return None

    if len(valid) == 1:
        return valid[0]

    # 여러 개 → 플레이 기록(score 행)이 가장 많은 것을 고른다
    def score_rows(p):
        try:
            conn = sqlite3.connect(p)
            try:
                return conn.execute("SELECT COUNT(*) FROM score").fetchone()[0]
            finally:
                conn.close()
        except Exception:
            return -1

    ranked = sorted(valid, key=score_rows, reverse=True)
    log("  (알림) LR2 DB 가 여러 개 있습니다. 기록이 가장 많은 것을 사용합니다:")
    for p in ranked:
        mark = "  ← 사용" if p == ranked[0] else ""
        log("         %s  (%s, %d곡)%s" % (os.path.basename(p),
                                          player_name(p), score_rows(p), mark))
    log("         다른 DB 를 쓰려면:  --db \"<경로>\"")
    return ranked[0]


def resolve_output_dir(db_path):
    """CSV 를 만들 폴더를 정한다.

    DB 를 찾았으면 그 폴더(= OpenLR2 의 Score 폴더)에 CSV 를 만든다.
    못 찾았으면 exe 옆에 만든다.
    """
    if db_path:
        return os.path.dirname(db_path)
    return HERE


def set_output_paths(out_dir):
    """CSV 출력 경로 전역 변수를 채운다. (있으면 덮어쓰기)"""
    global SAT_CSV, INS_CSV, ALL_CSV, UNP_CSV
    SAT_CSV = os.path.join(out_dir, "Satellite_songs.csv")
    INS_CSV = os.path.join(out_dir, "Insane_songs.csv")
    ALL_CSV = os.path.join(out_dir, "All_songs.csv")
    UNP_CSV = os.path.join(out_dir, "Unplayed_songs.csv")


def read_played_hashes(db_path):
    """score 테이블의 곡 hash 집합. clear=0(Failed) 도 포함."""
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT hash FROM score")
        played = {str(h).strip().lower() for (h,) in cur.fetchall()}
    finally:
        conn.close()
    log("  플레이 기록 " + str(len(played)) + "곡 (Failed 포함)")
    return played


def extract_unplayed(merged, db_path):
    step(4, 4, "미플레이 곡 추출 (플레이 기록 DB 대조)")
    if not db_path:
        log("  (경고) 플레이 기록 DB 를 찾지 못해 미플레이 추출을 건너뜁니다.")
        log("         --db <경로> 로 직접 지정할 수 있습니다.")
        return []

    log("  DB: " + db_path)
    log("  플레이어: " + player_name(db_path))
    played = read_played_hashes(db_path)
    unplayed = [(lv, t, m) for lv, t, m in merged if m not in played]
    played_in_pool = len(merged) - len(unplayed)

    log("  전체 풀      : " + str(len(merged)) + "곡")
    log("  이미 플레이  : " + str(played_in_pool) + "곡")
    log("  미플레이     : " + str(len(unplayed)) + "곡")
    save_csv(unplayed, UNP_CSV)

    sl_cnt = [r for r in unplayed if r[0].startswith("sl")]
    st_cnt = [r for r in unplayed if r[0].startswith("★")]
    log("  [Satellite(sl) 미플레이]")
    print_level_summary(sl_cnt, "sl")
    log("  [Insane(★) 미플레이]")
    print_level_summary(st_cnt, "★")
    return unplayed


# ----------------------------------------------------------------------------
# main
# ----------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(
        description="BMS 곡 데이터 크롤러 (Satellite sl + Insane ★ → CSV 4종)")
    ap.add_argument("--refresh", action="store_true",
                    help="캐시 무시하고 사이트에서 새로 받기")
    ap.add_argument("--db", default=None,
                    help="플레이 기록 DB 경로 직접 지정 (기본: 자동 탐색)")
    ap.add_argument("--list-db", action="store_true",
                    help="발견한 DB 목록만 보여주고 종료")
    args = ap.parse_args()

    # DB 목록만 보고 싶을 때
    if args.list_db:
        log("발견한 LR2 DB:")
        cands = _scan_candidates()
        if not cands:
            log("  (없음) 실행 위치: " + HERE)
        for p in cands:
            ok = is_lr2_db(p)
            info = ""
            if ok:
                try:
                    conn = sqlite3.connect(p)
                    try:
                        n = conn.execute("SELECT COUNT(*) FROM score").fetchone()[0]
                    finally:
                        conn.close()
                    info = "  (%s, %d곡)" % (player_name(p), n)
                except Exception:
                    pass
            log("  [%s] %s%s" % ("O" if ok else "X", p, info))
        return 0

    t0 = time.time()

    # ── 0) DB 를 먼저 찾아서 CSV 출력 폴더를 결정한다 ──
    #    OpenLR2 구조면: <LR2>\LR2files\Database\Score\<플레이어명>.db
    #    → CSV 도 그 Score 폴더 안에 만든다 (있으면 덮어쓰기)
    db_path = find_db(args.db)
    out_dir = resolve_output_dir(db_path)
    set_output_paths(out_dir)

    log("=" * 56)
    log(" BMS 곡 데이터 크롤러")
    log(" 실행 위치: " + HERE)
    if db_path:
        log(" DB 발견  : " + db_path)
        log(" 플레이어 : " + player_name(db_path))
        log(" CSV 출력 : " + out_dir)
    else:
        log(" DB       : 찾지 못함 → CSV 를 실행 위치에 저장")
        log(" CSV 출력 : " + out_dir)
    log("=" * 56)

    try:
        sat_rows = crawl_satellite(args.refresh)
        ins_rows, symbol = crawl_insane(args.refresh)
    except requests.RequestException as e:
        log("")
        log("[오류] 네트워크 요청 실패: " + str(e))
        log("       인터넷 연결을 확인한 뒤 다시 실행해주세요.")
        return 1

    merged = build_all()
    extract_unplayed(merged, db_path)

    log("")
    log("=" * 56)
    log(" 완료 (" + format(time.time() - t0, ".1f") + "초)")
    log("=" * 56)
    log(" 생성 파일:")
    for p in (SAT_CSV, INS_CSV, ALL_CSV, UNP_CSV):
        mark = "O" if os.path.exists(p) else "X"
        log("  [" + mark + "] " + os.path.basename(p))
    log("")
    log(" 이제 BMS_RandomPicker.exe 로 곡을 뽑을 수 있습니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
