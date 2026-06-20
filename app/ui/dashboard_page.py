"""PulseView — Premium patient dashboard."""
from __future__ import annotations

from typing import List

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget,
)

from ..analytics import latest_measurement, pressure_status, summary
from ..models import Measurement
from ..widgets import GlassCard, PageHeader, PressureGauge, SectionTitle, TrendChart


class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()
        self.cards: List[GlassCard] = []
        self._build()

    def _build(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(24)

        # Header
        main.addWidget(PageHeader("Огляд", "Контроль ключових показників і короткий аналітичний висновок"))

        # Banner
        banner = QFrame()
        banner.setObjectName("topBanner")
        bl = QHBoxLayout(banner)
        bl.setContentsMargins(20, 20, 20, 20)
        bl.setSpacing(16)
        txt = QVBoxLayout()
        txt.setSpacing(6)
        title = QLabel("Розумний моніторинг АТ")
        title.setObjectName("bannerTitle")
        title.setFont(QFont("Inter", 16, QFont.Weight.ExtraBold))
        desc = QLabel(
            "Фіксуйте вимірювання, стежте за динамікою артеріального тиску та пульсу. "
            "Система автоматично зіставляє зміни з атмосферним тиском."
        )
        desc.setObjectName("bannerText")
        desc.setWordWrap(True)
        txt.addWidget(title); txt.addWidget(desc)
        self.gauge = PressureGauge()
        bl.addLayout(txt, 1)
        bl.addWidget(self.gauge, 0)
        main.addWidget(banner)

        # Stat cards
        grid = QGridLayout()
        grid.setHorizontalSpacing(12); grid.setVerticalSpacing(12)
        labels = [
            ("Середній тиск", "0/0", "За всіма записами"),
            ("Середній пульс", "0", "уд/хв"),
            ("Поточний стан", "Немає даних", "Останнє вимірювання"),
            ("Середній атм. тиск", "0", "мм рт. ст."),
        ]
        for i, (t, v, s) in enumerate(labels):
            card = GlassCard(t, v, s, accent_index=i)
            self.cards.append(card)
            grid.addWidget(card, i // 2, i % 2)
        main.addLayout(grid)

        # Bottom row: chart + summary
        bot = QHBoxLayout(); bot.setSpacing(16)
        chart_p = QFrame(); chart_p.setObjectName("panel")
        cp = QVBoxLayout(chart_p); cp.setContentsMargins(16, 16, 16, 16); cp.setSpacing(12)
        cp.addWidget(SectionTitle("Динаміка тиску та атмосферного тиску"))
        self.chart = TrendChart(); cp.addWidget(self.chart)

        info_p = QFrame(); info_p.setObjectName("panel")
        ip = QVBoxLayout(info_p); ip.setContentsMargins(16, 16, 16, 16); ip.setSpacing(10)
        ip.addWidget(SectionTitle("Короткий висновок"))
        self.latest_label = QLabel("Останній запис відсутній")
        self.latest_label.setWordWrap(True)
        self.latest_label.setStyleSheet(f"color:{Tokens.N6};font-size:13px;font-weight:500;")
        ip.addWidget(self.latest_label)

        self.trend_label = QLabel("Тренд: немає даних")
        self.trend_label.setStyleSheet(
            f"font-size:13px;font-weight:700;color:#4f46e5;"
            f"background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #eef2ff,stop:1 #e0e7ff);"
            f"border:1px solid rgba(99,102,241,0.1);border-radius:10px;padding:8px 12px;"
        )
        ip.addWidget(self.trend_label)
        self.corr_label = QLabel("Кореляція з атмосферним тиском: —")
        self.corr_label.setWordWrap(True)
        self.corr_label.setStyleSheet(f"color:#64748b;font-size:12px;font-weight:500;")
        ip.addWidget(self.corr_label); ip.addStretch(1)

        bot.addWidget(chart_p, 2); bot.addWidget(info_p, 1)
        main.addLayout(bot)

    def refresh(self, measurements: List[Measurement]) -> None:
        stats = summary(measurements)
        latest = latest_measurement(measurements)
        self.cards[0].update_content(
            "Середній тиск",
            f"{int(stats['avg_systolic'])}/{int(stats['avg_diastolic'])}",
            "мм рт. ст. за наявними записами",
        )
        self.cards[1].update_content("Середній пульс", f"{int(stats['avg_pulse'])}", "уд/хв")
        self.cards[2].update_content("Поточний стан", stats["latest_status"], f"Кількість записів: {stats['count']}")
        avg_atm = f"{int(stats['avg_pressure'])}" if stats["avg_pressure"] else "—"
        self.cards[3].update_content("Середній атм. тиск", avg_atm, "мм рт. ст. (за заповненими полями)")

        if latest:
            self.gauge.set_value(latest.systolic, pressure_status(latest.systolic, latest.diastolic))
            self.latest_label.setText(
                f"Останнє вимірювання: {latest.timestamp} - "
                f"{latest.systolic}/{latest.diastolic} мм рт. ст., пульс {latest.pulse} уд/хв. "
                f"Активність: {latest.activity_level.lower()}."
            )
        else:
            self.gauge.set_value(120, "Немає даних")
            self.latest_label.setText("Останній запис відсутній")

        self.trend_label.setText(f"Тренд: {stats['pressure_trend']}")
        if stats["correlation"] is None:
            self.corr_label.setText("Кореляція з атмосферним тиском: недостатньо даних")
        else:
            self.corr_label.setText(f"Кореляція з атм. тиском: {stats['correlation']}")

        last14 = measurements[-14:]
        self.chart.set_series(
            [m.systolic for m in last14],
            [m.diastolic for m in last14],
            [m.timestamp[5:10] for m in last14],
            [m.atmospheric_pressure for m in last14],
        )


# Local alias for Tokens used in inline stylesheets
class Tokens:
    N6 = "#475569"
