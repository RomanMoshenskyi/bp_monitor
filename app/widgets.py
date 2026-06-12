from __future__ import annotations

from typing import List, Optional, Sequence

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class GlassCard(QFrame):
    def __init__(self, title: str = "", value: str = "", subtitle: str = ""):
        super().__init__()
        self.setObjectName("glassCard")
        self.setMinimumHeight(120)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        effect = QGraphicsDropShadowEffect(self)
        effect.setBlurRadius(28)
        effect.setOffset(0, 8)
        effect.setColor(QColor(15, 30, 60, 38))
        self.setGraphicsEffect(effect)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(8)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("cardTitle")
        self.value_label = QLabel(value)
        self.value_label.setObjectName("cardValue")
        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setObjectName("cardSubtitle")
        self.subtitle_label.setWordWrap(True)

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.subtitle_label)
        layout.addStretch(1)

    def update_content(self, title: str, value: str, subtitle: str) -> None:
        self.title_label.setText(title)
        self.value_label.setText(value)
        self.subtitle_label.setText(subtitle)


class SectionTitle(QLabel):
    def __init__(self, text: str):
        super().__init__(text)
        self.setObjectName("sectionTitle")


class TrendChart(QWidget):
    """Графік АТ (ліва вісь) та атмосферного тиску (права вісь) для порівняння."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setMinimumHeight(280)
        self.systolic_data: List[float] = []
        self.diastolic_data: List[float] = []
        self.atmospheric_data: List[Optional[float]] = []
        self.labels: List[str] = []
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_series(
        self,
        systolic: Sequence[float],
        diastolic: Sequence[float],
        labels: Sequence[str],
        atmospheric: Sequence[Optional[float]] | None = None,
    ) -> None:
        self.systolic_data = list(systolic)
        self.diastolic_data = list(diastolic)
        self.labels = list(labels)
        if atmospheric is not None:
            self.atmospheric_data = list(atmospheric)
        else:
            self.atmospheric_data = []
        self.update()

    def _map_points(self, values: Sequence[float], rect: QRectF, vmin: float, vmax: float) -> List[QPointF]:
        if not values:
            return []
        step = rect.width() / max(len(values) - 1, 1)
        points: List[QPointF] = []
        span = max(vmax - vmin, 1)
        for i, value in enumerate(values):
            x = rect.left() + step * i
            y = rect.bottom() - ((value - vmin) / span) * rect.height()
            points.append(QPointF(x, y))
        return points

    def _valid_atmospheric(self) -> List[float]:
        return [float(v) for v in self.atmospheric_data if v is not None]

    def _draw_legend_item(
        self,
        painter: QPainter,
        right_x: int,
        y: int,
        color: str,
        text: str,
        dashed: bool = False,
    ) -> int:
        """Малює один пункт легенди, вирівняний по правому краю. Повертає X для наступного пункту ліворуч."""
        fm = painter.fontMetrics()
        text_w = fm.horizontalAdvance(text)
        line_len = 16
        gap = 6
        total_w = line_len + gap + text_w
        left_x = right_x - total_w
        pen = QPen(QColor(color), 3)
        if dashed:
            pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.drawLine(left_x, y, left_x + line_len, y)
        painter.setPen(QColor("#304050"))
        painter.drawText(left_x + line_len + gap, y + 4, text)
        return left_x - 14

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#ffffff"))

        outer = self.rect().adjusted(8, 8, -8, -8)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#f6fbff"))
        painter.drawRoundedRect(outer, 18, 18)

        has_atm = len(self._valid_atmospheric()) >= 2
        right_pad = 48 if has_atm else 24
        chart_rect = QRectF(
            outer.left() + 52,
            outer.top() + 28,
            outer.width() - 52 - right_pad,
            outer.height() - 68,
        )

        painter.setPen(QPen(QColor("#dce7f3"), 1))
        for i in range(5):
            y = int(chart_rect.top() + (chart_rect.height() / 4) * i)
            painter.drawLine(int(chart_rect.left()), y, int(chart_rect.right()), y)

        if not self.systolic_data and not self.diastolic_data:
            painter.setPen(QColor("#7e8da1"))
            painter.drawText(chart_rect, Qt.AlignmentFlag.AlignCenter, "Недостатньо даних для побудови графіка")
            return

        bp_values = self.systolic_data + self.diastolic_data
        bp_min = min(bp_values) - 5
        bp_max = max(bp_values) + 5

        font = QFont()
        font.setPointSize(9)
        painter.setFont(font)
        painter.setPen(QColor("#6d7c90"))

        for i in range(5):
            value = bp_max - ((bp_max - bp_min) / 4) * i
            y = int(chart_rect.top() + (chart_rect.height() / 4) * i + 4)
            painter.drawText(
                QRectF(outer.left() + 4, y - 10, 44, 20),
                Qt.AlignmentFlag.AlignRight,
                f"{int(value)}",
            )

        atm_values = self._valid_atmospheric()
        if has_atm:
            atm_min = min(atm_values) - 3
            atm_max = max(atm_values) + 3
            painter.setPen(QColor("#a67c52"))
            for i in range(5):
                value = atm_max - ((atm_max - atm_min) / 4) * i
                y = int(chart_rect.top() + (chart_rect.height() / 4) * i + 4)
                painter.drawText(
                    QRectF(outer.right() - 44, y - 10, 40, 20),
                    Qt.AlignmentFlag.AlignLeft,
                    f"{int(value)}",
                )

        sys_points = self._map_points(self.systolic_data, chart_rect, bp_min, bp_max)
        dia_points = self._map_points(self.diastolic_data, chart_rect, bp_min, bp_max)

        def draw_series(
            points: Sequence[QPointF],
            line_color: str,
            fill_alpha: int = 20,
            dashed: bool = False,
            dot_radius: float = 4.2,
        ):
            if len(points) < 2:
                return
            pen = QPen(QColor(line_color), 3)
            if dashed:
                pen.setStyle(Qt.PenStyle.DashLine)
            path = QPainterPath(points[0])
            for p in points[1:]:
                path.lineTo(p)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)

            if not dashed:
                fill = QPainterPath(points[0])
                for p in points[1:]:
                    fill.lineTo(p)
                fill.lineTo(points[-1].x(), chart_rect.bottom())
                fill.lineTo(points[0].x(), chart_rect.bottom())
                fill.closeSubpath()
                color = QColor(line_color)
                color.setAlpha(fill_alpha)
                painter.fillPath(fill, color)

            painter.setBrush(QColor(line_color))
            painter.setPen(Qt.PenStyle.NoPen)
            for p in points:
                painter.drawEllipse(p, dot_radius, dot_radius)

        draw_series(sys_points, "#2f7cf6", 28)
        draw_series(dia_points, "#4ecdc4", 18)

        if has_atm and len(self.atmospheric_data) == len(self.systolic_data):
            atm_min = min(atm_values) - 3
            atm_max = max(atm_values) + 3
            atm_points: List[QPointF] = []
            step = chart_rect.width() / max(len(self.atmospheric_data) - 1, 1)
            span = max(atm_max - atm_min, 1)
            for i, value in enumerate(self.atmospheric_data):
                if value is None:
                    continue
                x = chart_rect.left() + step * i
                y = chart_rect.bottom() - ((float(value) - atm_min) / span) * chart_rect.height()
                atm_points.append(QPointF(x, y))
            draw_series(atm_points, "#e67e22", dashed=True, dot_radius=3.5)

        painter.setPen(QColor("#6d7c90"))
        max_labels = 6
        show_indices = list(range(len(self.labels)))
        if len(show_indices) > max_labels:
            step = max(1, len(show_indices) // max_labels)
            show_indices = list(range(0, len(self.labels), step))[:max_labels]
            if len(self.labels) - 1 not in show_indices:
                show_indices.append(len(self.labels) - 1)
        for i in show_indices:
            x = chart_rect.left() + (chart_rect.width() / max(len(self.labels) - 1, 1)) * i
            painter.drawText(
                QRectF(x - 30, chart_rect.bottom() + 8, 60, 18),
                Qt.AlignmentFlag.AlignHCenter,
                self.labels[i],
            )

        # Легенда справа: ~50 px від правого краю віджета графіка
        legend_y = int(chart_rect.top()) - 6
        legend_right = int(outer.right()) - 50
        cursor_x = legend_right
        if has_atm:
            cursor_x = self._draw_legend_item(painter, cursor_x, legend_y, "#e67e22", "Атм. тиск", dashed=True)
        cursor_x = self._draw_legend_item(painter, cursor_x, legend_y, "#4ecdc4", "Діастолічний")
        self._draw_legend_item(painter, cursor_x, legend_y, "#2f7cf6", "Систолічний")


class PressureGauge(QWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.value = 120
        self.label = "Норма"
        self.setMinimumSize(220, 180)

    def set_value(self, value: int, label: str):
        self.value = value
        self.label = label
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#ffffff"))

        outer = self.rect().adjusted(10, 10, -10, -10)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#f6fbff"))
        painter.drawRoundedRect(outer, 18, 18)

        center = outer.center()
        radius = min(outer.width(), outer.height()) * 0.34
        arc_rect = QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2)

        pen_bg = QPen(QColor("#dbe8f7"), 12)
        painter.setPen(pen_bg)
        painter.drawArc(arc_rect, 30 * 16, 120 * 16)

        ratio = max(0.0, min((self.value - 80) / 80, 1.0))
        span = int(120 * ratio * 16)
        color = QColor("#4ecdc4") if self.value < 130 else QColor("#ff9f43") if self.value < 140 else QColor("#ff5c7c")
        painter.setPen(QPen(color, 12))
        painter.drawArc(arc_rect, 30 * 16, span)

        painter.setPen(QColor("#1f3349"))
        font = QFont()
        font.setPointSize(24)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(QRectF(outer.left(), center.y() - 6, outer.width(), 34), Qt.AlignmentFlag.AlignHCenter, str(self.value))

        font.setPointSize(10)
        font.setBold(False)
        painter.setFont(font)
        painter.setPen(QColor("#6a7a92"))
        painter.drawText(QRectF(outer.left(), center.y() + 28, outer.width(), 18), Qt.AlignmentFlag.AlignHCenter, "Систолічний тиск")
        painter.drawText(QRectF(outer.left(), outer.bottom() - 32, outer.width(), 20), Qt.AlignmentFlag.AlignHCenter, self.label)
