from __future__ import annotations

from typing import List, Optional

from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..analytics import filter_by_days, generate_recommendations, summary
from ..models import Measurement
from ..widgets import GlassCard, SectionTitle, TrendChart


class AnalyticsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.period_box = QComboBox()
        self.period_box.addItems(
            ["Останні 7 днів", "Останні 14 днів", "Останні 30 днів", "Усі записи"]
        )
        self.period_box.currentIndexChanged.connect(lambda *_: self._emit_refresh())
        self.refresh_handler: Optional[callable] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        top = QHBoxLayout()
        top.addWidget(SectionTitle("📈  Поглиблена аналітика"))
        top.addStretch(1)
        period_lbl = QLabel("Період аналізу:")
        period_lbl.setStyleSheet("color:#64748b; font-weight:600; font-size:12px;")
        self.period_box.setFixedWidth(160)
        top.addWidget(period_lbl)
        top.addWidget(self.period_box)
        layout.addLayout(top)

        cards = QGridLayout()
        cards.setHorizontalSpacing(16)
        cards.setVerticalSpacing(16)
        self.metric_cards = [
            GlassCard("📊 Записів", "0", "у періоді", accent_index=0),
            GlassCard("⬆ Макс. систолічний", "0", "мм рт. ст.", accent_index=3),
            GlassCard("⬇ Мін. діастолічний", "0", "мм рт. ст.", accent_index=2),
            GlassCard("💓 Пульс", "0", "уд/хв середній", accent_index=1),
        ]
        for i, card in enumerate(self.metric_cards):
            cards.addWidget(card, 0, i)
        layout.addLayout(cards)

        center = QHBoxLayout()
        center.setSpacing(16)

        chart_panel = QFrame()
        chart_panel.setObjectName("panel")
        chart_layout = QVBoxLayout(chart_panel)
        chart_layout.setContentsMargins(18, 16, 18, 18)
        chart_layout.setSpacing(14)
        chart_layout.addWidget(SectionTitle("Тренд: АТ та атмосферний тиск"))
        self.chart = TrendChart()
        chart_layout.addWidget(self.chart)

        rec_panel = QFrame()
        rec_panel.setObjectName("panel")
        rec_layout = QVBoxLayout(rec_panel)
        rec_layout.setContentsMargins(18, 16, 18, 18)
        rec_layout.setSpacing(14)
        rec_layout.addWidget(SectionTitle("Аналітичні висновки"))
        self.recommendations = QTextEdit()
        self.recommendations.setReadOnly(True)
        self.recommendations.setMinimumHeight(280)
        self.recommendations.setStyleSheet(
            "QTextEdit { background:#fafaff; border:1.5px solid #e0e7ff;"
            " border-radius:12px; padding:12px; font-size:13px; line-height:1.6; color:#374151; }"
        )
        rec_layout.addWidget(self.recommendations)

        center.addWidget(chart_panel, 3)
        center.addWidget(rec_panel, 2)
        layout.addLayout(center)

        bottom = QFrame()
        bottom.setObjectName("panel")
        bottom_layout = QVBoxLayout(bottom)
        bottom_layout.setContentsMargins(18, 16, 18, 18)
        bottom_layout.setSpacing(12)
        bottom_layout.addWidget(
            SectionTitle("Деталізований висновок щодо атмосферного тиску")
        )
        self.atm_label = QLabel("Недостатньо даних")
        self.atm_label.setWordWrap(True)
        self.atm_label.setStyleSheet("color:#475569; font-size:13px;")
        bottom_layout.addWidget(self.atm_label)
        layout.addWidget(bottom)

        self._measurements: List[Measurement] = []

    def _emit_refresh(self) -> None:
        if self.refresh_handler:
            self.refresh_handler()

    def current_days(self) -> Optional[int]:
        mapping = {0: 7, 1: 14, 2: 30, 3: None}
        return mapping[self.period_box.currentIndex()]

    def refresh(self, measurements: List[Measurement]) -> None:
        self._measurements = measurements
        days = self.current_days()
        data = filter_by_days(measurements, days) if days else measurements
        stats = summary(data)
        count = len(data)
        max_sys = max((m.systolic for m in data), default=0)
        min_dia = min((m.diastolic for m in data), default=0)
        avg_pulse = round(sum(m.pulse for m in data) / count, 1) if count else 0

        self.metric_cards[0].update_content("Записів", str(count), "у вибраному періоді")
        self.metric_cards[1].update_content("Макс. систолічний", str(max_sys), "мм рт. ст.")
        self.metric_cards[2].update_content("Мін. діастолічний", str(min_dia), "мм рт. ст.")
        self.metric_cards[3].update_content(
            "Середній пульс", str(int(avg_pulse) if count else 0), "уд/хв"
        )

        self.chart.set_series(
            [m.systolic for m in data],
            [m.diastolic for m in data],
            [m.timestamp[5:10] for m in data],
            [m.atmospheric_pressure for m in data],
        )

        text = "\n\n".join(f"• {item}" for item in generate_recommendations(data))
        self.recommendations.setPlainText(text)

        if stats["correlation"] is None:
            self.atm_label.setText(
                "Поле атмосферного тиску у системі є допоміжним. "
                "Для статистичного співставлення бажано накопичити більше записів "
                "із заповненим атмосферним тиском."
            )
        else:
            corr = stats["correlation"]
            interpretation = (
                "Спостерігається виражений зв'язок між змінами систолічного і атмосферного тиску."
                if abs(corr) >= 0.55
                else "Зв'язок між атмосферним і систолічним тиском є слабким або помірним."
            )
            self.atm_label.setText(
                f"Орієнтовний коефіцієнт кореляції становить {corr}. {interpretation} "
                "Отриманий результат не замінює медичної консультації, але може бути "
                "використаний для індивідуального самоспостереження."
            )
