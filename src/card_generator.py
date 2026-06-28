# -*- coding: utf-8 -*-
"""H SECURITY 명함 생성 엔진.

명함템플릿.pdf(로고·레이아웃 베이스)에서 텍스트 영역을 비우고
입력값(CardInfo)으로 이름·직급·영문명·연락처를 다시 그린다.

- 대표(is_ceo=True): 핑크(#EC008C) 유지
- 직원(is_ceo=False): 로고 포함 전체 검정(#000000)

좌표·폰트·크기·정렬은 PoC로 확정된 값을 사용한다.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF


def _resource_base() -> Path:
    """에셋 루트. PyInstaller로 묶이면(frozen) 임시 추출 경로(_MEIPASS)를 쓴다."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent.parent


# ── 에셋 경로 ─────────────────────────────────────────────
_ASSETS = _resource_base() / "assets"
_FONTS = _ASSETS / "fonts"
_TEMPLATE = _ASSETS / "template" / "명함템플릿.pdf"

_REG = str(_FONTS / "Pretendard-Regular.ttf")
_BD = str(_FONTS / "Pretendard-Bold.ttf")
_SB = str(_FONTS / "Pretendard-SemiBold.ttf")
_MED = str(_FONTS / "Pretendard-Medium.ttf")

# ── 색상 ─────────────────────────────────────────────────
PINK = (0.9260547757148743, 0.0, 0.548302412033081)  # #EC008C (CEO)
BLACK = (0.0, 0.0, 0.0)                               # 직원
_WHITE = (1.0, 1.0, 1.0)

# 원본 핑크는 CMYK 마젠타(0 1 0 0 k)로 인코딩됨 → 검정(0 0 0 1 k)
_CMYK_MAGENTA = b"0 1 0 0 k"
_CMYK_BLACK = b"0 0 0 1 k"

# ── 레이아웃 상수 (PoC 확정값, 단위 pt) ──────────────────
_NAME_X0 = 29.0       # 첫 글자 중심 x
_NAME_PITCH = 20.0    # 글자 중심 간격
_NAME_BY = 77.0       # 이름 baseline
_NAME_SZ = 14.7       # 원본 손성흔 글자높이(~12.7pt)에 맞춘 크기
_TITLE_SZ = 9.5
_TITLE_GAP = 11.0     # 이름 끝 ~ 직급 간격
_ENG_X = 23.0
_ENG_BY = 91.0        # 한글이름(77)과 줄간격 14
_ENG_SZ = 9.3
_LABEL_SZ = 9.0       # M/T/E 라벨
_VALUE_SZ = 7.8       # 번호/이메일
_M_LABEL_X = 23.0
_M_VALUE_X = 35.0
_T_LABEL_X = 105.0    # M 우측
_T_VALUE_X = 114.78
_E_LABEL_X = 24.33    # M 중심에 맞춘 가운데 정렬
_E_VALUE_X = 35.0
_ROW1_BY = 113.0      # M / T 줄
_ROW2_BY = 127.0      # E 줄
_VALUE_BY1 = 112.5
_VALUE_BY2 = 126.5

# 원본 텍스트(이름·직급·영문·연락처·인스타)를 덮는 흰 박스
_COVERS = [
    (21, 62, 102, 79),    # 이름 + 직급
    (22, 81, 185, 92),    # 영문명
    (21, 106, 185, 115),  # M / E(원본 우측) 줄
    (21, 117, 178, 128),  # T / 인스타 줄
]


@dataclass
class CardInfo:
    """명함 한 장의 입력 정보."""
    is_ceo: bool = False   # True=대표(핑크), False=직원(검정)
    name_kr: str = ""      # 직원명(한글)
    title: str = ""        # 직급
    name_en: str = ""      # 영어이름 (직접 입력)
    alias: str = ""        # 별칭 → (alias)
    mobile: str = ""       # M
    tel: str = ""          # T
    email: str = ""        # E


def _english_line(info: CardInfo) -> str:
    name = info.name_en.strip()
    alias = info.alias.strip()
    if alias:
        return f"{name} ({alias})" if name else f"({alias})"
    return name


def generate(info: CardInfo) -> fitz.Document:
    """CardInfo로 명함 PDF 문서를 생성해 반환(닫지 않음)."""
    color = PINK if info.is_ceo else BLACK
    doc = fitz.open(str(_TEMPLATE))
    page = doc[0]

    # 직원: 로고(원본 핑크) 포함 모든 벡터를 검정으로
    if not info.is_ceo:
        for xref in page.get_contents():
            s = doc.xref_stream(xref)
            doc.update_stream(xref, s.replace(_CMYK_MAGENTA, _CMYK_BLACK))

    # 원본 텍스트 영역 비우기 — redaction으로 벡터를 실제 제거(개인정보 잔존 방지).
    # 흰색 덮기는 시각적으로만 가려 데이터가 남으므로 사용하지 않는다.
    for box in _COVERS:
        page.add_redact_annot(fitz.Rect(*box), fill=_WHITE)
    page.apply_redactions(graphics=fitz.PDF_REDACT_LINE_ART_REMOVE_IF_TOUCHED)

    sb = fitz.Font(fontfile=_SB)

    # 이름 (글자별 중심 배치, 자간 유지)
    name = info.name_kr.strip()
    last_cx = _NAME_X0
    for i, ch in enumerate(name):
        cx = _NAME_X0 + i * _NAME_PITCH
        tw = sb.text_length(ch, _NAME_SZ)
        page.insert_text((cx - tw / 2, _NAME_BY), ch,
                         fontfile=_SB, fontname="sb", fontsize=_NAME_SZ, color=color)
        last_cx = cx

    # 직급 (이름 뒤)
    if info.title.strip():
        adv = sb.text_length("가", _NAME_SZ)
        title_x = last_cx + adv / 2 + _TITLE_GAP
        page.insert_text((title_x, 76.5), info.title.strip(),
                         fontfile=_MED, fontname="med", fontsize=_TITLE_SZ, color=color)

    # 영문명 + 별칭
    eng = _english_line(info)
    if eng:
        page.insert_text((_ENG_X, _ENG_BY), eng,
                         fontfile=_REG, fontname="reg", fontsize=_ENG_SZ, color=color)

    # 연락처 (빈 항목은 생략)
    if info.mobile.strip():
        page.insert_text((_M_LABEL_X, _ROW1_BY), "M",
                         fontfile=_BD, fontname="bd", fontsize=_LABEL_SZ, color=color)
        page.insert_text((_M_VALUE_X, _VALUE_BY1), info.mobile.strip(),
                         fontfile=_REG, fontname="reg", fontsize=_VALUE_SZ, color=color)
    if info.tel.strip():
        page.insert_text((_T_LABEL_X, _ROW1_BY), "T",
                         fontfile=_BD, fontname="bd", fontsize=_LABEL_SZ, color=color)
        page.insert_text((_T_VALUE_X, _VALUE_BY1), info.tel.strip(),
                         fontfile=_REG, fontname="reg", fontsize=_VALUE_SZ, color=color)
    if info.email.strip():
        page.insert_text((_E_LABEL_X, _ROW2_BY), "E",
                         fontfile=_BD, fontname="bd", fontsize=_LABEL_SZ, color=color)
        page.insert_text((_E_VALUE_X, _VALUE_BY2), info.email.strip(),
                         fontfile=_REG, fontname="reg", fontsize=_VALUE_SZ, color=color)

    return doc


def save_pdf(info: CardInfo, path: str | Path) -> None:
    """명함 PDF를 파일로 저장(폰트 서브셋으로 용량 최소화)."""
    doc = generate(info)
    doc.subset_fonts()
    doc.save(str(path), garbage=4, deflate=True)
    doc.close()


def render_png(info: CardInfo, scale: float = 4.0) -> bytes:
    """미리보기용 PNG 바이트 반환."""
    doc = generate(info)
    pix = doc[0].get_pixmap(matrix=fitz.Matrix(scale, scale))
    data = pix.tobytes("png")
    doc.close()
    return data
