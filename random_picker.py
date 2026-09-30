# -*- coding: utf-8 -*-
"""
BMS 곡 랜덤 선택기 (Random Song Picker)
시안 D(Dual Mode) 재해석 — 라이트/다크 테마 토글 + 카드형 레이아웃

기능:
  1) sl + ★ 모든 곡에서 랜덤 선곡
  2) sl + ★ 중 '플레이하지 않았거나 Failed' 곡에서 랜덤 선곡
  3) 난이도 범위 제한 (예: ★10 이상 ~ ★20 이하) — 각 버튼에 적용

입력 CSV (스크립트와 같은 폴더):
  All_songs.csv      — 전체 곡 (3,461)
  Unplayed_songs.csv — 미플레이/Failed 곡 (3,268)

실행:  python -E random_picker.py
"""
import csv
import os
import random
import sys
import tkinter as tk
from tkinter import messagebox

# ----------------------------------------------------------------------------
# 테마 — 시안 D 의 dev(라이트) / gamer(다크) 팔레트를 Tkinter 색으로 옮김
# ----------------------------------------------------------------------------
THEMES = {
    "dev": {
        "bg": "#FFFFFF",
        "bg2": "#F6F7F9",
        "surface": "#FFFFFF",
        "line": "#E3E5EA",
        "text": "#2F343C",
        "ink": "#15181D",
        "muted": "#6C717A",
        "brand": "#2B5CFF",
        "brand_ink": "#FFFFFF",
        "brand_soft": "#EEF2FF",
        "bar_track": "#EEF0F3",
        "mode_bar": "#15181D",
        "mode_inactive": "#9097A6",
        "sl_badge_bg": "#EEF2FF",
        "sl_badge_fg": "#2B5CFF",
        "st_badge_bg": "#FFF3E0",
        "st_badge_fg": "#B26A00",
        "unplayed_bg": "#F1F8F4",
        "unplayed_fg": "#1B7A45",
        "hint": "#C98A00",
        "danger": "#D93B3B",
    },
    "gamer": {
        "bg": "#0F1117",
        "bg2": "#141722",
        "surface": "#171A24",
        "line": "#272B38",
        "text": "#D9DCE5",
        "ink": "#F3F4F8",
        "muted": "#8A90A0",
        "brand": "#5B82FF",
        "brand_ink": "#FFFFFF",
        "brand_soft": "#1C2340",
        "bar_track": "#232735",
        "mode_bar": "#07080C",
        "mode_inactive": "#9097A6",
        "sl_badge_bg": "#1C2340",
        "sl_badge_fg": "#8FB0FF",
        "st_badge_bg": "#3A2A12",
        "st_badge_fg": "#FFBE5C",
        "unplayed_bg": "#14261C",
        "unplayed_fg": "#63D69B",
        "hint": "#FFD24A",
        "danger": "#FF6B6B",
    },
}

FONT = "맑은 고딕"


def fonts(scale=1.0):
    def s(n, w="normal"):
        return (FONT, max(8, int(n * scale)), w)
    return {
        "title": s(26, "bold"),
        "h2": s(15, "bold"),
        "body": s(11),
        "small": s(10),
        "tiny": s(9),
        "hint": s(12, "bold"),
        "label": s(13, "bold"),
        "song": s(20, "bold"),
        "song_sub": s(12),
        "badge": s(10, "bold"),
        "btn": s(13, "bold"),
        "num": s(14, "bold"),
    }


def app_dir():
    """스크립트/exe 옆 폴더 (PyInstaller 대응)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


# ── CSV 탐색 규칙 (경로 하드코딩 없이 실행 파일 위치 기준) ──
#  크롤러가 OpenLR2 의 Score 폴더에 CSV 를 만들기 때문에,
#  선택기도 같은 곳을 찾아 읽어야 한다.
CSV_RELATIVE_CANDIDATES = [
    "",                                                    # exe 옆
    os.path.join("LR2files", "Database", "Score"),         # OpenLR2 표준
    os.path.join("..", "LR2files", "Database", "Score"),
    os.path.join("..", "..", "LR2files", "Database", "Score"),
    os.path.join("Score"),
]

CSV_SKIP_DIRS = {"_build", "build", ".git", "__pycache__", "node_modules"}


def find_csv(name):
    """CSV 를 실행 파일 위치 기준으로 찾는다.

    순서: exe 옆 → 상대 후보(Score 폴더 등) → 하위 재귀 탐색.
    못 찾으면 None.
    """
    base = app_dir()

    # 0) onefile 번들에 동봉된 경우
    if getattr(sys, "frozen", False):
        mp = getattr(sys, "_MEIPASS", None)
        if mp:
            p = os.path.join(mp, name)
            if os.path.exists(p):
                return p

    # 1) exe 옆 + 상대 후보
    for rel in CSV_RELATIVE_CANDIDATES:
        p = os.path.normpath(os.path.join(base, rel, name))
        if os.path.exists(p):
            return p

    # 2) 하위 재귀 탐색
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in CSV_SKIP_DIRS]
        if name in files:
            return os.path.abspath(os.path.join(root, name))
    return None


# ----------------------------------------------------------------------------
# 데이터 로드
# ----------------------------------------------------------------------------
def load_csv(path):
    """CSV → [(level, title, md5), ...]. path 가 None 이면 빈 리스트."""
    rows = []
    if not path or not os.path.exists(path):
        return rows
    with open(path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            rows.append(((r.get("level") or "").strip(),
                         (r.get("title") or "").strip(),
                         (r.get("md5") or "").strip().lower()))
    return rows


def level_num(level, symbol):
    """'sl12' / '★10' → 12 / 10, '★???' 나 파싱 불가면 None."""
    tail = level[len(symbol):] if level.startswith(symbol) else level
    return int(tail) if tail.isdigit() else None


def build_level_options(all_rows):
    """난이도 드롭다운에 쓸 (표시, 내부키) 목록을 만든다.

    반환: [("전체", "ALL"), ("sl0", "sl0"), ..., ("★1", "★1"), ..., ("★???","★???")]
    순서: sl0~sl12 → ★1~★25 → ★???
    """
    sl = sorted({lv for lv, _, _ in all_rows if lv.startswith("sl")},
                key=lambda x: int(x[2:]) if x[2:].isdigit() else 999)
    st = sorted({lv for lv, _, _ in all_rows if lv.startswith("★") and not lv.endswith("???")},
                key=lambda x: int(x[1:]) if x[1:].isdigit() else 999)
    st_unknown = sorted({lv for lv, _, _ in all_rows if lv.endswith("???")})
    return [("전체", "ALL")] + [(lv, lv) for lv in sl] + [(lv, lv) for lv in st] + [(lv, lv) for lv in st_unknown]


def in_range(level, lo_key, hi_key, rows_by_level):
    """난이도 범위 필터.

    - lo/hi 가 'ALL' 이면 그쪽 제한 없음
    - 같은 계열(sl끼리 / ★끼리)이면 숫자 비교
    - 계열이 다르면(sl vs ★) 범위 비교 불가 → 해당 곡은 통과시키지 않음
      (대신 'ALL' 로 두면 계열 무관하게 전부 포함)
    """
    if lo_key == "ALL" and hi_key == "ALL":
        return True
    ln = level_num(level, "sl") if level.startswith("sl") else level_num(level, "★")
    if ln is None:
        # ★??? 같은 레벨 미정 — 범위를 좁히면 제외, 전체면 포함
        return lo_key == "ALL" and hi_key == "ALL"

    lo_sym = "sl" if lo_key.startswith("sl") else ("★" if lo_key.startswith("★") else None)
    hi_sym = "sl" if hi_key.startswith("sl") else ("★" if hi_key.startswith("★") else None)
    sym = "sl" if level.startswith("sl") else "★"
    if lo_sym and sym != lo_sym:
        return False
    if hi_sym and sym != hi_sym:
        return False

    lo_n = level_num(lo_key, lo_sym) if lo_sym else None
    hi_n = level_num(hi_key, hi_sym) if hi_sym else None
    if lo_n is not None and ln < lo_n:
        return False
    if hi_n is not None and ln > hi_n:
        return False
    return True


# ----------------------------------------------------------------------------
# 앱
# ----------------------------------------------------------------------------
class PickerApp:
    def __init__(self, root):
        self.root = root
        self.theme = "gamer"          # 시안 D 의 기본 다크 모드
        self.scale = self._detect_scale()
        self.F = fonts(self.scale)

        self.all_rows = load_csv(find_csv("All_songs.csv"))
        self.unplayed_rows = load_csv(find_csv("Unplayed_songs.csv"))

        if not self.all_rows and not self.unplayed_rows:
            self._warn_missing_csv()
            self.root.destroy()
            raise SystemExit(0)

        self.level_options = build_level_options(self.all_rows)
        self._level_values = [k for _, k in self.level_options]

        self._build_ui()
        self.apply_theme()
        self._show_initial()

    def _detect_scale(self):
        """창이 작은 노트북에서 폰트를 자동으로 줄인다."""
        h = self.root.winfo_screenheight()
        for sc, limit in ((1.0, 900), (0.9, 800), (0.82, 720), (0.75, 0)):
            if h >= limit:
                return sc
        return 0.75

    def _warn_missing_csv(self):
        """곡 CSV 를 못 찾았을 때 안내하고 종료한다."""
        msg = (
            "곡 데이터 CSV 를 찾지 못했습니다.\n\n"
            "먼저 BMS_Crawler.exe 를 실행해주세요.\n"
            "크롤러가 곡 목록과 플레이 기록을 읽어\n"
            "아래 위치에 CSV 를 만들어줍니다.\n\n"
            "  <LR2 폴더>\\LR2files\\Database\\Score\\\n"
            "      All_songs.csv\n"
            "      Unplayed_songs.csv\n\n"
            "실행 위치: " + app_dir()
        )
        try:
            messagebox.showerror("곡 데이터 없음", msg)
        except Exception:
            print(msg)

    # ---------------- 색 헬퍼 ----------------
    @property
    def C(self):
        return THEMES[self.theme]

    # ---------------- UI 구성 ----------------
    def _build_ui(self):
        C = self.C
        self.root.title("BMS 곡 랜덤 선택기")
        self.root.configure(bg=C["bg"])

        # ── 상단 모드 바 (시안 D 의 mode-bar + mode-tab) ──
        self.mode_bar = tk.Frame(self.root, bg=C["mode_bar"])
        self.mode_bar.pack(fill="x")
        self.mode_tabs = {}
        for key, label in (("dev", "◐ Light"), ("gamer", "● Dark")):
            b = tk.Button(self.mode_bar, text=label, bd=0, relief="flat",
                          font=self.F["badge"], cursor="hand2", padx=16, pady=6,
                          command=lambda k=key: self.set_theme(k))
            b.pack(side="left", padx=(6, 0), pady=(6, 0))
            self.mode_tabs[key] = b

        # ── 헤더 ──
        self.header = tk.Frame(self.root, bg=C["bg"],
                               highlightbackground=C["line"], highlightthickness=0)
        self.header.pack(fill="x")
        inner = tk.Frame(self.header, bg=C["bg"])
        inner.pack(fill="x", padx=24, pady=14)

        self.logo_mark = tk.Label(inner, text="", bg=C["brand"], width=2, height=1)
        self.logo_mark.pack(side="left", padx=(0, 10))
        self.logo = tk.Label(inner, text="BMS Random Picker", bg=C["bg"],
                             fg=C["ink"], font=self.F["h2"])
        self.logo.pack(side="left")

        self.stat_label = tk.Label(inner, text="", bg=C["bg"], fg=C["muted"],
                                   font=self.F["small"])
        self.stat_label.pack(side="right")

        # ── 본문 ──
        self.body = tk.Frame(self.root, bg=C["bg2"])
        self.body.pack(fill="both", expand=True)

        # 필터 카드
        self.filter_card = tk.Frame(self.body, bg=C["surface"],
                                    highlightbackground=C["line"], highlightthickness=1)
        self.filter_card.pack(fill="x", padx=24, pady=(16, 0))
        fi = tk.Frame(self.filter_card, bg=C["surface"])
        fi.pack(fill="x", padx=18, pady=14)

        self.filter_title = tk.Label(fi, text="난이도 범위", bg=C["surface"],
                                     fg=C["muted"], font=self.F["label"])
        self.filter_title.pack(anchor="w")

        row = tk.Frame(fi, bg=C["surface"])
        row.pack(fill="x", pady=(6, 0))

        self.lo_var = tk.StringVar(value="전체")
        self.hi_var = tk.StringVar(value="전체")
        self.lo_menu = self._make_dropdown(row, self.lo_var)
        self.lo_menu.pack(side="left")
        self.tilde = tk.Label(row, text="~", bg=C["surface"], fg=C["muted"],
                              font=self.F["body"])
        self.tilde.pack(side="left", padx=8)
        self.hi_menu = self._make_dropdown(row, self.hi_var)
        self.hi_menu.pack(side="left")

        self.range_hint = tk.Label(fi, text="", bg=C["surface"], fg=C["hint"],
                                   font=self.F["hint"])
        self.range_hint.pack(anchor="w", pady=(6, 0))

        # ── 결과 카드 ──
        self.result_card = tk.Frame(self.body, bg=C["surface"],
                                    highlightbackground=C["line"], highlightthickness=1)
        self.result_card.pack(fill="both", expand=True, padx=24, pady=16)

        rc = tk.Frame(self.result_card, bg=C["surface"])
        rc.pack(fill="both", expand=True, padx=22, pady=20)

        self.badge = tk.Label(rc, text="", bg=C["brand_soft"], fg=C["brand"],
                              font=self.F["badge"], padx=10, pady=3)
        self.badge.pack(anchor="w")

        self.song_title = tk.Label(rc, text="", bg=C["surface"], fg=C["ink"],
                                   font=self.F["song"], wraplength=520, justify="left")
        self.song_title.pack(anchor="w", pady=(10, 2))

        self.song_sub = tk.Label(rc, text="", bg=C["surface"], fg=C["muted"],
                                 font=self.F["song_sub"], justify="left")
        self.song_sub.pack(anchor="w")

        # ── 버튼 ──
        btns = tk.Frame(self.body, bg=C["bg2"])
        btns.pack(fill="x", padx=24, pady=(0, 18))

        self.btn1 = tk.Button(btns, text="🎲  전체 곡에서 랜덤 선곡",
                              bd=0, relief="flat", cursor="hand2",
                              font=self.F["btn"], padx=18, pady=12,
                              command=self.pick_all)
        self.btn1.pack(side="left", expand=True, fill="x", padx=(0, 6))

        self.btn2 = tk.Button(btns, text="✨  미플레이 · Failed 곡에서 선곡",
                              bd=0, relief="flat", cursor="hand2",
                              font=self.F["btn"], padx=18, pady=12,
                              command=self.pick_unplayed)
        self.btn2.pack(side="left", expand=True, fill="x", padx=(6, 0))

        # 상태 표시줄
        self.status = tk.Label(self.root, text="", bg=C["bg"], fg=C["muted"],
                               font=self.F["tiny"], anchor="w")
        self.status.pack(fill="x", padx=24, pady=(0, 8))

        self._update_stats()
        self._update_range_hint()

    def _make_dropdown(self, parent, var):
        """ttk 없이 순수 tk.OptionMenu 스타일 드롭다운."""
        om = tk.OptionMenu(parent, var, *self._level_values,
                           command=lambda _=None: self._update_range_hint())
        om.config(bd=0, relief="flat", highlightthickness=0,
                  font=self.F["num"], padx=6, pady=2, cursor="hand2",
                  activebackground=self.C["brand_soft"])
        om["menu"].config(font=self.F["num"])
        return om

    # ---------------- 테마 ----------------
    def set_theme(self, key):
        if key not in THEMES:
            return
        self.theme = key
        self.apply_theme()

    def apply_theme(self):
        C = self.C

        # 모드 탭 색
        for k, b in self.mode_tabs.items():
            if k == self.theme:
                b.config(bg=C["bg"], fg=C["ink"],
                         activebackground=C["bg"], activeforeground=C["ink"])
            else:
                b.config(bg=C["mode_bar"], fg=C["mode_inactive"],
                         activebackground=C["mode_bar"], activeforeground=C["ink"])

        for w in (self.root, self.header, self.body):
            w.config(bg=C["bg"] if w is not self.body else C["bg2"])

        self.header.config(bg=C["bg"], highlightbackground=C["line"])
        for w in (self.logo, self.stat_label):
            w.config(bg=C["bg"])
        self.logo.config(fg=C["ink"])
        self.stat_label.config(fg=C["muted"])
        self.logo_mark.config(bg=C["brand"])

        for card in (self.filter_card, self.result_card):
            card.config(bg=C["surface"], highlightbackground=C["line"])

        def recolor_surface(parent):
            for ch in parent.winfo_children():
                if isinstance(ch, (tk.Frame, tk.Label)) and ch in (
                        self.tilde, self.filter_title, self.range_hint,
                        self.badge, self.song_title, self.song_sub):
                    continue
                try:
                    if ch.cget("bg") in ("#FFFFFF", "#171A24"):
                        ch.config(bg=C["surface"])
                except Exception:
                    pass
                recolor_surface(ch)

        self.filter_title.config(bg=C["surface"], fg=C["muted"])
        self.range_hint.config(bg=C["surface"], fg=C["hint"])
        self.tilde.config(bg=C["surface"], fg=C["muted"])

        for w in (self.badge, self.song_title, self.song_sub):
            w.config(bg=C["surface"])
        self.song_title.config(fg=C["ink"])
        self.song_sub.config(fg=C["muted"])

        for om in (self.lo_menu, self.hi_menu):
            om.config(bg=C["surface"], fg=C["ink"],
                      activebackground=C["brand_soft"], activeforeground=C["ink"],
                      highlightbackground=C["surface"])
            om["menu"].config(bg=C["surface"], fg=C["ink"],
                              activebackground=C["brand"],
                              activeforeground=C["brand_ink"])
            # 드롭다운 화살표(내부 메뉴버튼) 색
            try:
                om.children["menu"].config(bg=C["surface"], fg=C["ink"])
            except Exception:
                pass

        self.btn1.config(bg=C["brand"], fg=C["brand_ink"],
                         activebackground=C["brand"], activeforeground=C["brand_ink"],
                         disabledforeground=C["brand_ink"])
        self.btn2.config(bg=C["surface"], fg=C["ink"],
                         activebackground=C["brand_soft"], activeforeground=C["ink"],
                         disabledforeground=C["ink"],
                         highlightbackground=C["line"], highlightthickness=1)
        self.status.config(bg=C["bg"], fg=C["muted"])

        # 배지 색은 현재 곡에 맞춰 다시 칠한다 (결과가 있으면)
        if self.song_title.cget("text"):
            self._paint_badge()

        recolor_surface(self.filter_card)
        recolor_surface(self.result_card)

    # ---------------- 데이터 ----------------
    def _update_stats(self):
        self.stat_label.config(
            text="전체 %s곡 · 미플레이 %s곡" % (format(len(self.all_rows), ","),
                                              format(len(self.unplayed_rows), ",")))

    def _update_range_hint(self):
        lo, hi = self.lo_var.get(), self.hi_var.get()
        pool = self._filtered(self.all_rows)
        upool = self._filtered(self.unplayed_rows)
        C = THEMES[self.theme]
        if lo == "전체" and hi == "전체":
            self.range_hint.config(text="범위 제한 없음 (sl + ★ 전체)",
                                   fg=C["hint"])
        elif lo != "전체" and hi != "전체" and (
                (lo.startswith("sl")) != (hi.startswith("sl"))):
            self.range_hint.config(
                text="⚠ sl 과 ★ 는 난이도 체계가 달라 함께 범위 지정할 수 없습니다 (한쪽을 '전체'로)",
                fg=C["danger"])
        else:
            self.range_hint.config(
                text="해당 범위: 전체 %s곡 / 미플레이 %s곡" % (format(len(pool), ","),
                                                          format(len(upool), ",")),
                fg=C["hint"])
        self._last_status = (len(pool), len(upool))

    def _filtered(self, rows):
        lo, hi = self.lo_var.get(), self.hi_var.get()
        return [r for r in rows if in_range(r[0], lo, hi, None)]

    # ---------------- 선곡 ----------------
    def _show_initial(self):
        self.badge.config(text="READY", bg=self.C["brand_soft"], fg=self.C["brand"])
        self.song_title.config(text="버튼을 눌러 곡을 뽑아보세요")
        self.song_sub.config(text="난이도 범위를 지정하면 그 안에서만 뽑습니다.")
        self.status.config(text="")

    def _paint_badge(self):
        lv = getattr(self, "_cur_level", "")
        C = self.C
        if lv.startswith("sl"):
            self.badge.config(bg=C["sl_badge_bg"], fg=C["sl_badge_fg"])
        elif lv.startswith("★"):
            self.badge.config(bg=C["st_badge_bg"], fg=C["st_badge_fg"])
        else:
            self.badge.config(bg=C["brand_soft"], fg=C["brand"])

    def pick_all(self):
        self._pick(self.all_rows, "전체 곡")

    def pick_unplayed(self):
        self._pick(self.unplayed_rows, "미플레이 · Failed")

    def _pick(self, rows, label):
        pool = self._filtered(rows)
        if not pool:
            messagebox.showinfo(
                "결과 없음",
                "%s 중 지정한 난이도 범위에 해당하는 곡이 없습니다.\n"
                "범위를 넓히거나 '전체'로 바꿔보세요." % label)
            return
        level, title, _md5 = random.choice(pool)
        self._cur_level = level
        self.badge.config(text=level)
        self._paint_badge()
        self.song_title.config(text=title)
        self.song_sub.config(text="%s · %s" % (label, level))
        self.status.config(text="%s %s곡 중 1곡 선택" % (label, format(len(pool), ",")))


def main():
    root = tk.Tk()
    app = PickerApp(root)

    # 창 크기 — 화면 높이에 맞춰 클램프.
    # 주의: update_idletasks() 만으로는 지오메트리 미적용 상태라 reqheight 가 작게 나온다
    #       (창이 237x39 로 뜨는 버그) → update() 로 실제 레이아웃을 확정시킨 뒤 측정.
    root.update()
    w = max(620, root.winfo_reqwidth())
    h = max(560, root.winfo_reqheight())
    max_h = root.winfo_screenheight() - 90
    max_w = root.winfo_screenwidth() - 40
    if h > max_h:
        h = max_h
    if w > max_w:
        w = max_w
    root.geometry("%dx%d" % (w, h))
    root.update()
    root.minsize(560, 480)
    root.mainloop()


if __name__ == "__main__":
    main()
