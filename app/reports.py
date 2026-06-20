from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Sequence
import base64

from PyQt6.QtCore import Qt, QSize, QBuffer
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication

from .analytics import generate_recommendations, summary
from .auth import User
from .models import Measurement
from .widgets import TrendChart


def _generate_chart_image(measurements: Sequence[Measurement]) -> str:
    """Generate chart image as base64 data URL."""
    if not measurements:
        return ""
    
    # Create a TrendChart widget (off-screen)
    chart = TrendChart()
    chart.resize(800, 400)
    
    # Prepare data (last 20 measurements, reversed to show newest first)
    recent = list(measurements)[-20:]
    
    
    systolic = [m.systolic for m in recent]
    diastolic = [m.diastolic for m in recent]
    atmospheric = [m.atmospheric_pressure for m in recent]
    
    # Handle timestamp - could be datetime or string
    labels = []
    for m in recent:
        if hasattr(m.timestamp, 'strftime'):
            labels.append(m.timestamp.strftime("%d.%m"))
        else:
            # If it's a string, try to parse it or use as-is
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(str(m.timestamp))
                labels.append(dt.strftime("%d.%m"))
            except:
                labels.append(str(m.timestamp)[:10])
    
    chart.set_series(systolic, diastolic, labels, atmospheric)
    
    # Render to pixmap
    pixmap = chart.grab()
    
    # Convert to base64 using QBuffer
    buffer = QBuffer()
    buffer.open(QBuffer.OpenModeFlag.WriteOnly)
    pixmap.save(buffer, "PNG")
    buffer.close()
    img_base64 = base64.b64encode(buffer.data()).decode("utf-8")
    
    return f"data:image/png;base64,{img_base64}"


def build_doctor_report_html(
    patient: User,
    measurements: Sequence[Measurement],
    doctor_recommendations: List[str],
    auto_recommendations: List[str],
) -> str:
    stats = summary(measurements)
    
    # Generate chart image
    chart_image = _generate_chart_image(measurements)
    
    rows = ""
    for m in reversed(list(measurements)[-20:]):
        rows += (
            f"<tr><td>{m.timestamp}</td><td>{m.systolic}/{m.diastolic}</td>"
            f"<td>{m.pulse}</td><td>{m.atmospheric_pressure or '—'}</td>"
            f"<td>{m.mood}</td><td>{m.notes or '—'}</td></tr>"
        )
    doctor_block = "".join(f"<li>{text}</li>" for text in doctor_recommendations) or "<li>Немає записів</li>"
    auto_block = "".join(f"<li>{text}</li>" for text in auto_recommendations) or "<li>—</li>"
    
    chart_section = ""
    if chart_image:
        chart_section = f"""
  <h2>Графік динаміки тиску</h2>
  <div class="chart-container">
    <img src="{chart_image}" alt="Графік тиску" style="width: 100%; max-width: 800px; height: auto; border-radius: 12px; border: 1px solid #d6e2ef;">
  </div>
"""
    
    return f"""<!DOCTYPE html>
<html lang="uk">
<head>
  <meta charset="utf-8">
  <title>Звіт — {patient.full_name}</title>
  <style>
    body {{ font-family: Segoe UI, sans-serif; margin: 32px; color: #1c3150; }}
    h1 {{ color: #173456; }}
    h2 {{ color: #2c5282; margin-top: 24px; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 16px; }}
    th, td {{ border: 1px solid #d6e2ef; padding: 8px; text-align: left; }}
    th {{ background: #f5f9fd; }}
    .stats {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin: 16px 0; }}
    .card {{ background: #f6fbff; padding: 12px; border-radius: 12px; }}
    .chart-container {{ margin: 16px 0; text-align: center; }}
  </style>
</head>
<body>
  <h1>Медичний звіт пацієнта</h1>
  <p><strong>Пацієнт:</strong> {patient.full_name} | <strong>Вік:</strong> {patient.age or '—'}</p>
  <p><strong>Цільові показники:</strong> {patient.target_systolic}/{patient.target_diastolic} мм рт. ст., пульс {patient.target_pulse}</p>
  <p><strong>Дата звіту:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
  <div class="stats">
    <div class="card"><strong>Записів</strong><br>{stats['count']}</div>
    <div class="card"><strong>Середній тиск</strong><br>{stats['avg_systolic']}/{stats['avg_diastolic']}</div>
    <div class="card"><strong>Стан</strong><br>{stats['latest_status']}</div>
  </div>
  <h2>Рекомендації лікаря</h2>
  <ul>{doctor_block}</ul>
  <h2>Автоматична аналітика</h2>
  <ul>{auto_block}</ul>
{chart_section}
  <h2>Останні вимірювання</h2>
  <table>
    <tr><th>Дата</th><th>Тиск</th><th>Пульс</th><th>Атм.</th><th>Стан</th><th>Примітки</th></tr>
    {rows or '<tr><td colspan="6">Немає даних</td></tr>'}
  </table>
</body>
</html>"""


def save_doctor_report(path: str | Path, html: str) -> None:
    Path(path).write_text(html, encoding="utf-8")
