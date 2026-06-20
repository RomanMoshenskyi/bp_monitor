"""PulseView reusable widgets — glass cards, gauges, charts, badges."""
from __future__ import annotations

from typing import List, Optional, Sequence

from PyQt6.QtCore import QPointF, QRectF, QSize, Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget


# ── GlassCard ─────────────────────────────────────────────────────
class GlassCard(QFrame):
    """Premium stat card with hover glow and left accent bar."""
    ACCENTS = ["#6366f1", "#06b6d4", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899"]

    def __init__(self, title: str = "", value: str = "", subtitle: str = "", accent_index: int = 0):
        super().__init__()
        self.setObjectName("glassCard")
        self.setMinimumHeight(136); self.setFrameShape(QFrame.Shape.NoFrame)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._accent = self.ACCENTS[accent_index % len(self.ACCENTS)]
        self.setStyleSheet(f"""
            QFrame#glassCard {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #fafaff,stop:1 #f5f7ff);
                border: 1.5px solid rgba(226,232,240,0.65);
                border-radius: 18px;
            }}
            QFrame#glassCard:hover {{
                border-color: rgba(99,102,241,0.25);
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffffff,stop:1 #f8faff);
            }}
        """)
        lay = QVBoxLayout(self); lay.setContentsMargins(22,20,22,18); lay.setSpacing(6)
        top = QHBoxLayout(); top.setSpacing(10)
        self._dot = QLabel(); self._dot.setFixedSize(10,10)
        self._dot.setStyleSheet(f"background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {self._accent},stop:1 {self._accent}80);border-radius:5px;")
        self.title_label = QLabel(title); self.title_label.setObjectName("cardTitle")
        top.addWidget(self._dot); top.addWidget(self.title_label,1); lay.addLayout(top)
        self.value_label = QLabel(value); self.value_label.setObjectName("cardValue")
        lay.addWidget(self.value_label)
        self.subtitle_label = QLabel(subtitle); self.subtitle_label.setObjectName("cardSubtitle")
        self.subtitle_label.setWordWrap(True); lay.addWidget(self.subtitle_label); lay.addStretch(1)

    def update_content(self,title:str,value:str,subtitle:str)->None:
        self.title_label.setText(title); self.value_label.setText(value); self.subtitle_label.setText(subtitle)


# ── StatusBadge ───────────────────────────────────────────────────
class StatusBadge(QLabel):
    _COLORS = {
        "normal":("#d1fae5","#059669"),"висока":("#fee2e2","#dc2626"),"низький":("#fef3c7","#d97706"),
        "висок":("#fee2e2","#dc2626"),"норм":("#d1fae5","#059669"),"немає":("#f3f4f6","#6b7280"),
    }
    def __init__(self,text:str=""):
        super().__init__(text); self.setAlignment(Qt.AlignmentFlag.AlignCenter); self.setFixedHeight(26); self.update_status(text)
    def update_status(self,text:str)->None:
        self.setText(text)
        key=next((k for k in self._COLORS if k in text.lower()),"немає")
        bg,fg=self._COLORS[key]
        self.setStyleSheet(f"background:{bg};color:{fg};border-radius:13px;padding:2px 12px;font-size:12px;font-weight:700;")


# ── SectionTitle ──────────────────────────────────────────────────
class SectionTitle(QLabel):
    def __init__(self,text:str):
        super().__init__(text); self.setObjectName("sectionTitle")


# ── TrendChart ────────────────────────────────────────────────────
class TrendChart(QWidget):
    _SYS="#6366f1"; _DIA="#06b6d4"; _ATM="#f59e0b"; _GRID="#edf0f7"; _AXIS="#94a3b8"
    def __init__(self,parent:Optional[QWidget]=None):
        super().__init__(parent); self.setMinimumHeight(300)
        self.systolic_data:List[float]=[]; self.diastolic_data:List[float]=[]
        self.atmospheric_data:List[Optional[float]]=[]; self.labels:List[str]=[]
        self.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Expanding)
    def set_series(self,systolic:Sequence[float],diastolic:Sequence[float],labels:Sequence[str],atmospheric:Sequence[Optional[float]]|None=None)->None:
        self.systolic_data=list(systolic); self.diastolic_data=list(diastolic); self.labels=list(labels)
        self.atmospheric_data=list(atmospheric) if atmospheric is not None else []; self.update()
    def _map(self,values:Sequence[float],rect:QRectF,vmin:float,vmax:float)->List[QPointF]:
        if not values: return []
        step=rect.width()/max(len(values)-1,1); span=max(vmax-vmin,1)
        return [QPointF(rect.left()+step*i,rect.bottom()-((v-vmin)/span)*rect.height()) for i,v in enumerate(values)]
    def _bez(self,pts:List[QPointF])->QPainterPath:
        path=QPainterPath(pts[0])
        for i in range(1,len(pts)):
            p0,p1=pts[i-1],pts[i]; cx=(p0.x()+p1.x())/2
            path.cubicTo(QPointF(cx,p0.y()),QPointF(cx,p1.y()),p1)
        return path
    def _vatm(self)->List[float]: return [float(v) for v in self.atmospheric_data if v is not None]
    def _legend(self,p:QPainter,rx:int,y:int,color:str,text:str,dashed:bool=False)->int:
        fm=p.fontMetrics(); tw=fm.horizontalAdvance(text); ll=18; left=rx-ll-6-tw
        pen=QPen(QColor(color),2.5)
        if dashed: pen.setStyle(Qt.PenStyle.DashLine)
        p.setPen(pen); p.drawLine(left,y,left+ll,y)
        p.setBrush(QColor(color)); p.setPen(Qt.PenStyle.NoPen); p.drawEllipse(QPointF(left+ll//2,y),3.5,3.5)
        p.setPen(QColor("#475569")); p.drawText(left+ll+6,y+4,text); return left-18
    def paintEvent(self,e):
        p=QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing); r=self.rect()
        p.setPen(Qt.PenStyle.NoPen); bg=QLinearGradient(0,0,0,r.height()); bg.setColorAt(0,QColor("#fafaff")); bg.setColorAt(1,QColor("#f5f7ff")); p.setBrush(bg); p.drawRoundedRect(r,22,22)
        p.setPen(QPen(QColor(226,232,240,120),1)); p.setBrush(Qt.BrushStyle.NoBrush); p.drawRoundedRect(r.adjusted(0,0,-1,-1),22,22); p.setPen(Qt.PenStyle.NoPen)
        has_atm=len(self._vatm())>=2; rpad=56 if has_atm else 20
        chart=QRectF(r.left()+56,r.top()+36,r.width()-56-rpad,r.height()-72)
        p.setFont(QFont("Segoe UI",8))
        for i in range(6):
            gy=chart.top()+(chart.height()/5)*i; p.setPen(QPen(QColor(self._GRID),1)); p.drawLine(int(chart.left()),int(gy),int(chart.right()),int(gy))
        if not self.systolic_data:
            p.setPen(QColor(self._AXIS)); p.drawText(chart,Qt.AlignmentFlag.AlignCenter,"Недостатньо даних"); p.end(); return
        bp_vals=self.systolic_data+self.diastolic_data; bp_min=min(bp_vals)-8; bp_max=max(bp_vals)+8
        p.setPen(QColor(self._AXIS))
        for i in range(6):
            val=bp_max-((bp_max-bp_min)/5)*i; gy=chart.top()+(chart.height()/5)*i
            p.drawText(QRectF(r.left()+4,gy-10,48,20),Qt.AlignmentFlag.AlignRight,f"{int(val)}")
        atm_vals=self._vatm()
        if has_atm:
            atm_min=min(atm_vals)-4; atm_max=max(atm_vals)+4; p.setPen(QColor(self._ATM))
            for i in range(6):
                val=atm_max-((atm_max-atm_min)/5)*i; gy=chart.top()+(chart.height()/5)*i
                p.drawText(QRectF(r.right()-rpad+4,gy-10,rpad-8,20),Qt.AlignmentFlag.AlignLeft,f"{int(val)}")
        sys_pts=self._map(self.systolic_data,chart,bp_min,bp_max); dia_pts=self._map(self.diastolic_data,chart,bp_min,bp_max)
        def draw(pts:List[QPointF],color:str,alpha:int,dashed:bool=False,dr:float=4.0):
            if len(pts)<2: return
            path=self._bez(pts)
            if not dashed:
                fp=QPainterPath(path); fp.lineTo(pts[-1].x(),chart.bottom()); fp.lineTo(pts[0].x(),chart.bottom()); fp.closeSubpath()
                gr=QLinearGradient(0,chart.top(),0,chart.bottom()); c=QColor(color); c.setAlpha(alpha); gr.setColorAt(0,c); c2=QColor(color); c2.setAlpha(0); gr.setColorAt(1,c2)
                p.setPen(Qt.PenStyle.NoPen); p.fillPath(fp,gr)
            pen=QPen(QColor(color),2.5); pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            if dashed: pen.setStyle(Qt.PenStyle.DashLine)
            p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush); p.drawPath(path)
            for pt in pts:
                p.setPen(QPen(QColor(color),2)); p.setBrush(QColor("white")); p.drawEllipse(pt,dr,dr)
        draw(sys_pts,self._SYS,50); draw(dia_pts,self._DIA,35)
        if has_atm and len(self.atmospheric_data)==len(self.systolic_data):
            atm_pts:List[QPointF]=[]; step=chart.width()/max(len(self.atmospheric_data)-1,1); span=max(atm_max-atm_min,1)
            for i,v in enumerate(self.atmospheric_data):
                if v is None: continue
                atm_pts.append(QPointF(chart.left()+step*i,chart.bottom()-((float(v)-atm_min)/span)*chart.height()))
            draw(atm_pts,self._ATM,0,dashed=True,dr=3.0)
        p.setPen(QColor(self._AXIS)); max_lbl=8; n=len(self.labels); indices=list(range(0,n,max(1,n//max_lbl))); 
        if n-1 not in indices: indices.append(n-1)
        for i in indices:
            x=chart.left()+(chart.width()/max(n-1,1))*i
            p.drawText(QRectF(x-28,chart.bottom()+6,56,18),Qt.AlignmentFlag.AlignHCenter,self.labels[i])
        ly=int(chart.top())-14; cx=int(r.right())-16
        if has_atm: cx=self._legend(p,cx,ly,self._ATM,"Атм. тиск",dashed=True)
        cx=self._legend(p,cx,ly,self._DIA,"Діастолічний"); self._legend(p,cx,ly,self._SYS,"Систолічний")
        p.end()


# ── PressureGauge ─────────────────────────────────────────────────
class PressureGauge(QWidget):
    def __init__(self,parent:Optional[QWidget]=None):
        super().__init__(parent); self._disp=120; self._tgt=120; self.label="Норма"; self.setMinimumSize(210,180)
        self._tm=QTimer(self); self._tm.setInterval(16); self._tm.timeout.connect(self._tick)
    def set_value(self,value:int,label:str)->None:
        self._tgt=value; self.label=label; self._tm.start()
    def _tick(self):
        diff=self._tgt-self._disp
        if abs(diff)<0.5: self._disp=self._tgt; self._tm.stop()
        else: self._disp+=diff*0.12
        self.update()
    def paintEvent(self,e):
        p=QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing); r=self.rect().adjusted(8,8,-8,-8)
        p.setPen(Qt.PenStyle.NoPen); bg=QLinearGradient(0,r.top(),0,r.bottom()); bg.setColorAt(0,QColor("#fafaff")); bg.setColorAt(1,QColor("#f5f7ff")); p.setBrush(bg); p.drawRoundedRect(r,22,22)
        p.setPen(QPen(QColor(226,232,240,100),1)); p.setBrush(Qt.BrushStyle.NoBrush); p.drawRoundedRect(r.adjusted(0,0,-1,-1),22,22)
        cx=r.center().x(); cy=int(r.top()+r.height()*0.50); radius=min(r.width(),r.height())*0.32; arc_r=QRectF(cx-radius,cy-radius,radius*2,radius*2)
        sa=170*16; sp=-200*16; p.setPen(QPen(QColor("#e8edf5"),10,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap)); p.drawArc(arc_r,sa,sp)
        v=self._disp; ratio=max(0.0,min((v-80)/80,1.0)); fs=int(-200*ratio*16)
        arc_color=QColor("#10b981") if v<120 else QColor("#06b6d4") if v<130 else QColor("#f59e0b") if v<140 else QColor("#ef4444")
        gc=QColor(arc_color); gc.setAlpha(40); p.setPen(QPen(gc,16,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap)); p.drawArc(arc_r,sa,fs)
        p.setPen(QPen(arc_color,10,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap)); p.drawArc(arc_r,sa,fs)
        p.setPen(QColor("#0f172a")); p.setFont(QFont("Segoe UI",24,QFont.Weight.Bold)); p.drawText(QRectF(r.left(),cy-20,r.width(),40),Qt.AlignmentFlag.AlignHCenter,str(int(v)))
        p.setFont(QFont("Segoe UI",8)); p.setPen(QColor("#94a3b8")); p.drawText(QRectF(r.left(),cy+22,r.width(),16),Qt.AlignmentFlag.AlignHCenter,"мм рт. ст.")
        sc="#10b981" if v<120 else "#06b6d4" if v<130 else "#f59e0b" if v<140 else "#ef4444"
        p.setFont(QFont("Segoe UI",9,QFont.Weight.Bold)); fm=p.fontMetrics(); tw=fm.horizontalAdvance(self.label)+26; pill_y=r.bottom()-32; pill=QRectF(cx-tw/2,pill_y,tw,24)
        c=QColor(sc); c.setAlpha(22); p.setBrush(c); p.setPen(Qt.PenStyle.NoPen); p.drawRoundedRect(pill,12,12); p.setPen(QColor(sc)); p.drawText(pill,Qt.AlignmentFlag.AlignCenter,self.label)
        p.end()


# ── PageHeader ────────────────────────────────────────────────────
class PageHeader(QWidget):
    """Consistent page header with title, subtitle and optional action row."""
    def __init__(self, title: str, subtitle: str = "", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setStyleSheet("background:transparent;")
        v = QVBoxLayout(self); v.setContentsMargins(0,0,0,0); v.setSpacing(4)
        self.title = QLabel(title); self.title.setObjectName("pageTitle")
        v.addWidget(self.title)
        if subtitle:
            self.sub = QLabel(subtitle); self.sub.setObjectName("pageSubtitle")
            v.addWidget(self.sub)
