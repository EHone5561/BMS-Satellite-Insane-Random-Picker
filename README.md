# BMS 곡 랜덤 선택기 (BMS Random Picker)

LR2(OpenLR2) 플레이 기록을 읽어서, **아직 안 한 곡**이나 **전체 곡 중 하나**를 무작위로 뽑아주는 프로그램입니다.

곡 뽑을 때 "뭐 하지" 고민하는 시간을 줄여줍니다.

- 두 난이도표(*Satellite* `sl0`~`sl12` + 発狂BMS + `★1`~`★25`)를 합쳐 *약 3,460곡*에서 뽑습니다
- 내 플레이 기록(`<플레이어명>.db`)을 자동으로 찾아 **미플레이/실패 곡**만 골라낼 수 있습니다
- 난이도 범위 제한 검색, 라이트/다크 테마 지원

---

## 빠른 시작 (사용자)

윈도우 exe만 있으면 됩니다.

1. **[Releases](../../releases)** 에서 `BMS_Crawler.exe` 와 `BMS_RandomPicker.exe` 를 받습니다
2. 두 파일을 **OpenLR2 폴더에** 복사합니다
3. `BMS_Crawler.exe` 를 **처음 한 번** 실행 (곡 목록 준비)
4. 그 뒤로는 `BMS_RandomPicker.exe` 로 곡을 뽑습니다

자세한 사용법은 아래 **설치** · **사용법** 항목을 참고하세요.

---

## 개발자용

### 소스에서 직접 실행

```bash
# 필요: Python 3.10+ / 의존성: requests, Pillow (아이콘 생성 시)
pip install requests pillow

# 크롤러 실행 (CSV 4종 생성)
python crawl_all.py

# 랜덤 선택기 실행 (GUI)
python random_picker.py
```

> `Tkinter` 는 파이썬 표준 라이브러리라 별도 설치가 필요 없습니다.

### exe 빌드

```bash
pip install pyinstaller

python make_icon.py     # 노란 별 아이콘 생성 (최초 1회)
python build_exes.py    # exe 2개 빌드 → dist/
```

### 저장소 구조

```
├── crawl_all.py             크롤러 본체 (난이도표 수집 + 미플레이 추출)
├── random_picker.py         랜덤 선택기 GUI (Tkinter)
├── build_exes.py            exe 2개 빌드 스크립트
├── make_icon.py             노란 별 아이콘 생성
├── star_yellow.ico/.png     아이콘
│
├── crawl_satellite.py       (구) Satellite 단독 크롤러 — 통합됨
├── crawl_insane.py          (구) Insane 단독 크롤러 — 통합됨
├── extract_all.py           (구) 전체 목록 추출기 — 통합됨
├── extract_unplayed.py      (구) 미플레이 추출기 — 통합됨
│
├── _test_openlr2.py         검증: OpenLR2 구조 흉내 → CSV 생성 확인
├── _test_exe.py             검증: exe 실행 → CSV 생성 확인
├── _test_exe2.py            검증: 다른 이름 DB 자동 인식 확인
├── _test_dbname.py          검증: DB 선택 로직 (다중 DB·가짜 DB)
│
├── README.md                이 문서 (사용법)
└── PROGRAM_STRUCTURE.md     내부 구조 상세 문서
```

### 테스트

OpenLR2 폴더 구조를 임시로 만들어 검증합니다.
**본인 `HANYUU.db`(또는 자기 DB)가 프로젝트 폴더에 있어야** 실행됩니다.

```bash
python _test_openlr2.py    # DB 자동 탐색 + CSV 생성
python _test_dbname.py     # DB 여러 개 / 다른 이름 / 가짜 DB
```

---

## 라이선스

**MIT License** — 자유롭게 사용·수정·배포할 수 있습니다. 자세한 내용은 [LICENSE](LICENSE) 를 참고하세요.

> ⚠ **개인정보 주의**: `LR2files\Database\Score\*.db` 에는 **계정 정보(비밀번호 해시·IR ID)와
> 개인 플레이 기록**이 들어있습니다. 이 저장소는 `.gitignore` 로 `*.db` 를 막아두었으니
> **절대 커밋하지 마세요.** 각자 자기 DB만 로컬에서 쓰면 됩니다.

---

## 데이터 출처

곡 목록은 아래 난이도표 사이트에서 받아옵니다. 각 사이트의 이용 규칙을 따릅니다.

| 난이도표 | 사이트 |
|---|---|
| **Satellite (sl)** | [stellabms.xyz](https://stellabms.xyz/sl/table.html) |
| **発狂BMS (★)** | [darksabun.club](https://darksabun.club/table/archive/insane1/) |

---

## 준비물

- **OpenLR2** (LR2 기반 BMS 플레이어) — 플레이 기록이 있어야 미플레이 곡을 구분할 수 있습니다
- **인터넷 연결** — 곡 목록(난이도표)을 받아오는 데 필요합니다 (크롤러 실행 시에만)
- Windows 10 / 11

---

## 파일 구성

압축을 풀면 이렇게 되어 있습니다.

```
BMS_Crawler.exe          ← ① 곡 목록 준비 (처음 한 번)
BMS_RandomPicker.exe     ← ② 곡 뽑기 (평소 사용)
score.json               ← 캐시 (자동 생성)
insane_data.json         ← 캐시 (자동 생성)
```

> **중요**: 두 exe는 **같은 폴더에** 두세요.
>
> **DB 파일명은 상관없습니다.** LR2가 만든 `<플레이어명>.db` 를 자동으로 찾습니다.
> (예: `HANYUU.db`, `TAE1WON.db`, `player.db` …)

---

## 설치

1. `BMS_Crawler.exe` 와 `BMS_RandomPicker.exe` 를 **OpenLR2 폴더에** 복사합니다.

```
예시)
D:\OpenLR2\
├── BMS_Crawler.exe          ← 여기에 복사
├── BMS_RandomPicker.exe     ← 여기에 복사
├── LR2Body.exe
└── LR2files\
    └── Database\
        └── Score\
            └── <플레이어명>.db   ← 이미 있는 파일 (예: HANYUU.db)
```

> OpenLR2 폴더가 `D:\OpenLR2` 가 아니어도 됩니다. `C:\Games\LR2` 든 어디든,
> **BMS_Crawler.exe 를 OpenLR2 최상위 폴더에 두기만** 하면 알아서 찾아갑니다.

---

## 사용법

### 1단계 — 처음 한 번: 곡 목록 준비

`BMS_Crawler.exe` 를 **더블클릭**합니다.

검은 콘솔 창이 뜨고 진행 상황이 표시됩니다.

```
========================================================
 BMS 곡 데이터 크롤러
 실행 위치: D:\OpenLR2
 DB 발견  : D:\OpenLR2\LR2files\Database\Score\HANYUU.db
 플레이어 : HANYUU
 CSV 출력 : D:\OpenLR2\LR2files\Database\Score
========================================================

[1/4] Satellite (sl) 크롤링 — stellabms.xyz
--------------------------------------------------------
  (요청) https://stellabms.xyz/sl/score.json
  총 2467 곡 수신
  (저장) Satellite_songs.csv  2467 행
    sl0 : 252
    sl1 : 274
    ...

[2/4] Insane (★) 크롤링 — darksabun.club
--------------------------------------------------------
  ...

[3/4] 전체 곡 리스트 병합 (sl + ★, md5 중복 제거)
--------------------------------------------------------
  병합 결과 3461곡 (중복 제거 41곡)

[4/4] 미플레이 곡 추출 (플레이 기록 DB 대조)
--------------------------------------------------------
  DB: D:\OpenLR2\LR2files\Database\Score\HANYUU.db
  플레이 기록 204곡 (Failed 포함)
  전체 풀      : 3461곡
  이미 플레이  : 193곡
  미플레이     : 3268곡
  (저장) Unplayed_songs.csv  3268 행

========================================================
 완료 (1.4초)
========================================================
 생성 파일:
  [O] Satellite_songs.csv
  [O] Insane_songs.csv
  [O] All_songs.csv
  [O] Unplayed_songs.csv

 이제 BMS_RandomPicker.exe 로 곡을 뽑을 수 있습니다.
```

**"완료"** 가 뜨면 성공입니다. 창을 닫으세요.

> `[O]` 가 4개 다 나와야 정상입니다. 하나라도 `[X]` 면 인터넷 연결을 확인하고 다시 실행하세요.

### 2단계 — 곡 뽑기

`BMS_RandomPicker.exe` 를 **더블클릭**합니다.

아래 같은 창이 뜹니다.

```
┌──────────────────────────────────────────────────┐
│ [Light] [Dark]                     ← 테마 전환    │
├──────────────────────────────────────────────────┤
│ ■ BMS Random Picker   전체 3,461곡 · 미플레이 3,268곡│
├──────────────────────────────────────────────────┤
│ 난이도 범위                                       │
│ [전체 ▼]  ~  [전체 ▼]                            │
│ 해당 범위: 전체 3,461곡 / 미플레이 3,268곡          │
├──────────────────────────────────────────────────┤
│ [READY]                                          │
│ 버튼을 눌러 곡을 뽑아보세요                         │
│                                                  │
│ [전체에서 뽑기]      [안 한 곡에서 뽑기]             │
└──────────────────────────────────────────────────┘
```

**버튼 설명**

| 버튼 | 뽑는 대상 |
|---|---|
| **전체에서 뽑기** | sl + ★ 모든 곡 중 하나 (이미 한 곡도 나옴) |
| **안 한 곡에서 뽑기** | 플레이 기록이 없는 곡 중 하나 (Failed도 제외됨) |

**난이도 범위 지정** (선택)

- 드롭다운에서 `이상` ~ `이하` 를 고릅니다
- 예: `★10` ~ `★20` → 그 범위 안에서만 뽑힘
- `전체` 로 두면 범위 제한 없음

> ⚠ `sl` 과 `★` 는 난이도 체계가 달라서 **한쪽만** 지정해야 합니다.
> (예: `sl5` ~ `전체` ✅ / `sl5` ~ `★10` ❌ → 빨간 경고)

**테마 전환**

- `Light` / `Dark` 버튼으로 밝은 화면·어두운 화면 전환

---

## 언제 다시 크롤러를 돌려야 하나요?

새로 곡을 플레이했다면, **"안 한 곡에서 뽑기"** 목록을 갱신해야 합니다.

```
새 곡을 플레이했다 → BMS_Crawler.exe 다시 실행 → 끝
```

**주기적으로 돌릴 필요는 없습니다.** 아래 경우에만 다시 실행하세요:

- 새 곡을 플레이했을 때 (미플레이 목록 갱신)
- 새 난이도표가 나왔을 때 (곡 목록 갱신)
- 몇 달 지나서 새 곡이 추가됐을 때

> `--refresh` 없이 실행하면 캐시(`score.json`)를 재사용합니다.
> 곡 목록까지 새로 받고 싶으면 명령 프롬프트에서 `BMS_Crawler.exe --refresh` 로 실행하세요.

---

## 자주 묻는 질문

### Q. "곡 데이터 CSV 를 찾지 못했습니다" 창이 떠요

`BMS_Crawler.exe` 를 먼저 실행해야 합니다.
그래도 안 되면 두 exe가 **같은 폴더에 있는지** 확인하세요.

### Q. 곡이 안 뽑히고 "해당 범위에 곡이 없습니다" 가 떠요

난이도 범위를 너무 좁게 잡았거나, `sl` 과 `★` 를 섞어서 지정한 경우입니다.
범위를 넓히거나 한쪽을 `전체` 로 바꿔보세요.

### Q. "안 한 곡에서 뽑기" 를 눌러도 아는 곡이 나와요

`BMS_Crawler.exe` 를 마지막으로 돌린 뒤에 플레이한 곡은 아직 목록에 없습니다.
크롤러를 다시 실행하면 최신 상태가 됩니다.

### Q. 창이 작게 나와요

화면 해상도에 맞춰 폰트가 자동으로 조절됩니다.
그래도 작으면 Windows 디스플레이 설정에서 배율을 확인해보세요.

### Q. `score.json` / `insane_data.json` 은 뭔가요?

난이도표 원본을 임시 저장해둔 캐시입니다.
**지워도 됩니다** — 다음 실행 때 다시 받아옵니다.
(남겨두면 재실행이 더 빠릅니다.)

### Q. 곡 데이터를 새로 받고 싶어요

`score.json` 과 `insane_data.json` 을 지우고 `BMS_Crawler.exe` 를 다시 실행하세요.

### Q. 내 플레이 기록(DB)이 수정되나요?

**아닙니다.** 읽기만 합니다.
`LR2files\Database\Score\` 폴더에 CSV를 새로 쓸 뿐, DB 파일은 건드리지 않습니다.

### Q. 백신이 exe를 경고해요

PyInstaller로 만든 실행 파일에 가끔 나오는 오탐입니다.
"추가 정보" → "실행" 을 누르거나, 백신 예외에 등록하세요.

### Q. 내 DB 파일 이름이 `HANYUU.db` 가 아닌데요?

**상관없습니다.** LR2는 플레이어 이름을 따라 `<플레이어명>.db` 를 만드는데,
크롤러가 **Score 폴더의 `.db` 를 자동으로 찾아** 씁니다.
(`TAE1WON.db`, `player.db` 뭐든 괜찮습니다.)

### Q. DB가 여러 개면 어떻게 되나요?

플레이 기록(`score` 테이블)이 **가장 많은 DB** 를 자동으로 고릅니다.
어떤 DB를 찾았는지 보려면:

```bash
BMS_Crawler.exe --list-db
```

특정 DB를 쓰고 싶으면 직접 지정하세요:

```bash
BMS_Crawler.exe --db "C:\...\내DB.db"
```

### Q. `--list-db` 결과에 `[X]` 가 뜨는데요?

LR2 스코어 DB가 아니라는 뜻입니다 (`score`/`player` 테이블이 없음).
같은 폴더에 다른 프로그램의 `.db` 가 있으면 그렇게 표시됩니다.
`[O]` 인 것만 실제로 쓰입니다.

---

## 고급 — 명령 프롬프트 옵션

`BMS_Crawler.exe` 는 옵션을 받습니다.
(`Shift + 우클릭` → "여기서 PowerShell 창 열기" 후 실행)

```bash
# 기본 실행 (DB 자동 탐색 · 캐시 재사용)
.\BMS_Crawler.exe

# 사이트에서 강제 재다운로드
.\BMS_Crawler.exe --refresh

# 어떤 DB 를 찾았는지 목록 보기
.\BMS_Crawler.exe --list-db

# DB 경로 직접 지정 (자동 탐색 대신)
.\BMS_Crawler.exe --db "D:\OpenLR2\LR2files\Database\Score\내DB.db"
```

---

## 폴더 구조 (실행 후)

```
D:\OpenLR2\
├── BMS_Crawler.exe
├── BMS_RandomPicker.exe
├── score.json                    ← 캐시
├── insane_data.json              ← 캐시
└── LR2files\
    └── Database\
        └── Score\
            ├── <플레이어명>.db           ← 원본 (수정 안 함)
            ├── Satellite_songs.csv      ← 생성됨
            ├── Insane_songs.csv         ← 생성됨
            ├── All_songs.csv            ← 생성됨
            └── Unplayed_songs.csv       ← 생성됨
```

CSV 4개는 **플레이 기록 DB 옆**(= Score 폴더)에 생성됩니다.
크롤러를 다시 돌리면 **덮어씁니다**.

---

## 요약 (3줄)

1. exe 2개를 **OpenLR2 폴더에** 복사
2. `BMS_Crawler.exe` 를 **처음 한 번** 실행
3. 그 뒤로는 `BMS_RandomPicker.exe` 로 곡 뽑기

새 곡을 플레이했을 때만 크롤러를 다시 돌려주세요.

---

*더 자세한 내부 구조는 `PROGRAM_STRUCTURE.md` 를 참고하세요.*
