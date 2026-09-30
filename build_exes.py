# -*- coding: utf-8 -*-
"""
BMS 툴 exe 2종 빌드 스크립트

  1) BMS_Crawler.exe       ← crawl_all.py  (아이콘: 노란 별)
  2) BMS_RandomPicker.exe  ← random_picker.py (아이콘: 노란 별)

사용:
  python build_exes.py            # 둘 다 빌드
  python build_exes.py crawler    # 크롤러만
  python build_exes.py picker     # 선택기만

결과: dist/ 폴더 안에 exe 2개
주의: 기존 파일을 지우지 않고 덮어쓴다 (--noconfirm).
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ICON = os.path.join(HERE, "star_yellow.ico")
DIST = os.path.join(HERE, "dist")
WORK = os.path.join(HERE, "_build")

TARGETS = {
    "crawler": {
        "script": "crawl_all.py",
        "name": "BMS_Crawler",
        "console": True,       # 로그를 봐야 하므로 콘솔 창 표시
        "hidden": [],
        "data": [],
    },
    "picker": {
        "script": "random_picker.py",
        "name": "BMS_RandomPicker",
        "console": False,      # GUI 앱 → 콘솔 숨김
        "hidden": [],
        # 선택기는 CSV/DB 를 exe 옆에서 읽는다 (코드가 app_dir() 사용)
        # 빌드 시점 파일을 동봉하지 않고, 크롤러가 만든 파일을 그대로 씀
        "data": [],
    },
}


def build(key):
    t = TARGETS[key]
    script = os.path.join(HERE, t["script"])
    if not os.path.exists(script):
        print("[오류] 스크립트 없음: " + script)
        return False

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",           # 기존 산출물 덮어쓰기
        "--clean",
        "--onefile",
        "--name", t["name"],
        "--distpath", DIST,
        "--workpath", WORK,
        "--specpath", HERE,
    ]
    cmd.append("--console" if t["console"] else "--windowed")

    if os.path.exists(ICON):
        cmd += ["--icon", ICON]
    else:
        print("[경고] 아이콘 없음 → 기본 아이콘 사용: " + ICON)

    for d in t["data"]:
        cmd += ["--add-data", d]
    for h in t["hidden"]:
        cmd += ["--hidden-import", h]

    cmd.append(script)

    print("=" * 60)
    print(" 빌드: " + t["name"] + "  (" + t["script"] + ")")
    print("=" * 60)
    print(" ".join(cmd))
    print()
    r = subprocess.run(cmd, cwd=HERE)
    ok = (r.returncode == 0)
    out = os.path.join(DIST, t["name"] + ".exe")
    if ok and os.path.exists(out):
        mb = os.path.getsize(out) / (1024 * 1024)
        print("\n[성공] " + out + "  (" + format(mb, ".1f") + " MB)\n")
    else:
        print("\n[실패] " + t["name"] + "\n")
    return ok


def main():
    keys = sys.argv[1:] or ["crawler", "picker"]
    keys = [k for k in keys if k in TARGETS]
    if not keys:
        print("사용: python build_exes.py [crawler] [picker]")
        return 1

    os.makedirs(DIST, exist_ok=True)
    results = {k: build(k) for k in keys}

    print("=" * 60)
    print(" 결과")
    print("=" * 60)
    for k, ok in results.items():
        print("  [" + ("O" if ok else "X") + "] " + TARGETS[k]["name"] + ".exe")
    print("\n출력 폴더: " + DIST)
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
