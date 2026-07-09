# pdf_restyler — H SECURITY 명함 PDF 생성기

이름·직급·연락처를 입력하면 **회사 명함 PDF를 자동 생성**하는 Windows 데스크톱 앱입니다.
실사용자(비개발자)가 더블클릭 한 번으로 쓸 수 있도록 **단일 실행 파일(exe)** 로 패키징해 실무에 배포했습니다.

> PDF 내부 구조(글리프·redaction) 직접 제어 · 실사용자 배포 완료 · PySide6 데스크톱 GUI

## 개요

- 대표(핑크) / 직원(검정·로고) **디자인 자동 분기**
- 입력 폼 + **실시간 미리보기** → 버튼 한 번으로 PDF 저장 (빈 항목은 명함에서 자동 생략)
- 원본 명함 PDF의 개인정보를 **redaction으로 완전 제거**하고, 새 텍스트를 같은 자리·같은 스타일로 재구성

## 기술적 하이라이트

- **아웃라인 글리프 재구성** — 원본 명함의 글자가 텍스트가 아닌 **곡선(아웃라인)** 으로 박혀 있어 직접 치환이 불가능한 문제를, 좌표·색·자간을 추출해 **Pretendard 폰트로 같은 자리에 다시 그리는 방식**으로 해결
- **개인정보 완전 삭제(redaction)** — 흰색 덮어쓰기가 아니라 PDF 내부 콘텐츠를 실제로 삭제하는 redaction 적용 → 배포 파일에 원본 개인정보가 잔존하지 않음 (보안 관점 설계)
- **비개발자 배포** — PyInstaller onefile로 Python 런타임·라이브러리·폰트·템플릿까지 전부 내장한 단일 exe. 설치 과정 0, 저장 다이얼로그 없이 정해진 폴더에 `YYMMDD_이름.pdf` 자동 저장
- **인쇄 규격 준수** — 명함 90×50mm, 브랜드 컬러(`#EC008C`/`#000000`) 정확 재현

## 기술 스택

| 구분 | 사용 기술 |
|------|-----------|
| Language | Python 3.12 |
| GUI | PySide6 (Qt) · qdarktheme |
| PDF 엔진 | PyMuPDF (글리프 분석·redaction·텍스트 재구성) |
| 배포 | PyInstaller (단일 exe, Windows 64bit) |

## 실행 (개발)

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## 배포 exe 빌드

```powershell
pyinstaller main.py --onefile --windowed --name "HSecurity_명함생성기" `
  --icon assets/chiikawa.ico --add-data "assets;assets" `
  --paths src --hidden-import gui --hidden-import card_generator `
  --collect-all qdarktheme
```

→ `dist/HSecurity_명함생성기.exe` + `docs/사용설명서.pdf`(비개발자용 매뉴얼)를 zip으로 묶어 전달.

## 구조

```
main.py                      진입점(런처)
src/
  card_generator.py          명함 생성 엔진 (CardInfo → PDF)
  gui.py                     PySide6 GUI (입력 폼·미리보기·저장·다크테마)
assets/
  fonts/Pretendard-*.ttf     폰트
  template/명함템플릿.pdf      명함 베이스 (로고·레이아웃만, 개인정보 제거됨)
docs/
  사용설명서.pdf              비개발자용 매뉴얼
  대표_템플릿.pdf / 직원_템플릿.pdf  샘플(더미값)
```

## 개발 방식

이 프로젝트는 역할별 AI 에이전트 팀(기획·백엔드·프론트엔드·QA·리뷰·보안)을 직접 구성·운영하는 [AI Agent Workspace](https://github.com/muhwa91/ai-agent-workspace) 거버넌스 아래에서 개발·유지보수됩니다 — 훅 기반 품질 게이트, 비공개 모노레포 → 공개 미러 워크플로우.

---
개발 · 제작 : 여중기
