# BMS 곡 랜덤 선택기 — 프로그램 구조

> LR2(OpenLR2) 플레이 기록을 읽어, 아직 안 한 곡이나 전체 곡 중 하나를 무작위로 뽑아주는 도구.
> 크롤러와 선택기 **두 개의 exe**로 이루어져 있다.

---

## 1. 한눈에 보기

```
┌─────────────────────────┐          ┌─────────────────────────┐
│  BMS_Crawler.exe        │          │  BMS_RandomPicker.exe   │
│  (1회 실행 · 데이터 준비) │          │  (평소 사용 · 곡 뽑기)     │
└───────────┬─────────────┘          └───────────▲─────────────┘
            │                                     │
            │  인터넷에서 곡 목록 수신              │  CSV 읽기
            │  + LR2 DB 와 대조                    │
            │                                     │
            ▼                                     │
    ┌───────────────────────────────────────────────┐
    │   LR2files\Database\Score\   (자동 생성)      │
    │   ├── <플레이어명>.db       ← 원본 (읽기만)    │
    │   ├── Satellite_songs.csv                    │
    │   ├── Insane_songs.csv                       │
    │   ├── All_songs.csv                          │
    │   └── Unplayed_songs.csv                     │
    └───────────────────────────────────────────────┘
```

**요약**: 크롤러를 한 번 돌려 CSV를 만들어두고, 그 뒤로는 선택기만 실행해서 곡을 뽑는다.

---

## 2. 두 exe 의 역할

| | BMS_Crawler.exe | BMS_RandomPicker.exe |
|---|---|---|
| **목적** | 곡 목록 · 미플레이 목록 준비 | 실제로 곡 뽑기 |
| **실행 시점** | 처음 한 번 + 새 곡을 플레이했을 때 | 곡 뽑고 싶을 때마다 |
| **인터넷** | 필요 (난이도표 다운로드) | 불필요 |
| **화면** | 콘솔 창 (진행 로그 표시) | GUI 창 |
| **출력** | CSV 4개 생성 | 화면에 곡 표시 |
| **크기** | 12.3 MB | 10.9 MB |
| **아이콘** | 노란 별 | 노란 별 |

---

## 3. BMS_Crawler.exe 상세

### 3-1. 처리 순서 (4단계)

```
[0/4] DB 탐색      <플레이어명>.db 를 찾아 CSV 출력 폴더 결정
[1/4] Satellite    stellabms.xyz/sl/score.json 다운로드 → Satellite_songs.csv
[2/4] Insane       darksabun.club/.../insane1/data.json 다운로드 → Insane_songs.csv
[3/4] 병합         두 표를 md5 기준으로 합침 → All_songs.csv
[4/4] 미플레이     <플레이어명>.db 와 대조 → Unplayed_songs.csv
```

### 3-2. DB 자동 탐색 (경로 · 파일명 하드코딩 없음)

실행 파일 위치를 기준으로 **상대 경로**를 찾아간다. OpenLR2를 어느 드라이브에 두든 동작한다.

**파일명도 가정하지 않는다.** LR2는 플레이어 이름을 따라 `<플레이어명>.db` 를 만들기 때문에
(`HANYUU.db`, `TAE1WON.db`, `player.db` …), **`*.db` 를 스캔**해서 고른다.

```
탐색 순서
  1) <exe 옆>\*.db
  2) <exe 옆>\LR2files\Database\Score\*.db     ← OpenLR2 표준
  3) <상위>\LR2files\Database\Score\*.db
  4) <상위상위>\LR2files\Database\Score\*.db
  5) <exe 아래 모든 폴더를 재귀 탐색>

찾으면 → 그 폴더(= Score)에 CSV 생성
못 찾으면 → exe 옆에 CSV 생성
```

### 3-2-1. 어떤 DB 를 고르는가

같은 폴더에 `.db` 가 여러 개일 수 있으므로 **2단계로 거른다**.

```
1차 — LR2 DB 검증
    sqlite_master 에 score · player 테이블이 둘 다 있는가?
    → 없으면 탈락 (다른 프로그램의 .db 를 걸러냄)

2차 — 여럿이면 기록 수 비교
    SELECT COUNT(*) FROM score 가 가장 많은 DB 를 사용
    (가장 많이 플레이한 계정 = 주 계정으로 판단)
```

실제 출력 예:

```
 (알림) LR2 DB 가 여러 개 있습니다. 기록이 가장 많은 것을 사용합니다:
        SUZUHA.db  (SUZUHA, 204곡)  ← 사용
        TAE1WON.db  (TAE1WON, 30곡)
        다른 DB 를 쓰려면:  --db "<경로>"
```

바꾸고 싶으면 `--db` 로 직접 지정한다.

### 3-2-2. `--list-db` 로 확인

어떤 `.db` 를 찾았고 LR2 DB 인지 아닌지 한눈에 본다.

```
$ BMS_Crawler.exe --list-db
발견한 LR2 DB:
  [X] D:\OpenLR2\LR2files\Database\Score\fake.db
  [O] D:\OpenLR2\LR2files\Database\Score\HANYUU.db  (HANYUU, 204곡)
  [O] D:\OpenLR2\LR2files\Database\Score\TAE1WON.db  (TAE1WON, 204곡)
```

`[O]` = 사용 가능 / `[X]` = LR2 DB 아님

### 3-3. 미플레이 판정 규칙

- 플레이 기록 DB(`<플레이어명>.db`)의 `score` 테이블에서 `hash` 를 읽는다
- **`clear=0` (Failed) 도 "플레이한 곡"으로 포함** → 제외 대상
- 즉 "미플레이" = 기록이 아예 없는 곡

```
전체 곡 풀      3,461 곡
├─ 이미 플레이    193 곡  (DB에 hash 있음 · Failed 포함)
└─ 미플레이      3,268 곡  ← Unplayed_songs.csv
```

### 3-4. 옵션

```bash
BMS_Crawler.exe                # DB 자동 탐색 + 캐시 재사용 (빠름)
BMS_Crawler.exe --refresh      # 사이트에서 강제 재다운로드
BMS_Crawler.exe --list-db      # 발견한 DB 목록만 보기
BMS_Crawler.exe --db "경로"    # DB 경로 직접 지정 (자동 탐색 대신)
```

---

## 4. CSV 4종 설명

모든 CSV는 **`level,title,md5`** 3컬럼, 인코딩 `utf-8-sig`(엑셀에서 한자·일본어 안 깨짐).

| 파일 | 행 수 | 내용 | 쓰는 곳 |
|---|---|---|---|
| `Satellite_songs.csv` | 2,467 | Satellite 난이도표 전체 (sl0~sl12) | 중간 산출물 |
| `Insane_songs.csv` | 1,035 | Insane 난이도표 전체 (★1~★25, ★???) | 중간 산출물 |
| `All_songs.csv` | 3,461 | 위 둘을 md5 중복 제거해 합친 전체 | 선택기 **버튼 1** |
| `Unplayed_songs.csv` | 3,268 | 전체 중 플레이 기록 없는 곡 | 선택기 **버튼 2** |

### 레벨 표기 규칙

| 난이도표 | 접두사 | 범위 | 비고 |
|---|---|---|---|
| Satellite | `sl` | `sl0` ~ `sl12` | |
| Insane | `★` | `★1` ~ `★25` | |
| Insane (미정) | `★` | `★???` | 독립 카테고리, 범위 검색에서 자동 제외 |

### 왜 md5가 연결고리인가

- 플레이 기록 DB에는 **곡 제목도, 난이도표 정보도 없다. 오직 `hash`(md5)만 있다.**
- 그래서 곡 이름·난이도는 반드시 크롤러 CSV와 조인해야 알 수 있다.
- 중복 판정도 **제목이 아니라 md5** 로 한다. (두 표에서 제목 공백이 미묘하게 다른 경우가 있음)

---

## 5. BMS_RandomPicker.exe 상세

### 5-1. 기능 3가지

| 버튼/기능 | 동작 |
|---|---|
| **버튼 1** | sl + ★ **모든 곡** 중 하나 랜덤 |
| **버튼 2** | sl + ★ 중 **미플레이/Failed** 곡 하나 랜덤 |
| **난이도 범위** | 예: `★10` 이상 ~ `★20` 이하 — 각 버튼에 적용 |

### 5-2. CSV 탐색

크롤러가 만든 CSV를 exe 위치 기준 상대 경로로 찾는다 (크롤러와 동일한 규칙).
못 찾으면 **"먼저 BMS_Crawler.exe 를 실행해주세요"** 안내 창을 띄운다.

### 5-3. 화면 구성 (시안 D 재해석 · Dual Mode)

```
┌────────────────────────────────────────────────┐
│ [Light] [Dark]                    ← 테마 토글   │
├────────────────────────────────────────────────┤
│ ■ BMS Random Picker    전체 3,461 · 미플레이 3,268│
├────────────────────────────────────────────────┤
│ 난이도 범위                                     │
│ [전체 ▼] ~ [전체 ▼]                            │
│ 해당 범위: 전체 3,461곡 / 미플레이 3,268곡  ← 노란색│
├────────────────────────────────────────────────┤
│ [READY]                                        │
│ 버튼을 눌러 곡을 뽑아보세요                       │
│                                                │
│ [버튼 1: 전체에서 뽑기]  [버튼 2: 안 한 곡에서 뽑기] │
└────────────────────────────────────────────────┘
```

- 라이트(`#FFFFFF`) / 다크(`#0F1117`) 전환, 선택한 테마는 유지
- 난이도 드롭다운 40개 (전체 + sl0~sl12 + ★1~★25 + ★???)
- 범위 힌트는 **노란색**, sl/★ 혼합 지정 시 **빨간 경고**

---

## 6. 폴더 구조 (배포 기준)

```
D:\OpenLR2\
├── BMS_Crawler.exe              ← 크롤러 (1회 실행)
├── BMS_RandomPicker.exe         ← 선택기 (평소 사용)
├── score.json                   ← Satellite 원본 캐시 (859 KB)
├── insane_data.json             ← Insane 원본 캐시 (484 KB)
│
└── LR2files\
    └── Database\
        └── Score\
            ├── <플레이어명>.db            ← LR2 원본 DB (읽기만, 수정 안 함)
            ├── Satellite_songs.csv      (2,467 행)
            ├── Insane_songs.csv         (1,035 행)
            ├── All_songs.csv            (3,461 행)
            └── Unplayed_songs.csv       (3,268 행)
```

**json 캐시 2개**는 재실행을 빠르게 하려고 exe 옆에 둔다. 지워도 다음 실행 때 다시 받아온다.

---

## 7. 전체 데이터 흐름

```
stellabms.xyz                     darksabun.club
  score.json                        data.json
  (2,467곡)                         (1,035곡)
      │                                  │
      ▼                                  ▼
 Satellite_songs.csv            Insane_songs.csv
      │                                  │
      └────────────┬─────────────────────┘
                   ▼
            md5 기준 중복 제거 (41곡)
                   │
                   ▼
            All_songs.csv (3,461)
                   │
                   │        <플레이어명>.db
                   │        score 테이블
                   │        (204개 hash)
                   └────────┬────────┘
                            ▼
                   기록 없는 곡만 추출
                            │
                            ▼
                   Unplayed_songs.csv (3,268)
                            │
                            ▼
                   BMS_RandomPicker.exe
                   → 곡 랜덤 표시
```

---

## 8. 개발 소스 (참고)

`C:\Suzuha\Satellite_Crawler\`

| 파일 | 설명 |
|---|---|
| `crawl_all.py` | 크롤러 본체 (1~4단계 전부) |
| `random_picker.py` | 선택기 GUI (Tkinter) |
| `build_exes.py` | exe 2개 빌드 스크립트 |
| `make_icon.py` | 노란 별 아이콘 생성 |
| `crawl_satellite.py` · `crawl_insane.py` | (구) 개별 크롤러 — `crawl_all.py` 로 통합됨 |
| `extract_all.py` · `extract_unplayed.py` | (구) 추출기 — `crawl_all.py` 로 통합됨 |

### 기술 스택

- **언어**: Python 3.14
- **GUI**: Tkinter (표준 라이브러리)
- **크롤링**: requests (JSON 직접 파싱)
- **DB**: sqlite3 (표준 라이브러리)
- **패키징**: PyInstaller 6.19 (onefile)
- **아이콘**: Pillow 로 생성한 `star_yellow.ico` (16~256px 7종)

---

*최종 갱신: 2026-09-30*
