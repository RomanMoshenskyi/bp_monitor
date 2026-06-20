"""DoctorReportService - Medical report generation and management."""
from __future__ import annotations

import uuid
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import select, desc, and_

from app.domain.entities import DoctorReportORM, UserORM, MeasurementORM
from app.application.dto.doctor_report_dto import DoctorReportDTO, DoctorReportCreateDTO


class DoctorReportService:
    """
    Service for managing doctor medical reports.
    
    Handles:
    - Creating medical reports with full clinical documentation
    - Generating professional HTML reports with signatures
    - Listing reports by doctor (private to doctor)
    - Downloading and viewing reports
    """
    
    def __init__(self, db: Session, reports_dir: str = "doctor_reports"):
        self._db = db
        self._reports_dir = Path(reports_dir)
        self._reports_dir.mkdir(exist_ok=True)
    
    def create_report(self, data: DoctorReportCreateDTO) -> DoctorReportDTO:
        """
        Create a new medical report.
        
        Args:
            data: Report creation data
            
        Returns:
            Created report DTO
        """
        try:
            # Generate unique report number
            report_number = f"MR-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
            
            report = DoctorReportORM(
                patient_id=data.patient_id,
                doctor_id=data.doctor_id,
                report_number=report_number,
                report_date=data.report_date or date.today(),
                
                # Complaints and history
                chief_complaint=data.chief_complaint,
                history_illness=data.history_illness,
                history_life=data.history_life,
                
                # Examination
                objective_exam=data.objective_exam,
                general_condition=data.general_condition,
                consciousness=data.consciousness,
                body_temperature=data.body_temperature,
                skin_condition=data.skin_condition,
                
                # Vital signs
                heart_rate=data.heart_rate,
                respiratory_rate=data.respiratory_rate,
                blood_pressure_sys=data.blood_pressure_sys,
                blood_pressure_dia=data.blood_pressure_dia,
                
                # Cardiovascular
                heart_sounds=data.heart_sounds,
                pulse_rhythm=data.pulse_rhythm,
                pulse_character=data.pulse_character,
                
                # Diagnosis
                preliminary_diagnosis=data.preliminary_diagnosis,
                final_diagnosis=data.final_diagnosis,
                diagnosis_code_icd=data.diagnosis_code_icd,
                
                # Exams
                ecg_results=data.ecg_results,
                xray_results=data.xray_results,
                lab_results=data.lab_results,
                other_exams=data.other_exams,
                
                # Treatment
                treatment_plan=data.treatment_plan,
                prescriptions=data.prescriptions,
                procedures=data.procedures,
                lifestyle_recommendations=data.lifestyle_recommendations,
                diet_recommendations=data.diet_recommendations,
                activity_recommendations=data.activity_recommendations,
                
                # Conclusions
                doctor_conclusion=data.doctor_conclusion,
                prognosis=data.prognosis,
                
                # Follow up
                next_visit_date=data.next_visit_date,
                next_visit_reason=data.next_visit_reason,
                
                # Sick leave
                sick_leave_required=data.sick_leave_required,
                sick_leave_days=data.sick_leave_days,
                sick_leave_from=data.sick_leave_from,
                sick_leave_to=data.sick_leave_to,
            )
            
            self._db.add(report)
            self._db.commit()
            self._db.refresh(report)
            
            return self._to_dto(report)
        except Exception:
            self._db.rollback()
            raise
    
    def sign_report(
        self, 
        report_id: int, 
        doctor_name: str, 
        position: str, 
        specialty: str = None
    ) -> DoctorReportDTO:
        """
        Sign a medical report.
        
        Args:
            report_id: Report to sign
            doctor_name: Doctor's full name for signature
            position: Doctor's position
            specialty: Doctor's specialty (optional)
            
        Returns:
            Updated report DTO
        """
        try:
            report = self._db.get(DoctorReportORM, report_id)
            if not report:
                raise ValueError(f"Report {report_id} not found")
            
            report.sign(doctor_name, position, specialty)
            self._db.commit()
            self._db.refresh(report)
            
            return self._to_dto(report)
        except Exception:
            self._db.rollback()
            raise
    
    def generate_html_report(self, report_id: int) -> str:
        """
        Generate professional HTML medical report.
        
        Args:
            report_id: Report ID
            
        Returns:
            HTML content
        """
        report = self._db.get(DoctorReportORM, report_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")
        
        # Get patient and doctor info
        patient = self._db.get(UserORM, report.patient_id)
        doctor = self._db.get(UserORM, report.doctor_id)
        
        # Build professional medical report HTML
        html = self._build_medical_report_html(report, patient, doctor)
        
        return html
    
    def save_html_report(self, report_id: int, html_content: str, save_path: str = None) -> Path:
        """
        Save HTML report to file.
        
        Args:
            report_id: Report ID
            html_content: HTML content
            save_path: Optional custom path to save file (if None, uses default reports_dir)
            
        Returns:
            Path to saved file
        """
        report = self._db.get(DoctorReportORM, report_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")
        
        if save_path:
            filepath = Path(save_path)
        else:
            filename = f"medical_report_{report.report_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            filepath = self._reports_dir / filename
        
        filepath.write_text(html_content, encoding="utf-8")
        
        # Update report record
        report.file_path = str(filepath)
        report.file_size = filepath.stat().st_size
        self._db.commit()
        
        return filepath
    
    def list_doctor_reports(
        self, 
        doctor_id: int, 
        patient_id: Optional[int] = None,
        limit: int = 50
    ) -> List[DoctorReportDTO]:
        """
        List reports created by a doctor.
        
        Args:
            doctor_id: Doctor's user ID
            patient_id: Optional filter by patient
            limit: Maximum results
            
        Returns:
            List of report DTOs
        """
        stmt = select(DoctorReportORM).where(
            DoctorReportORM.doctor_id == doctor_id
        ).order_by(desc(DoctorReportORM.created_at)).limit(limit)
        
        if patient_id:
            stmt = stmt.where(DoctorReportORM.patient_id == patient_id)
        
        results = self._db.execute(stmt).scalars().all()
        return [self._to_dto(r) for r in results]
    
    def get_report(self, report_id: int, doctor_id: Optional[int] = None) -> Optional[DoctorReportDTO]:
        """
        Get a specific report.
        
        Args:
            report_id: Report ID
            doctor_id: Optional doctor ID for access control
            
        Returns:
            Report DTO or None if not found or access denied
        """
        report = self._db.get(DoctorReportORM, report_id)
        if not report:
            return None
        
        # Access control - only creator can view
        if doctor_id and report.doctor_id != doctor_id:
            return None
        
        return self._to_dto(report)
    
    def delete_report(self, report_id: int, doctor_id: int) -> bool:
        """
        Delete a report (only by creator).
        
        Args:
            report_id: Report ID
            doctor_id: Doctor's user ID (for verification)
            
        Returns:
            True if deleted, False if not found or not authorized
        """
        try:
            report = self._db.get(DoctorReportORM, report_id)
            if not report or report.doctor_id != doctor_id:
                return False
            
            # Delete file if exists
            if report.file_path:
                try:
                    Path(report.file_path).unlink(missing_ok=True)
                except Exception:
                    pass
            
            self._db.delete(report)
            self._db.commit()
            return True
        except Exception:
            self._db.rollback()
            raise
    
    def _to_dto(self, report: DoctorReportORM) -> DoctorReportDTO:
        """Convert ORM to DTO."""
        return DoctorReportDTO(
            id=report.id,
            report_number=report.report_number,
            patient_id=report.patient_id,
            doctor_id=report.doctor_id,
            report_date=report.report_date,
            chief_complaint=report.chief_complaint,
            preliminary_diagnosis=report.preliminary_diagnosis,
            final_diagnosis=report.final_diagnosis,
            diagnosis_code_icd=report.diagnosis_code_icd,
            treatment_plan=report.treatment_plan,
            prescriptions=report.prescriptions,
            doctor_conclusion=report.doctor_conclusion,
            next_visit_date=report.next_visit_date,
            is_signed=report.is_signed,
            doctor_signature_name=report.doctor_signature_name,
            doctor_position=report.doctor_position,
            doctor_specialty=report.doctor_specialty,
            signature_date=report.signature_date,
            file_path=report.file_path,
            created_at=report.created_at,
        )
    
    def _build_medical_report_html(
        self, 
        report: DoctorReportORM, 
        patient: UserORM, 
        doctor: UserORM
    ) -> str:
        """Build professional medical report HTML."""
        
        # Helper to format value or show dash
        def fmt(val, suffix=""):
            if val is None:
                return "—"
            return f"{val}{suffix}"
        
        # Build sections conditionally
        sections = []
        
        # Header
        header = f"""
        <div class="report-header">
            <h1>МЕДИЧНИЙ ЗВІТ</h1>
            <div class="report-number">№ {report.report_number}</div>
            <div class="report-date">Дата: {report.report_date.strftime('%d.%m.%Y') if report.report_date else '—'}</div>
        </div>
        """
        sections.append(header)
        
        # Patient info
        patient_section = f"""
        <div class="section">
            <h2>Інформація про пацієнта</h2>
            <table class="info-table">
                <tr><td><strong>ПІБ:</strong></td><td>{patient.name if patient else '—'}</td></tr>
                <tr><td><strong>Вік:</strong></td><td>{fmt(patient.age if hasattr(patient, 'age') else None)}</td></tr>
                <tr><td><strong>Email:</strong></td><td>{patient.email if patient else '—'}</td></tr>
            </table>
        </div>
        """
        sections.append(patient_section)
        
        # Complaints
        if report.chief_complaint:
            sections.append(f"""
        <div class="section">
            <h2>Скарги</h2>
            <p>{report.chief_complaint}</p>
        </div>
        """)
        
        # History
        history_parts = []
        if report.history_illness:
            history_parts.append(f"<p><strong>Анамнез захворювання:</strong> {report.history_illness}</p>")
        if report.history_life:
            history_parts.append(f"<p><strong>Анамнез життя:</strong> {report.history_life}</p>")
        if history_parts:
            sections.append(f"""
        <div class="section">
            <h2>Анамнез</h2>
            {''.join(history_parts)}
        </div>
        """)
        
        # Objective examination
        exam_parts = []
        if report.general_condition:
            exam_parts.append(f"<tr><td>Загальний стан</td><td>{report.general_condition}</td></tr>")
        if report.consciousness:
            exam_parts.append(f"<tr><td>Свідомість</td><td>{report.consciousness}</td></tr>")
        if report.body_temperature:
            exam_parts.append(f"<tr><td>Температура тіла</td><td>{report.body_temperature}°C</td></tr>")
        if report.skin_condition:
            exam_parts.append(f"<tr><td>Стан шкіри</td><td>{report.skin_condition}</td></tr>")
        
        vital_parts = []
        if report.heart_rate:
            vital_parts.append(f"<tr><td>Частота серцевих скорочень</td><td>{report.heart_rate} уд/хв</td></tr>")
        if report.respiratory_rate:
            vital_parts.append(f"<tr><td>Частота дихання</td><td>{report.respiratory_rate} дих/хв</td></tr>")
        if report.blood_pressure_sys and report.blood_pressure_dia:
            vital_parts.append(f"<tr><td>Артеріальний тиск</td><td>{report.blood_pressure_sys}/{report.blood_pressure_dia} мм рт.ст.</td></tr>")
        
        cardio_parts = []
        if report.heart_sounds:
            cardio_parts.append(f"<tr><td>Тони серця</td><td>{report.heart_sounds}</td></tr>")
        if report.pulse_rhythm:
            cardio_parts.append(f"<tr><td>Ритм пульсу</td><td>{report.pulse_rhythm}</td></tr>")
        if report.pulse_character:
            cardio_parts.append(f"<tr><td>Характер пульсу</td><td>{report.pulse_character}</td></tr>")
        
        if exam_parts or vital_parts or cardio_parts:
            obj_exam = ""
            if exam_parts:
                obj_exam += f"""
                <h3>Загальний огляд</h3>
                <table class="data-table">{''.join(exam_parts)}</table>
                """
            if vital_parts:
                obj_exam += f"""
                <h3>Вітальні показники</h3>
                <table class="data-table">{''.join(vital_parts)}</table>
                """
            if cardio_parts:
                obj_exam += f"""
                <h3>Серцево-судинна система</h3>
                <table class="data-table">{''.join(cardio_parts)}</table>
                """
            
            sections.append(f"""
        <div class="section">
            <h2>Об'єктивний огляд</h2>
            {obj_exam}
        </div>
        """)
        
        # Diagnosis
        diag_parts = []
        if report.preliminary_diagnosis:
            diag_parts.append(f"<p><strong>Попередній діагноз:</strong> {report.preliminary_diagnosis}</p>")
        if report.final_diagnosis:
            diag_parts.append(f"<p><strong>Заключний діагноз:</strong> {report.final_diagnosis}</p>")
        if report.diagnosis_code_icd:
            diag_parts.append(f"<p><strong>Код за МКХ-10:</strong> {report.diagnosis_code_icd}</p>")
        if diag_parts:
            sections.append(f"""
        <div class="section diagnosis">
            <h2>Діагноз</h2>
            {''.join(diag_parts)}
        </div>
        """)
        
        # Examinations
        exam_results = []
        if report.ecg_results:
            exam_results.append(f"<p><strong>ЕКГ:</strong> {report.ecg_results}</p>")
        if report.xray_results:
            exam_results.append(f"<p><strong>Рентген:</strong> {report.xray_results}</p>")
        if report.lab_results:
            exam_results.append(f"<p><strong>Лабораторні дослідження:</strong> {report.lab_results}</p>")
        if report.other_exams:
            exam_results.append(f"<p><strong>Інші обстеження:</strong> {report.other_exams}</p>")
        if exam_results:
            sections.append(f"""
        <div class="section">
            <h2>Результати обстежень</h2>
            {''.join(exam_results)}
        </div>
        """)
        
        # Treatment
        treat_parts = []
        if report.treatment_plan:
            treat_parts.append(f"<p><strong>План лікування:</strong> {report.treatment_plan}</p>")
        if report.prescriptions:
            treat_parts.append(f"<p><strong>Призначення (лікарські препарати):</strong></p><pre>{report.prescriptions}</pre>")
        if report.procedures:
            treat_parts.append(f"<p><strong>Процедури:</strong> {report.procedures}</p>")
        if treat_parts:
            sections.append(f"""
        <div class="section treatment">
            <h2>Лікування та призначення</h2>
            {''.join(treat_parts)}
        </div>
        """)
        
        # Recommendations
        rec_parts = []
        if report.lifestyle_recommendations:
            rec_parts.append(f"<p><strong>Рекомендації щодо способу життя:</strong> {report.lifestyle_recommendations}</p>")
        if report.diet_recommendations:
            rec_parts.append(f"<p><strong>Дієтичні рекомендації:</strong> {report.diet_recommendations}</p>")
        if report.activity_recommendations:
            rec_parts.append(f"<p><strong>Рекомендації щодо активності:</strong> {report.activity_recommendations}</p>")
        if rec_parts:
            sections.append(f"""
        <div class="section">
            <h2>Рекомендації</h2>
            {''.join(rec_parts)}
        </div>
        """)
        
        # Conclusion
        if report.doctor_conclusion:
            sections.append(f"""
        <div class="section conclusion">
            <h2>Заключення лікаря</h2>
            <p>{report.doctor_conclusion}</p>
            {f"<p><strong>Прогноз:</strong> {report.prognosis}</p>" if report.prognosis else ""}
        </div>
        """)
        
        # Next visit
        if report.next_visit_date:
            sections.append(f"""
        <div class="section">
            <h2>Наступне відвідування</h2>
            <p><strong>Дата:</strong> {report.next_visit_date.strftime('%d.%m.%Y')}</p>
            {f"<p><strong>Причина:</strong> {report.next_visit_reason}</p>" if report.next_visit_reason else ""}
        </div>
        """)
        
        # Sick leave
        if report.sick_leave_required:
            sections.append(f"""
        <div class="section sick-leave">
            <h2>Листок непрацездатності</h2>
            <p><strong>Видано лікарняний на:</strong> {fmt(report.sick_leave_days, ' днів')}</p>
            <p><strong>Період:</strong> {fmt(report.sick_leave_from)} — {fmt(report.sick_leave_to)}</p>
        </div>
        """)
        
        # Signature
        signature_section = ""
        if report.is_signed:
            signature_section = f"""
        <div class="signature-section">
            <div class="signature-line">
                <p><strong>Лікар:</strong> {fmt(report.doctor_signature_name)}</p>
                <p><strong>Посада:</strong> {fmt(report.doctor_position)}</p>
                {f"<p><strong>Спеціальність:</strong> {report.doctor_specialty}</p>" if report.doctor_specialty else ""}
                <p><strong>Підписано:</strong> {report.signature_date.strftime('%d.%m.%Y %H:%M') if report.signature_date else '—'}</p>
                <div class="signature-stamp">
                    <span class="stamp-text">ПІДПИСАНО ЕЛЕКТРОННО</span>
                </div>
            </div>
        </div>
        """
        else:
            signature_section = """
        <div class="signature-section unsigned">
            <p><em>Звіт не підписано лікарем</em></p>
        </div>
        """
        
        sections.append(signature_section)
        
        # Footer
        footer = f"""
        <div class="report-footer">
            <p>Звіт згенеровано системою BP Monitor | {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
        </div>
        """
        sections.append(footer)
        
        # Full HTML document
        html = f"""<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Медичний звіт №{report.report_number}</title>
    <style>
        @page {{
            size: A4;
            margin: 20mm;
        }}
        * {{
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #1a1a1a;
            max-width: 210mm;
            margin: 0 auto;
            padding: 20mm;
            background: #fff;
        }}
        .report-header {{
            text-align: center;
            border-bottom: 3px double #2c5282;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .report-header h1 {{
            font-size: 24pt;
            color: #2c5282;
            margin: 0 0 10px 0;
            text-transform: uppercase;
            letter-spacing: 3px;
        }}
        .report-number {{
            font-size: 14pt;
            font-weight: bold;
            color: #4a5568;
            margin: 10px 0;
        }}
        .report-date {{
            font-size: 11pt;
            color: #718096;
        }}
        .section {{
            margin-bottom: 25px;
            page-break-inside: avoid;
        }}
        .section h2 {{
            font-size: 14pt;
            color: #2c5282;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 8px;
            margin-bottom: 15px;
        }}
        .section h3 {{
            font-size: 12pt;
            color: #4a5568;
            margin-top: 15px;
            margin-bottom: 10px;
        }}
        .info-table, .data-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
        }}
        .info-table td, .data-table td {{
            padding: 8px 12px;
            border-bottom: 1px solid #e2e8f0;
        }}
        .info-table td:first-child, .data-table td:first-child {{
            width: 40%;
            font-weight: 500;
            color: #4a5568;
        }}
        .diagnosis {{
            background: #ebf8ff;
            padding: 15px;
            border-left: 4px solid #3182ce;
            border-radius: 4px;
        }}
        .treatment {{
            background: #f0fff4;
            padding: 15px;
            border-left: 4px solid #38a169;
            border-radius: 4px;
        }}
        .treatment pre {{
            background: #fff;
            padding: 10px;
            border-radius: 4px;
            border: 1px solid #e2e8f0;
            font-family: inherit;
            white-space: pre-wrap;
            margin-top: 5px;
        }}
        .conclusion {{
            background: #fffaf0;
            padding: 15px;
            border-left: 4px solid #dd6b20;
            border-radius: 4px;
        }}
        .sick-leave {{
            background: #fed7d7;
            padding: 15px;
            border-left: 4px solid #c53030;
            border-radius: 4px;
        }}
        .signature-section {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #e2e8f0;
            page-break-inside: avoid;
        }}
        .signature-section.unsigned {{
            color: #a0aec0;
            font-style: italic;
        }}
        .signature-line {{
            margin-top: 20px;
        }}
        .signature-line p {{
            margin: 5px 0;
        }}
        .signature-stamp {{
            display: inline-block;
            margin-top: 20px;
            padding: 10px 30px;
            border: 3px solid #2c5282;
            border-radius: 5px;
            color: #2c5282;
            font-weight: bold;
            text-transform: uppercase;
            transform: rotate(-5deg);
            opacity: 0.8;
        }}
        .report-footer {{
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #e2e8f0;
            text-align: center;
            font-size: 9pt;
            color: #a0aec0;
        }}
        @media print {{
            body {{
                padding: 0;
            }}
            .section {{
                page-break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    {''.join(sections)}
</body>
</html>"""
        
        return html
