# H SECURITY 명함 생성기 (pdf_restyler)

이름·직급·연락처를 입력하면 **H SECURITY 명함 PDF를 자동 생성**하는 Windows 데스크톱 앱.
비개발자도 더블클릭 한 번으로 명함을 만들 수 있도록 단독 실행 파일(exe)로 배포한다.

- **대표 = 핑크 / 직원 = 검정**(로고 포함) 디자인 자동 분기
- 입력 폼 + **실시간 미리보기** + 한 번에 PDF 저장
- 곡선(아웃라인)으로 박힌 명함 글자를 **Pretendard로 재구성**, **redaction으로 원본 개인정보 잔존 제거**
- 다크 테마(indigo-600 포인트) · 치이카와 아이콘

## 기술 스택
Python 3.12 · **PySide6**(GUI) · **PyMuPDF**(PDF 엔진) · **Pretendard**(폰트) · qdarktheme(테마) · **PyInstaller**(배포)

## 개발 실행
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## 사용법
1. **구분**(대표/직원) 선택
2. **이름·직급·영어명·별칭·M(휴대폰)·T(전화)·E(이메일)** 입력 — 빈 항목은 명함에서 자동 생략
3. 오른쪽 **미리보기**로 확인
4. **[PDF로 저장]** → `<exe 폴더>/HSecurity_명함/YYMMDD_이름.pdf` 에 자동 저장(다이얼로그 없음)

## 배포 exe 빌드
```powershell
pyinstaller main.py --onefile --windowed --name "HSecurity_명함생성기" `
  --icon assets/chiikawa.ico --add-data "assets;assets" `
  --paths src --hidden-import gui --hidden-import card_generator `
  --collect-all qdarktheme
```
→ `dist/HSecurity_명함생성기.exe` (Python·라이브러리·폰트·템플릿·아이콘 전부 내장, Windows 64bit 전용)

## 디렉터리 구조
```
main.py                      진입점(런처)
requirements.txt
src/
  card_generator.py          명함 생성 엔진 (CardInfo → PDF)
  gui.py                     PySide6 GUI (입력 폼·미리보기·저장·다크테마)
assets/
  fonts/Pretendard-*.ttf     본문/이름 폰트
  template/명함템플릿.pdf      명함 베이스 (로고·레이아웃만, 개인정보 제거됨)
  chiikawa.svg / chiikawa.ico 앱·exe 아이콘
docs/
  사용설명서.pdf              비개발자용 매뉴얼
  대표_템플릿.pdf / 직원_템플릿.pdf  샘플(더미값)
  progress.html              진행 기록
```

## 명함 편집 원리 · 제약
- 명함 글자는 PDF에 **곡선(아웃라인)** 으로 박혀 있어 텍스트로 직접 치환 불가 → 좌표·색·자간을 추출해 **Pretendard로 같은 자리에 다시 그림**
- 원본 텍스트는 **redaction(실제 콘텐츠 삭제)** 으로 제거 — 흰색 덮기와 달리 PDF 내부에 개인정보가 남지 않음
- 명함 규격 **90 × 50 mm** · 색상 핑크 `#EC008C` / 검정 `#000000`
- 원본 폰트를 PDF가 알려주지 않으므로(임베드 0) 자형은 Pretendard로 통일

## 배포 패키지
`dist/HSecurity_명함생성기.exe` + `docs/사용설명서.pdf` → `docs/HSecurity_명함생성기.zip` 으로 묶어 전달.
미서명 exe라 Windows SmartScreen "추가 정보 → 실행" 안내가 필요하다.

---
개발 · 제작 : 여중기
