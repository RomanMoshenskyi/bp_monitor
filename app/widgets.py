from __future__ import annotations

from typing import List, Optional, Sequence

from PyQt6.QtCore import (
    QEasingCurve, QPointF, QPropertyAnimation, QRectF, QSize,
    Qt, QTimer, pyqtProperty,
)
from PyQt6.QtGui import (
    QColor, QFont, QLinearGradient, QPainter, QPainterPath,
    QPen, QRadialGradient,
)
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class GlassCard(QFrame):
    """Premium animated stat card with hover glow and accent bar."""

    # accent colours per card index (cycled)
    ACCENTS = ["#6366f1", "#06b6d4", "#10b981", "#f59e0b"]

    def __init__(self, title: str = "", value: str = "", subtitle: str = "",
                 accent_index: int = 0):
        super().__init__()
        self.setObjectName("glassCard")
        self.setMinimumHeight(130)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._accent = self.ACCENTS[accent_index % len(self.ACCENTS)]
        self._glow_opacity: float = 0.0

        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(24)
        self._shadow.setOffset(0, 6)
        self._shadow.setColor(QColor(15, 20, 50, 30))
        self.setGraphicsEffect(self._shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(4)

        # accent dot + title row
        top_row = QHBoxLayout()
        top_row.setSpacing(8)
        self._dot = QLabel()
        self._dot.setFixedSize(10, 10)
        self._dot.setStyleSheet(
            f"background:{self._accent}; border-radius:5px;"
        )
        self.title_label = QLabel(title)
        self.title_label.setObjectName("cardTitle")
        top_row.addWidget(self._dot)
        top_row.addWidget(self.title_label, 1)
        layout.addLayout(top_row)

        self.value_label = QLabel(value)
        self.value_label.setObjectName("cardValue")
        layout.addWidget(self.value_label)

        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setObjectName("cardSubtitle")
        self.subtitle_label.setWordWrap(True)
        layout.addWidget(self.subtitle_label)
        layout.addStretch(1)

        # hover animation
        self._anim = QPropertyAnimation(self, b"glowOpacity", self)
        self._anim.setDuration(200)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    # ── pyqtProperty for animation ─────────────────────────────────────────
    def _get_glow(self) -> float:
        return self._glow_opacity

    def _set_glow(self, v: float) -> None:
        self._glow_opacity = v
        blur = int(24 + v * 20)
        alpha = int(30 + v * 40)
        self._shadow.setBlurRadius(blur)
        self._shadow.setColor(QColor(
            *QColor(self._accent).getRgb()[:3], alpha
        ))

    glowOpacity = pyqtProperty(float, _get_glow, _set_glow)

    def enterEvent(self, e):
        self._anim.stop()
        self._anim.setStartValue(self._glow_opacity)
        self._anim.setEndValue(1.0)
        self._anim.start()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._anim.stop()
        self._anim.setStartValue(self._glow_opacity)
        self._anim.setEndValue(0.0)
        self._anim.start()
        super().leaveEvent(e)

    def paintEvent(self, e):
        super().paintEvent(e)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        # left accent bar
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(self._accent))
        p.drawRoundedRect(0, 20, 4, self.height() - 40, 2, 2)

    def update_content(self, title: str, value: str, subtitle: str) -> None:
        self.title_label.setText(title)
        self.value_label.setText(value)
        self.subtitle_label.setText(subtitle)


class StatusBadge(QLabel):
    """Coloured pill badge for BP status."""
    _COLORS = {
        "normal":  ("#d1fae5", "#059669"),
        "висока":  ("#fee2e2", "#dc2626"),
        "низький": ("#fef3c7", "#d97706"),
        "висок":   ("#fee2e2", "#dc2626"),
        "норм":    ("#d1fae5", "#059669"),
        "немає":   ("#f3f4f6", "#6b7280"),
    }

    def __init__(self, text: str = ""):
        super().__init__(text)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(26)
        self.update_status(text)

    def update_status(self, text: str) -> None:
        self.setText(text)
        key = next((k for k in self._COLORS if k in text.lower()), "немає")
        bg, fg = self._COLORS[key]
        self.setStyleSheet(
            f"background:{bg}; color:{fg}; border-radius:13px;"
            f"padding:2px 12px; font-size:12px; font-weight:700;"
        )


class SectionTitle(QLabel):
    def __init__(self, text: str):
        super().__init__(text)
        self.setObjectName("sectionTitle")


class TrendChart(QWidget):
    """Premium bezier-curve chart with gradient fills and dual Y-axes."""

    _SYS_COLOR   = "#6366f1"
    _DIA_COLOR   = "#06b6d4"
    _ATM_COLOR   = "#f59e0b"
    _GRID_COLOR  = "#e8edf5"
    _BG_COLOR    = "#f8faff"
    _AXIS_COLOR  = "#94a3b8"

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setMinimumHeight(300)
        self.systolic_data:    List[float]          = []
        self.diastolic_data:   List[float]          = []
        self.atmospheric_data: List[Optional[float]] = []
        self.labels:           List[str]            = []
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_series(
        self,
        systolic:    Sequence[float],
        diastolic:   Sequence[float],
        labels:      Sequence[str],
        atmospheric: Sequence[Optional[float]] | None = None,
    ) -> None:
        self.systolic_data    = list(systolic)
        self.diastolic_data   = list(diastolic)
        self.labels           = list(labels)
        self.atmospheric_data = list(atmospheric) if atmospheric is not None else []
        self.update()

    # ── helpers ────────────────────────────────────────────────────────────
    def _map_points(self, values: Sequence[float], rect: QRectF,
                    vmin: float, vmax: float) -> List[QPointF]:
        if not values:
            return []
        step = rect.width() / max(len(values) - 1, 1)
        span = max(vmax - vmin, 1)
        return [
            QPointF(rect.left() + step * i,
                    rect.bottom() - ((v - vmin) / span) * rect.height())
            for i, v in enumerate(values)
        ]

    def _bezier_path(self, points: List[QPointF]) -> QPainterPath:
        """Smooth cubic bezier through points."""
        path = QPainterPath(points[0])
        for i in range(1, len(points)):
            p0 = points[i - 1]
            p1 = points[i]
            cx = (p0.x() + p1.x()) / 2
            path.cubicTo(QPointF(cx, p0.y()), QPointF(cx, p1.y()), p1)
        return path

    def _valid_atm(self) -> List[float]:
        return [float(v) for v in self.atmospheric_data if v is not None]

    def _draw_legend(self, painter: QPainter, right_x: int, y: int,
                     color: str, text: str, dashed: bool = False) -> int:
        fm   = painter.fontMetrics()
        tw   = fm.horizontalAdvance(text)
        ll   = 18
        left = right_x - ll - 6 - tw
        pen  = QPen(QColor(color), 2.5)
        if dashed:
            pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.drawLine(left, y, left + ll, y)
        # dot
        painter.setBrush(QColor(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(left + ll // 2, y), 3.5, 3.5)
        painter.setPen(QColor("#475569"))
        painter.drawText(left + ll + 6, y + 4, text)
        return left - 18

    # ── paint ──────────────────────────────────────────────────────────────
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        r  = self.rect()
        # background card
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(self._BG_COLOR))
        p.drawRoundedRect(r, 20, 20)

        has_atm  = len(self._valid_atm()) >= 2
        rpad     = 56 if has_atm else 20
        chart    = QRectF(r.left() + 56, r.top() + 36,
                          r.width() - 56 - rpad, r.height() - 72)

        # grid lines
        font = QFont("Segoe UI", 8)
        p.setFont(font)
        for i in range(6):
            gy = chart.top() + (chart.height() / 5) * i
            p.setPen(QPen(QColor(self._GRID_COLOR), 1))
            p.drawLine(int(chart.left()), int(gy), int(chart.right()), int(gy))

        if not self.systolic_data:
            p.setPen(QColor("#94a3b8"))
            p.drawText(chart, Qt.AlignmentFlag.AlignCenter, "Недостатньо даних")
            return

        bp_vals = self.systolic_data + self.diastolic_data
        bp_min  = min(bp_vals) - 8
        bp_max  = max(bp_vals) + 8

        # Y axis labels (left)
        p.setPen(QColor(self._AXIS_COLOR))
        for i in range(6):
            val = bp_max - ((bp_max - bp_min) / 5) * i
            gy  = chart.top() + (chart.height() / 5) * i
            p.drawText(QRectF(r.left() + 4, gy - 10, 48, 20),
                       Qt.AlignmentFlag.AlignRight, f"{int(val)}")

        atm_vals = self._valid_atm()
        if has_atm:
            atm_min = min(atm_vals) - 4
            atm_max = max(atm_vals) + 4
            p.setPen(QColor(self._ATM_COLOR))
            for i in range(6):
                val = atm_max - ((atm_max - atm_min) / 5) * i
                gy  = chart.top() + (chart.height() / 5) * i
                p.drawText(QRectF(r.right() - rpad + 4, gy - 10, rpad - 8, 20),
                           Qt.AlignmentFlag.AlignLeft, f"{int(val)}")

        sys_pts = self._map_points(self.systolic_data,  chart, bp_min, bp_max)
        dia_pts = self._map_points(self.diastolic_data, chart, bp_min, bp_max)

        def draw_series(pts: List[QPointF], color: str, alpha: int,
                        dashed: bool = False, dot_r: float = 4.0):
            if len(pts) < 2:
                return
            path = self._bezier_path(pts)

            # gradient fill
            if not dashed:
                fill_path = QPainterPath(path)
                fill_path.lineTo(pts[-1].x(), chart.bottom())
                fill_path.lineTo(pts[0].x(),  chart.bottom())
                fill_path.closeSubpath()
                grad = QLinearGradient(0, chart.top(), 0, chart.bottom())
                c = QColor(color)
                c.setAlpha(alpha)
                grad.setColorAt(0, c)
                c2 = QColor(color)
                c2.setAlpha(0)
                grad.setColorAt(1, c2)
                p.setPen(Qt.PenStyle.NoPen)
                p.fillPath(fill_path, grad)

            pen = QPen(QColor(color), 2.5)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            if dashed:
                pen.setStyle(Qt.PenStyle.DashLine)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(path)

            # dots with white center
            for pt in pts:
                p.setPen(QPen(QColor(color), 2))
                p.setBrush(QColor("white"))
                p.drawEllipse(pt, dot_r, dot_r)

        draw_series(sys_pts, self._SYS_COLOR, 50)
        draw_series(dia_pts, self._DIA_COLOR, 35)

        if has_atm and len(self.atmospheric_data) == len(self.systolic_data):
            atm_pts: List[QPointF] = []
            step = chart.width() / max(len(self.atmospheric_data) - 1, 1)
            span = max(atm_max - atm_min, 1)
            for i, v in enumerate(self.atmospheric_data):
                if v is None:
                    continue
                x = chart.left() + step * i
                y = chart.bottom() - ((float(v) - atm_min) / span) * chart.height()
                atm_pts.append(QPointF(x, y))
            draw_series(atm_pts, self._ATM_COLOR, 0, dashed=True, dot_r=3.0)

        # X-axis labels
        p.setPen(QColor(self._AXIS_COLOR))
        max_lbl  = 8
        n        = len(self.labels)
        indices  = list(range(0, n, max(1, n // max_lbl)))
        if n - 1 not in indices:
            indices.append(n - 1)
        for i in indices:
            x = chart.left() + (chart.width() / max(n - 1, 1)) * i
            p.drawText(QRectF(x - 28, chart.bottom() + 6, 56, 18),
                       Qt.AlignmentFlag.AlignHCenter, self.labels[i])

        # legend
        legend_y = int(chart.top()) - 14
        cx = int(r.right()) - 16
        if has_atm:
            cx = self._draw_legend(p, cx, legend_y, self._ATM_COLOR, "Атм. тиск", dashed=True)
        cx = self._draw_legend(p, cx, legend_y, self._DIA_COLOR, "Діастолічний")
        self._draw_legend(p, cx, legend_y, self._SYS_COLOR, "Систолічний")


class PressureGauge(QWidget):
    """Animated semi-circular arc gauge."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._display_value = 120
        self._target_value  = 120
        self.label          = "Норма"
        self.setMinimumSize(200, 170)
        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(16)
        self._anim_timer.timeout.connect(self._tick)

    def set_value(self, value: int, label: str) -> None:
        self._target_value = value
        self.label         = label
        self._anim_timer.start()

    def _tick(self):
        diff = self._target_value - self._display_value
        if abs(diff) < 0.5:
            self._display_value = self._target_value
            self._anim_timer.stop()
        else:
            self._display_value += diff * 0.12
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect().adjusted(8, 8, -8, -8)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#f8faff"))
        p.drawRoundedRect(r, 20, 20)

        cx     = r.center().x()
        # Move arc centre upward, leave room for pill at bottom
        cy     = int(r.top() + r.height() * 0.50)
        radius = min(r.width(), r.height()) * 0.32
        arc_r  = QRectF(cx - radius, cy - radius, radius * 2, radius * 2)

        # Track arc (200° span, start at 170°)
        start_a = 170 * 16
        span_a  = -200 * 16
        p.setPen(QPen(QColor("#e2e8f0"), 9, Qt.PenStyle.SolidLine,
                      Qt.PenCapStyle.RoundCap))
        p.drawArc(arc_r, start_a, span_a)

        # Value arc
        v = self._display_value
        ratio = max(0.0, min((v - 80) / 80, 1.0))
        filled_span = int(-200 * ratio * 16)
        if v < 120:
            arc_color = QColor("#10b981")
        elif v < 130:
            arc_color = QColor("#06b6d4")
        elif v < 140:
            arc_color = QColor("#f59e0b")
        else:
            arc_color = QColor("#ef4444")
        p.setPen(QPen(arc_color, 9, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawArc(arc_r, start_a, filled_span)

        # value text — centred inside the arc
        p.setPen(QColor("#1e293b"))
        f = QFont("Segoe UI", 22, QFont.Weight.Bold)
        p.setFont(f)
        p.drawText(QRectF(r.left(), cy - 18, r.width(), 36),
                   Qt.AlignmentFlag.AlignHCenter, str(int(v)))

        f2 = QFont("Segoe UI", 8)
        p.setFont(f2)
        p.setPen(QColor("#94a3b8"))
        p.drawText(QRectF(r.left(), cy + 20, r.width(), 16),
                   Qt.AlignmentFlag.AlignHCenter, "мм рт. ст.")

        # status pill — fixed distance from bottom, never overlaps arc
        status_color = (
            "#10b981" if v < 120 else
            "#06b6d4" if v < 130 else
            "#f59e0b" if v < 140 else "#ef4444"
        )
        f3 = QFont("Segoe UI", 9, QFont.Weight.Bold)
        p.setFont(f3)
        fm   = p.fontMetrics()
        tw   = fm.horizontalAdvance(self.label) + 22
        pill_y = r.bottom() - 30
        pill = QRectF(cx - tw / 2, pill_y, tw, 22)
        c    = QColor(status_color)
        c.setAlpha(25)
        p.setBrush(c)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(pill, 11, 11)
        p.setPen(QColor(status_color))
        p.drawText(pill, Qt.AlignmentFlag.AlignCenter, self.label)
