"""PrescriptionService - Managing doctor prescriptions for patients."""
from __future__ import annotations

import uuid
from datetime import date, datetime, time, timedelta
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import select, desc, and_, func

from app.domain.entities import PrescriptionORM, PrescriptionStatus, MedicationIntakeORM
from app.application.dto.prescription_dto import (
    PrescriptionCreateDTO, 
    PrescriptionDTO, 
    PrescriptionIntakeDTO
)


class PrescriptionService:
    """
    Service for managing doctor prescriptions.
    
    Handles:
    - Creating prescriptions with detailed schedules
    - Tracking patient notification status
    - Managing prescription lifecycle (active, completed, cancelled)
    - Generating intake schedule
    """
    
    def __init__(self, db: Session):
        self._db = db
    
    def create_prescription(self, data: PrescriptionCreateDTO) -> PrescriptionDTO:
        """
        Create a new prescription for a patient.
        
        Args:
            data: Prescription creation data
            
        Returns:
            Created prescription DTO
        """
        # Generate unique prescription number
        prescription_number = f"RX-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        
        # Calculate end date if duration provided
        end_date = None
        if data.duration_days and data.start_date:
            end_date = data.start_date + timedelta(days=data.duration_days)
        
        prescription = PrescriptionORM(
            doctor_id=data.doctor_id,
            patient_id=data.patient_id,
            prescription_number=prescription_number,
            prescription_date=data.prescription_date or date.today(),
            
            # Medication details
            medication_name=data.medication_name,
            medication_form=data.medication_form,
            dosage=data.dosage,
            
            # Schedule
            frequency_per_day=data.frequency_per_day,
            specific_times=data.specific_times,
            
            # Duration
            duration_days=data.duration_days,
            start_date=data.start_date or date.today(),
            end_date=end_date,
            
            # Administration
            take_with_food=data.take_with_food,
            take_before_food=data.take_before_food,
            take_after_food=data.take_after_food,
            special_instructions=data.special_instructions,
            
            # Doctor notes
            prescribed_for=data.prescribed_for,
            contraindications=data.contraindications,
            side_effects_notes=data.side_effects_notes,
            interactions_warning=data.interactions_warning,
            
            # Status
            status=PrescriptionStatus.ACTIVE,
            patient_notified=False,
        )
        
        self._db.add(prescription)
        self._db.commit()
        self._db.refresh(prescription)
        
        # Generate intake schedule entries
        self._generate_intake_schedule(prescription)
        
        return self._to_dto(prescription)
    
    def _generate_intake_schedule(self, prescription: PrescriptionORM) -> None:
        """Generate scheduled intake entries for a prescription."""
        if not prescription.duration_days or not prescription.start_date:
            return
        
        # Get specific times or create default schedule
        times = prescription.specific_times or []
        if not times and prescription.frequency_per_day:
            # Generate evenly spaced times
            times = self._calculate_default_times(prescription.frequency_per_day)
        
        # Create intake entries for each day and time
        current_date = prescription.start_date
        end_date = prescription.end_date or (current_date + timedelta(days=prescription.duration_days))
        
        while current_date <= end_date:
            for t in times:
                scheduled_dt = datetime.combine(current_date, t)
                intake = MedicationIntakeORM(
                    prescription_id=prescription.id,
                    patient_id=prescription.patient_id,
                    scheduled_time=scheduled_dt,
                    status="pending",
                )
                self._db.add(intake)
            
            current_date += timedelta(days=1)
        
        self._db.commit()
    
    def _calculate_default_times(self, frequency: int) -> List[time]:
        """Calculate default intake times based on frequency."""
        if frequency == 1:
            return [time(9, 0)]  # 9:00 AM
        elif frequency == 2:
            return [time(8, 0), time(20, 0)]  # 8:00 AM, 8:00 PM
        elif frequency == 3:
            return [time(8, 0), time(14, 0), time(20, 0)]  # 8 AM, 2 PM, 8 PM
        elif frequency == 4:
            return [time(8, 0), time(12, 0), time(16, 0), time(20, 0)]
        elif frequency >= 6:
            # Every 4 hours starting at 6 AM
            return [
                time(6, 0), time(10, 0), time(14, 0),
                time(18, 0), time(22, 0), time(2, 0)
            ][:frequency]
        else:
            return [time(9, 0)]
    
    def get_patient_prescriptions(
        self, 
        patient_id: int, 
        status: Optional[str] = None,
        include_completed: bool = False
    ) -> List[PrescriptionDTO]:
        """
        Get all prescriptions for a patient.
        
        Args:
            patient_id: Patient's user ID
            status: Filter by status (active, completed, cancelled)
            include_completed: Whether to include completed prescriptions
            
        Returns:
            List of prescription DTOs
        """
        stmt = select(PrescriptionORM).where(
            PrescriptionORM.patient_id == patient_id
        ).order_by(desc(PrescriptionORM.created_at))
        
        if status:
            stmt = stmt.where(PrescriptionORM.status == status)
        elif not include_completed:
            stmt = stmt.where(PrescriptionORM.status == PrescriptionStatus.ACTIVE)
        
        results = self._db.execute(stmt).scalars().all()
        return [self._to_dto(r) for r in results]
    
    def get_doctor_prescriptions(
        self, 
        doctor_id: int, 
        patient_id: Optional[int] = None
    ) -> List[PrescriptionDTO]:
        """
        Get prescriptions created by a doctor.
        
        Args:
            doctor_id: Doctor's user ID
            patient_id: Optional filter by patient
            
        Returns:
            List of prescription DTOs
        """
        stmt = select(PrescriptionORM).where(
            PrescriptionORM.doctor_id == doctor_id
        ).order_by(desc(PrescriptionORM.created_at))
        
        if patient_id:
            stmt = stmt.where(PrescriptionORM.patient_id == patient_id)
        
        results = self._db.execute(stmt).scalars().all()
        return [self._to_dto(r) for r in results]
    
    def get_prescription(self, prescription_id: int) -> Optional[PrescriptionDTO]:
        """
        Get a specific prescription.
        
        Args:
            prescription_id: Prescription ID
            
        Returns:
            Prescription DTO or None
        """
        prescription = self._db.get(PrescriptionORM, prescription_id)
        if not prescription:
            return None
        return self._to_dto(prescription)
    
    def cancel_prescription(
        self, 
        prescription_id: int, 
        doctor_id: int, 
        reason: str = None
    ) -> bool:
        """
        Cancel a prescription (only by creator).
        
        Args:
            prescription_id: Prescription ID
            doctor_id: Doctor's user ID (for verification)
            reason: Cancellation reason
            
        Returns:
            True if cancelled, False if not found or not authorized
        """
        prescription = self._db.get(PrescriptionORM, prescription_id)
        if not prescription or prescription.doctor_id != doctor_id:
            return False
        
        prescription.cancel(reason)
        
        # Also cancel pending intakes
        stmt = select(MedicationIntakeORM).where(
            and_(
                MedicationIntakeORM.prescription_id == prescription_id,
                MedicationIntakeORM.status == "pending"
            )
        )
        pending_intakes = self._db.execute(stmt).scalars().all()
        for intake in pending_intakes:
            intake.mark_skipped(f"Prescription cancelled: {reason or 'No reason given'}")
        
        self._db.commit()
        return True
    
    def mark_patient_notified(self, prescription_id: int) -> bool:
        """
        Mark that patient has been notified.
        
        Args:
            prescription_id: Prescription ID
            
        Returns:
            True if updated
        """
        prescription = self._db.get(PrescriptionORM, prescription_id)
        if not prescription:
            return False
        
        prescription.patient_notified = True
        self._db.commit()
        return True
    
    def mark_notification_seen(self, prescription_id: int) -> bool:
        """
        Mark that patient has seen the notification.
        
        Args:
            prescription_id: Prescription ID
            
        Returns:
            True if updated
        """
        prescription = self._db.get(PrescriptionORM, prescription_id)
        if not prescription:
            return False
        
        prescription.notification_seen_at = datetime.utcnow()
        self._db.commit()
        return True
    
    def accept_prescription(self, prescription_id: int, patient_id: int) -> bool:
        """
        Patient accepts a prescription.
        
        Args:
            prescription_id: Prescription ID
            patient_id: Patient's user ID (for verification)
            
        Returns:
            True if accepted
        """
        prescription = self._db.get(PrescriptionORM, prescription_id)
        if not prescription or prescription.patient_id != patient_id:
            return False
        
        prescription.notification_accepted = True
        prescription.notification_seen_at = datetime.utcnow()
        self._db.commit()
        return True
    
    def get_pending_intakes(
        self, 
        patient_id: int, 
        from_time: Optional[datetime] = None,
        to_time: Optional[datetime] = None
    ) -> List[PrescriptionIntakeDTO]:
        """
        Get pending medication intakes for a patient.
        
        Args:
            patient_id: Patient's user ID
            from_time: Start time filter
            to_time: End time filter
            
        Returns:
            List of intake DTOs
        """
        stmt = (
            select(MedicationIntakeORM)
            .join(PrescriptionORM, MedicationIntakeORM.prescription_id == PrescriptionORM.id)
            .where(
                and_(
                    MedicationIntakeORM.patient_id == patient_id,
                    MedicationIntakeORM.status == "pending",
                    PrescriptionORM.status != "cancelled"  # Exclude cancelled prescriptions
                )
            )
            .order_by(MedicationIntakeORM.scheduled_time)
        )
        
        if from_time:
            stmt = stmt.where(MedicationIntakeORM.scheduled_time >= from_time)
        if to_time:
            stmt = stmt.where(MedicationIntakeORM.scheduled_time <= to_time)
        
        results = self._db.execute(stmt).scalars().all()
        return [self._intake_to_dto(r) for r in results]
    
    def get_missed_intakes(
        self, 
        patient_id: int, 
        since: Optional[datetime] = None
    ) -> List[PrescriptionIntakeDTO]:
        """
        Get missed medication intakes for a patient.
        
        Args:
            patient_id: Patient's user ID
            since: Look back from this time
            
        Returns:
            List of missed intake DTOs
        """
        since = since or datetime.utcnow() - timedelta(days=7)
        
        stmt = (
            select(MedicationIntakeORM)
            .join(PrescriptionORM, MedicationIntakeORM.prescription_id == PrescriptionORM.id)
            .where(
                and_(
                    MedicationIntakeORM.patient_id == patient_id,
                    MedicationIntakeORM.status.in_(["missed", "late"]),
                    MedicationIntakeORM.scheduled_time >= since,
                    PrescriptionORM.status != "cancelled"  # Exclude cancelled prescriptions
                )
            )
            .order_by(desc(MedicationIntakeORM.scheduled_time))
        )
        
        results = self._db.execute(stmt).scalars().all()
        return [self._intake_to_dto(r) for r in results]
    
    def record_intake(
        self, 
        intake_id: int, 
        patient_id: int,
        taken_at: Optional[datetime] = None,
        dosage: Optional[float] = None,
        notes: Optional[str] = None
    ) -> bool:
        """
        Record that patient took medication.
        
        Args:
            intake_id: Intake schedule entry ID
            patient_id: Patient's user ID (for verification)
            taken_at: When taken (defaults to now)
            dosage: Actual dosage taken
            notes: Notes
            
        Returns:
            True if recorded
        """
        intake = self._db.get(MedicationIntakeORM, intake_id)
        if not intake or intake.patient_id != patient_id:
            return False
        
        taken_at = taken_at or datetime.utcnow()
        intake.record_intake(taken_at, dosage, notes)
        
        self._db.commit()
        return True
    
    def skip_intake(
        self, 
        intake_id: int, 
        patient_id: int,
        reason: Optional[str] = None
    ) -> bool:
        """
        Mark an intake as intentionally skipped.
        
        Args:
            intake_id: Intake schedule entry ID
            patient_id: Patient's user ID (for verification)
            reason: Reason for skipping
            
        Returns:
            True if marked
        """
        intake = self._db.get(MedicationIntakeORM, intake_id)
        if not intake or intake.patient_id != patient_id:
            return False
        
        intake.mark_skipped(reason)
        
        self._db.commit()
        return True
    
    def get_adherence_stats(
        self, 
        patient_id: int, 
        prescription_id: Optional[int] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get medication adherence statistics.
        
        Args:
            patient_id: Patient's user ID
            prescription_id: Optional specific prescription
            days: Number of days to analyze
            
        Returns:
            Adherence statistics dictionary
        """
        from_time = datetime.utcnow() - timedelta(days=days)
        
        # Build query - always exclude cancelled prescriptions
        stmt = (
            select(MedicationIntakeORM)
            .join(PrescriptionORM, MedicationIntakeORM.prescription_id == PrescriptionORM.id)
            .where(
                and_(
                    MedicationIntakeORM.patient_id == patient_id,
                    MedicationIntakeORM.scheduled_time >= from_time,
                    PrescriptionORM.status != "cancelled"  # Exclude cancelled prescriptions
                )
            )
        )
        
        if prescription_id:
            stmt = stmt.where(MedicationIntakeORM.prescription_id == prescription_id)
        
        results = self._db.execute(stmt).scalars().all()
        
        total = len(results)
        if total == 0:
            return {"total": 0, "taken": 0, "missed": 0, "skipped": 0, "adherence_rate": 0.0}
        
        taken = sum(1 for r in results if r.status in ["taken", "early"])
        late = sum(1 for r in results if r.status == "late")
        missed = sum(1 for r in results if r.status == "missed")
        skipped = sum(1 for r in results if r.status == "skipped")
        
        adherence_rate = (taken + late) / total * 100 if total > 0 else 0
        
        return {
            "total": total,
            "taken": taken,
            "late": late,
            "missed": missed,
            "skipped": skipped,
            "adherence_rate": round(adherence_rate, 1),
            "days_analyzed": days,
        }
    
    def get_intake_calendar_data(
        self, 
        patient_id: int,
        year: int,
        month: int
    ) -> Dict[str, Any]:
        """
        Get calendar data for medication adherence visualization.
        
        Returns data in format suitable for GitHub-style contribution graph.
        
        Args:
            patient_id: Patient's user ID
            year: Year to get data for
            month: Month to get data for
            
        Returns:
            Calendar data with daily adherence levels
        """
        from calendar import monthrange
        
        # Get month bounds
        _, days_in_month = monthrange(year, month)
        start_date = date(year, month, 1)
        end_date = date(year, month, days_in_month)
        
        start_dt = datetime.combine(start_date, time.min)
        end_dt = datetime.combine(end_date, time.max)
        
        # Get all intakes for the month - excluding cancelled prescriptions
        stmt = (
            select(MedicationIntakeORM)
            .join(PrescriptionORM, MedicationIntakeORM.prescription_id == PrescriptionORM.id)
            .where(
                and_(
                    MedicationIntakeORM.patient_id == patient_id,
                    MedicationIntakeORM.scheduled_time >= start_dt,
                    MedicationIntakeORM.scheduled_time <= end_dt,
                    PrescriptionORM.status != "cancelled"  # Exclude cancelled prescriptions
                )
            )
        )
        
        results = self._db.execute(stmt).scalars().all()
        
        # Group by date
        daily_data = {}
        for intake in results:
            day_key = intake.scheduled_time.strftime("%Y-%m-%d")
            if day_key not in daily_data:
                daily_data[day_key] = {"total": 0, "taken": 0, "missed": 0, "skipped": 0, "intakes": []}
            
            daily_data[day_key]["total"] += 1
            if intake.status in ["taken", "early", "late"]:
                daily_data[day_key]["taken"] += 1
            elif intake.status == "missed":
                daily_data[day_key]["missed"] += 1
            elif intake.status == "skipped":
                daily_data[day_key]["skipped"] += 1
            
            # Add intake details for calendar display
            med_name = None
            dosage = None
            if intake.prescription:
                med_name = intake.prescription.medication_name
                dosage = intake.prescription.dosage
            elif intake.medication:
                med_name = intake.medication.name
                dosage = f"{intake.medication.dosage} {intake.medication.unit}"
            
            daily_data[day_key]["intakes"].append({
                "medication_name": med_name or "Невідомо",
                "dosage": dosage or "",
                "scheduled_time": intake.scheduled_time.isoformat() if intake.scheduled_time else None,
                "taken_at": intake.taken_at.isoformat() if intake.taken_at else None,
                "status": intake.status
            })
        
        # Calculate adherence levels (0-4) for each day
        calendar_days = []
        for day in range(1, days_in_month + 1):
            day_date = date(year, month, day)
            day_key = day_date.strftime("%Y-%m-%d")
            
            day_data = daily_data.get(day_key, {"total": 0, "taken": 0, "missed": 0, "skipped": 0})
            
            if day_data["total"] == 0:
                level = 0  # No medications scheduled
            else:
                adherence = day_data["taken"] / day_data["total"]
                if adherence >= 1.0:
                    level = 4  # Perfect
                elif adherence >= 0.75:
                    level = 3  # Good
                elif adherence >= 0.5:
                    level = 2  # Fair
                else:
                    level = 1  # Poor
            
            calendar_days.append({
                "date": day_key,
                "day": day,
                "level": level,
                "total": day_data["total"],
                "taken": day_data["taken"],
                "missed": day_data["missed"],
                "skipped": day_data["skipped"],
                "intakes": day_data.get("intakes", []),
            })
        
        return {
            "year": year,
            "month": month,
            "days": calendar_days,
        }
    
    def auto_mark_missed_intakes(self, patient_id: int):
        """
        Automatically mark overdue intakes as missed.
        
        Args:
            patient_id: Patient's user ID
        """
        from datetime import datetime, timedelta
        
        now = datetime.utcnow()
        # Mark intakes as missed if they're overdue by more than 1 hour
        overdue_threshold = now - timedelta(hours=1)
        
        # Find pending intakes that are overdue
        stmt = (
            select(MedicationIntakeORM)
            .join(PrescriptionORM, MedicationIntakeORM.prescription_id == PrescriptionORM.id)
            .where(
                and_(
                    MedicationIntakeORM.patient_id == patient_id,
                    MedicationIntakeORM.status == "pending",
                    MedicationIntakeORM.scheduled_time < overdue_threshold,
                    PrescriptionORM.status != "cancelled"
                )
            )
        )
        
        results = self._db.execute(stmt).scalars().all()
        
        # Mark them as missed
        for intake in results:
            intake.mark_missed()
            intake.taken_at = None  # Ensure taken_at is None for missed
            intake.taken_on_time = False
            intake.minutes_delay = int((now - intake.scheduled_time).total_seconds() / 60)
        
        if results:
            self._db.commit()
    
    def _to_dto(self, prescription: PrescriptionORM) -> PrescriptionDTO:
        """Convert ORM to DTO."""
        return PrescriptionDTO(
            id=prescription.id,
            prescription_number=prescription.prescription_number,
            doctor_id=prescription.doctor_id,
            patient_id=prescription.patient_id,
            prescription_date=prescription.prescription_date,
            medication_name=prescription.medication_name,
            medication_form=prescription.medication_form,
            dosage=prescription.dosage,
            frequency_per_day=prescription.frequency_per_day,
            specific_times=[t.isoformat() for t in prescription.specific_times] if prescription.specific_times else None,
            duration_days=prescription.duration_days,
            start_date=prescription.start_date,
            end_date=prescription.end_date,
            take_with_food=prescription.take_with_food,
            special_instructions=prescription.special_instructions,
            prescribed_for=prescription.prescribed_for,
            status=prescription.status,
            patient_notified=prescription.patient_notified,
            notification_seen_at=prescription.notification_seen_at,
            notification_accepted=prescription.notification_accepted,
            created_at=prescription.created_at,
        )
    
    def _intake_to_dto(self, intake: MedicationIntakeORM) -> PrescriptionIntakeDTO:
        """Convert Intake ORM to DTO."""
        # Get medication name from prescription if available
        med_name = None
        dosage = None
        if intake.prescription:
            med_name = intake.prescription.medication_name
            dosage = intake.prescription.dosage
        elif intake.medication:
            med_name = intake.medication.name
            dosage = f"{intake.medication.dosage} {intake.medication.unit}"
        
        return PrescriptionIntakeDTO(
            id=intake.id,
            prescription_id=intake.prescription_id,
            medication_id=intake.medication_id,
            medication_name=med_name,
            dosage=dosage,
            scheduled_time=intake.scheduled_time,
            taken_at=intake.taken_at,
            status=intake.status,
            taken_on_time=intake.taken_on_time,
            minutes_delay=intake.minutes_delay,
        )
