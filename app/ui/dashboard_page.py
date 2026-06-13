from __future__ import annotations

from typing import List

from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from ..analytics import latest_measurement, pressure_status, summary
from ..models import Measurement
from ..widgets import GlassCard, PressureGauge, SectionTitle, TrendChart


class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()
        self.cards: List[GlassCard] = []
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(18)

        banner = QFrame()
        banner.setObjectName("topBanner")
        banner_layout = QHBoxLayout(banner)
        banner_layout.setContentsMargins(24, 22, 24, 22)
        banner_layout.setSpacing(18)

        banner_text_box = QVBoxLayout()
        banner_text_box.setSpacing(6)
        title = QLabel("💓  Розумний моніторинг АТ")
        title.setObjectName("bannerTitle")
        text = QLabel(
            "Фіксуйте вимірювання, стежте динаміку артеріального тиску та пульсу. "
            "Система автоматично зіставляє зміни з атмосферним тиском."
        )
        text.setObjectName("bannerText")
        text.setWordWrap(True)
        banner_text_box.addWidget(title)
        banner_text_box.addWidget(text)

        self.gauge = PressureGauge()
        banner_layout.addLayout(banner_text_box, 3)
        banner_layout.addWidget(self.gauge, 2)
        main.addWidget(banner)

        cards_layout = QGridLayout()
        cards_layout.setHorizontalSpacing(16)
        cards_layout.setVerticalSpacing(16)
        labels = [
            ("Середній тиск", "0/0", "За всіма записами"),
            ("Середній пульс", "0", "уд/хв"),
            ("Поточний стан", "Немає даних", "Останнє вимірювання"),
            ("Середній атм. тиск", "0", "мм рт. ст."),
        ]
        for i, (t, v, s) in enumerate(labels):
            card = GlassCard(t, v, s, accent_index=i)
            self.cards.append(card)
            cards_layout.addWidget(card, i // 2, i % 2)
        main.addLayout(cards_layout)

        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(16)

        chart_panel = QFrame()
        chart_panel.setObjectName("panel")
        cp_layout = QVBoxLayout(chart_panel)
        cp_layout.setContentsMargins(18, 16, 18, 18)
        cp_layout.setSpacing(14)
        cp_layout.addWidget(SectionTitle("Динаміка тиску та атмосферного тиску"))
        self.chart = TrendChart()
        cp_layout.addWidget(self.chart)

        info_panel = QFrame()
        info_panel.setObjectName("panel")
        info_layout = QVBoxLayout(info_panel)
        info_layout.setContentsMargins(18, 16, 18, 18)
        info_layout.setSpacing(12)
        info_layout.addWidget(SectionTitle("Короткий висновок"))
        self.latest_label = QLabel("Останній запис відсутній")
        self.latest_label.setWordWrap(True)
        self.latest_label.setStyleSheet("color:#475569; font-size:13px;")
        info_layout.addWidget(self.latest_label)

        self.trend_label = QLabel("📉  Тренд: немає даних")
        self.trend_label.setStyleSheet(
            "font-size:13px; font-weight:700; color:#4f46e5;"
            "background:#eef2ff; border-radius:8px; padding:6px 10px;"
        )
        info_layout.addWidget(self.trend_label)

        self.corr_label = QLabel("📌 Кореляція з атмосферним тиском: —")
        self.corr_label.setWordWrap(True)
        self.corr_label.setStyleSheet("color:#64748b; font-size:12px;")
        info_layout.addWidget(self.corr_label)
        info_layout.addStretch(1)

        bottom_layout.addWidget(chart_panel, 3)
        bottom_layout.addWidget(info_panel, 2)
        main.addLayout(bottom_layout)

    def refresh(self, measurements: List[Measurement]) -> None:
        stats = summary(measurements)
        latest = latest_measurement(measurements)
        self.cards[0].update_content(
            "Середній тиск",
            f"{int(stats['avg_systolic'])}/{int(stats['avg_diastolic'])}",
            "мм рт. ст. за наявними записами",
        )
        self.cards[1].update_content("Середній пульс", f"{int(stats['avg_pulse'])}", "уд/хв")
        self.cards[2].update_content(
            "Поточний стан", stats["latest_status"],
            f"Кількість записів: {stats['count']}",
        )
        avg_atm = f"{int(stats['avg_pressure'])}" if stats["avg_pressure"] else "—"
        self.cards[3].update_content(
            "Середній атм. тиск", avg_atm, "мм рт. ст. (за заповненими полями)"
        )

        if latest:
            self.gauge.set_value(
                latest.systolic, pressure_status(latest.systolic, latest.diastolic)
            )
            self.latest_label.setText(
                f"Останнє вимірювання: {latest.timestamp} · "
                f"{latest.systolic}/{latest.diastolic} мм рт. ст., "
                f"пульс {latest.pulse} уд/хв. Активність: {latest.activity_level.lower()}."
            )
        else:
            self.gauge.set_value(120, "Немає даних")
            self.latest_label.setText("Останній запис відсутній")

        self.trend_label.setText(f"📉  Тренд: {stats['pressure_trend']}")
        if stats["correlation"] is None:
            self.corr_label.setText("📌 Кореляція з атмосферним тиском: недостатньо даних")
        else:
            self.corr_label.setText(
                "📌 Кореляція з атм. тиском: "
                f"{stats['correlation']}"
            )

        last14 = measurements[-14:]
        self.chart.set_series(
            [m.systolic for m in last14],
            [m.diastolic for m in last14],
            [m.timestamp[5:10] for m in last14],
            [m.atmospheric_pressure for m in last14],
        )
