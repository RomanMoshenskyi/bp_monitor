"""ReportService - from diploma class diagram."""
from __future__ import annotations

import json
import csv
import logging
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from sqlalchemy.orm import Session

from app.domain.entities import ReportORM, MeasurementORM, UserORM, ReportFormat, ReportStatus
from app.application.dto import ReportDTO, ReportCreateDTO, AnalysisResultDTO

_logger = logging.getLogger(__name__)


class ReportService:
    """
    Report generation service.
    
    From diploma class diagram: generateReport(patientId, period)
    """
    
    def __init__(self, db: Session, reports_dir: str = "reports"):
        self._db = db
        self._reports_dir = Path(reports_dir)
        self._reports_dir.mkdir(exist_ok=True)
    
    def generate_csv(
        self,
        patient_id: int,
        measurements: List[MeasurementORM],
        generated_by: Optional[int] = None,
    ) -> ReportDTO:
        """
        Generate CSV report.
        
        From diploma (section 3.4.5): Export to JSON/CSV format.
        """
        # Create report record
        report = ReportORM(
            patient_id=patient_id,
            period_start=measurements[0].measured_at.date() if measurements else date.today(),
            period_end=measurements[-1].measured_at.date() if measurements else date.today(),
            file_format=ReportFormat.CSV,
            status=ReportStatus.GENERATING,
            generated_by=generated_by,
        )
        
        self._db.add(report)
        self._db.commit()
        
        try:
            # Generate CSV file
            filename = f"report_{patient_id}_{report.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = self._reports_dir / filename
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # Header
                writer.writerow([
                    'ID', 'Date', 'Systolic', 'Diastolic', 'Pulse',
                    'Pressure (mmHg)', 'Temperature', 'Notes'
                ])
                # Data
                for m in measurements:
                    writer.writerow([
                        m.id,
                        m.measured_at.isoformat() if m.measured_at else '',
                        m.systolic,
                        m.diastolic,
                        m.pulse or '',
                        m.weather_snapshot.pressure_mmhg if m.weather_snapshot else '',
                        m.weather_snapshot.temperature if m.weather_snapshot else '',
                        m.notes or '',
                    ])
            
            # Update report
            report.mark_completed(str(filepath), filepath.stat().st_size)
            self._db.commit()
            
            _logger.info(f"CSV report {report.id} generated: {filepath}")
            
            return self._to_dto(report)
            
        except Exception as e:
            report.mark_failed(str(e))
            self._db.commit()
            _logger.error(f"Failed to generate CSV report: {e}")
            raise
    
    def generate_json(
        self,
        patient_id: int,
        measurements: List[MeasurementORM],
        analysis: Optional[AnalysisResultDTO] = None,
        generated_by: Optional[int] = None,
    ) -> ReportDTO:
        """Generate JSON report (for backup/export per diploma)."""
        report = ReportORM(
            patient_id=patient_id,
            period_start=measurements[0].measured_at.date() if measurements else date.today(),
            period_end=measurements[-1].measured_at.date() if measurements else date.today(),
            file_format=ReportFormat.JSON,
            status=ReportStatus.GENERATING,
            generated_by=generated_by,
        )
        
        self._db.add(report)
        self._db.commit()
        
        try:
            filename = f"report_{patient_id}_{report.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self._reports_dir / filename
            
            data = {
                "patient_id": patient_id,
                "generated_at": datetime.utcnow().isoformat(),
                "period": {
                    "start": report.period_start.isoformat(),
                    "end": report.period_end.isoformat(),
                },
                "measurements_count": len(measurements),
                "measurements": [m.to_dict() for m in measurements],
            }
            
            if analysis:
                data["analysis"] = analysis.to_dict()
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            report.mark_completed(str(filepath), filepath.stat().st_size)
            self._db.commit()
            
            _logger.info(f"JSON report {report.id} generated: {filepath}")
            
            return self._to_dto(report)
            
        except Exception as e:
            report.mark_failed(str(e))
            self._db.commit()
            _logger.error(f"Failed to generate JSON report: {e}")
            raise
    
    def list_for_patient(
        self, 
        patient_id: int,
        limit: int = 50,
    ) -> List[ReportDTO]:
        """List generated reports for patient."""
        from sqlalchemy import select, desc
        
        stmt = (
            select(ReportORM)
            .where(ReportORM.patient_id == patient_id)
            .order_by(desc(ReportORM.created_at))
            .limit(limit)
        )
        
        results = self._db.execute(stmt).scalars().all()
        return [self._to_dto(r) for r in results]
    
    def get_report(self, report_id: int) -> Optional[ReportDTO]:
        """Get report by ID."""
        report = self._db.get(ReportORM, report_id)
        return self._to_dto(report) if report else None
    
    def _to_dto(self, report: ReportORM) -> ReportDTO:
        """Convert ORM to DTO."""
        return ReportDTO(
            id=report.id,
            patient_id=report.patient_id,
            period_start=report.period_start,
            period_end=report.period_end,
            file_format=report.file_format,
            file_path=report.file_path,
            file_size=report.file_size,
            status=report.status,
            title=report.title,
            description=report.description,
            generated_at=report.generated_at,
            created_at=report.created_at,
        )
