# -*- coding: utf-8 -*-
"""H SECURITY 명함 생성기 — PySide6 GUI.

좌측 입력 폼 → 우측 실시간 미리보기 → PDF 저장.
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QFontDatabase, QIcon, QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QComboBox, QFormLayout, QFrame,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton,
    QRadioButton, QVBoxLayout, QWidget,
)

import qdarktheme

import card_generator as cg

# 다크 테마 위에 얹는 포인트색 — trading_info 주색상 indigo-600 계열.
# (QSS는 color-mix()/var() 미지원 → indigo-600/500/700/400을 hex로 변환해 사용.
#  라디오 선택 표시에는 색을 입히지 않음 — qdarktheme 기본 사용)
_ACCENT_QSS = """
QPushButton { background-color:#4f46e5; color:#ffffff; border:none; border-radius:5px; padding:9px 14px; font-weight:bold; }
QPushButton:hover { background-color:#6366f1; }
QPushButton:pressed { background-color:#4338ca; }
QLineEdit:focus, QComboBox:focus { border:1px solid #4f46e5; }
QGroupBox::title { color:#818cf8; font-weight:bold; }
"""

_PREVIEW_W = 540  # 미리보기 표시 폭(px)
_ICON = cg._ASSETS / "chiikawa.svg"          # 파비콘 (assets에 번들)


def _output_base() -> Path:
    """PDF 저장 기준 폴더. exe(frozen)면 exe가 놓인 폴더, 개발 시엔 프로젝트 루트."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent
_EMAIL_DOMAINS = [
    "gmail.com", "naver.com", "daum.net", "nate.com",
    "kakao.com", "hanmail.net", "outlook.com", "icloud.com",
]


def _phone_inputs():
    """전화번호 3칸 위젯 + (e1, e2, e3) 반환."""
    w = QWidget()
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    e1, e2, e3 = QLineEdit(), QLineEdit(), QLineEdit()
    for e, ml, ph, wd in ((e1, 3, "010", 48), (e2, 4, "0000", 58), (e3, 4, "0000", 58)):
        e.setMaxLength(ml)
        e.setPlaceholderText(ph)
        e.setFixedWidth(wd)
        e.setAlignment(Qt.AlignCenter)
    lay.addWidget(e1)
    lay.addWidget(QLabel("-"))
    lay.addWidget(e2)
    lay.addWidget(QLabel("-"))
    lay.addWidget(e3)
    lay.addStretch()
    return w, (e1, e2, e3)


class CardApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("H SECURITY 명함 생성기")
        if _ICON.exists():
            self.setWindowIcon(QIcon(str(_ICON)))
        self.setMinimumWidth(960)

        # ── 구분 (대표 / 직원) ─────────────────────
        self.rb_ceo = QRadioButton("대표")
        self.rb_staff = QRadioButton("직원")
        self.rb_staff.setChecked(True)
        self.role_group = QButtonGroup(self)
        self.role_group.addButton(self.rb_ceo)
        self.role_group.addButton(self.rb_staff)
        role_box = QGroupBox("구분")
        role_l = QHBoxLayout()
        role_l.addWidget(self.rb_ceo)
        role_l.addWidget(self.rb_staff)
        role_l.addStretch()
        role_box.setLayout(role_l)

        # ── 텍스트 입력 ────────────────────────────
        self.in_name = QLineEdit()
        self.in_title = QLineEdit()
        self.in_eng = QLineEdit()
        self.in_alias = QLineEdit()
        self.in_name.setPlaceholderText("ex) 홍길동")
        self.in_title.setPlaceholderText("ex) 실장")
        self.in_eng.setPlaceholderText("ex) GilDong Hong")
        self.in_alias.setPlaceholderText("ex) Abc (없으면 비움)")

        # ── 전화 3칸 (M / T) ──────────────────────
        m_w, self.m_parts = _phone_inputs()
        t_w, self.t_parts = _phone_inputs()

        # ── 이메일 (아이디 + 도메인 셀렉트) ────────
        email_w = QWidget()
        email_l = QHBoxLayout(email_w)
        email_l.setContentsMargins(0, 0, 0, 0)
        self.email_id = QLineEdit()
        self.email_id.setPlaceholderText("아이디")
        self.email_domain = QComboBox()  # 선택 전용 (직접 수정 불가)
        self.email_domain.addItems(_EMAIL_DOMAINS + ["직접 입력"])
        self.email_custom = QLineEdit()
        self.email_custom.setPlaceholderText("도메인 입력")
        self.email_custom.setVisible(False)  # "직접 입력" 선택 시에만 표시
        email_l.addWidget(self.email_id, 1)
        email_l.addWidget(QLabel("@"))
        email_l.addWidget(self.email_domain)
        email_l.addWidget(self.email_custom, 1)

        form = QFormLayout()
        form.addRow("이름", self.in_name)
        form.addRow("직급", self.in_title)
        form.addRow("영어명", self.in_eng)
        form.addRow("별칭", self.in_alias)
        form.addRow("M (휴대폰)", m_w)
        form.addRow("T (전화)", t_w)
        form.addRow("E (이메일)", email_w)
        form_box = QGroupBox("명함 정보")
        form_box.setLayout(form)

        self.btn_save = QPushButton("PDF로 저장")
        self.btn_save.setMinimumHeight(38)
        self.btn_save.clicked.connect(self.save)

        left = QVBoxLayout()
        left.addWidget(role_box)
        left.addWidget(form_box)
        left.addStretch()
        left.addWidget(self.btn_save)
        left_w = QWidget()
        left_w.setLayout(left)
        left_w.setFixedWidth(380)

        # ── 미리보기 ──────────────────────────────
        self.preview = QLabel("미리보기")
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumSize(_PREVIEW_W, int(_PREVIEW_W * 150.2 / 266.5))
        self.preview.setFrameShape(QFrame.Box)
        self.preview.setStyleSheet("background:#e9e9ee; color:#888; border:1px solid #ccc;")
        prev_box = QGroupBox("미리보기")
        prev_l = QVBoxLayout()
        prev_l.addWidget(self.preview)
        prev_l.addStretch()
        prev_box.setLayout(prev_l)

        root = QHBoxLayout()
        root.addWidget(left_w)
        root.addWidget(prev_box, 1)
        self.setLayout(root)

        # ── 실시간 미리보기 (디바운스) ────────────
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(150)
        self._timer.timeout.connect(self.update_preview)

        edits = [self.in_name, self.in_title, self.in_eng, self.in_alias,
                 self.email_id, *self.m_parts, *self.t_parts]
        for w in edits:
            w.textChanged.connect(self._schedule)
        self.email_domain.currentTextChanged.connect(self._on_domain_changed)
        self.email_custom.textChanged.connect(self._schedule)
        self.rb_ceo.toggled.connect(self._schedule)

        self.update_preview()

    # ── 로직 ──────────────────────────────────────
    @staticmethod
    def _join_phone(parts) -> str:
        vals = [p.text().strip() for p in parts]
        return "-".join(vals) if all(vals) else ""

    def _on_domain_changed(self, text: str):
        self.email_custom.setVisible(text == "직접 입력")
        self._schedule()

    def _email(self) -> str:
        eid = self.email_id.text().strip()
        if self.email_domain.currentText() == "직접 입력":
            dom = self.email_custom.text().strip()
        else:
            dom = self.email_domain.currentText().strip()
        return f"{eid}@{dom}" if eid and dom else ""

    def collect(self) -> cg.CardInfo:
        return cg.CardInfo(
            is_ceo=self.rb_ceo.isChecked(),
            name_kr=self.in_name.text(),
            title=self.in_title.text(),
            name_en=self.in_eng.text(),
            alias=self.in_alias.text(),
            mobile=self._join_phone(self.m_parts),
            tel=self._join_phone(self.t_parts),
            email=self._email(),
        )

    def _schedule(self):
        self._timer.start()

    def update_preview(self):
        try:
            png = cg.render_png(self.collect(), scale=4.0)
            img = QImage.fromData(png, "PNG")
            pix = QPixmap.fromImage(img).scaledToWidth(_PREVIEW_W, Qt.SmoothTransformation)
            self.preview.setPixmap(pix)
        except Exception as e:  # noqa: BLE001
            self.preview.setText(f"미리보기 오류:\n{e}")

    def save(self):
        info = self.collect()
        if not info.name_kr.strip():
            QMessageBox.warning(self, "확인", "이름을 입력해 주세요.")
            return
        # exe가 놓인 폴더(개발 시 프로젝트 루트)/HSecurity_명함/<YYMMDD>_<이름>.pdf
        folder = _output_base() / "HSecurity_명함"
        folder.mkdir(parents=True, exist_ok=True)
        name = info.name_kr.strip().replace(" ", "_")
        path = folder / f"{datetime.now():%y%m%d}_{name}.pdf"
        try:
            cg.save_pdf(info, path)
            QMessageBox.information(self, "완료", f"저장되었습니다:\n{path}")
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self, "오류", f"저장 실패:\n{e}")


def _apply_theme(app: QApplication):
    """번들 Pretendard 폰트(한글) + 다크 테마 + 핑크 포인트."""
    fid = QFontDatabase.addApplicationFont(str(cg._ASSETS / "fonts" / "Pretendard-Regular.ttf"))
    fams = QFontDatabase.applicationFontFamilies(fid) if fid >= 0 else []
    fam = fams[0] if fams else "Malgun Gothic"
    qss = qdarktheme.load_stylesheet("dark")
    qss += f'\n* {{ font-family: "{fam}"; }}\n' + _ACCENT_QSS
    app.setStyleSheet(qss)
    app.setFont(QFont(fam, 10))


def main():
    app = QApplication(sys.argv)
    _apply_theme(app)
    if _ICON.exists():
        app.setWindowIcon(QIcon(str(_ICON)))
    win = CardApp()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
