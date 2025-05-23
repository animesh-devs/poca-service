from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, List
from sqlalchemy import or_, and_

from app.db.database import get_db
from app.models.user import User, UserRole
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.hospital import Hospital
from app.models.appointment import Appointment, AppointmentStatus, AppointmentType
from app.models.mapping import DoctorPatientMapping, HospitalPatientMapping, HospitalDoctorMapping
from app.schemas.appointment import (
    AppointmentCreate, AppointmentUpdate, AppointmentResponse, AppointmentListResponse,
    AppointmentStatusUpdate, AppointmentCancellation
)
from app.dependencies import get_current_user, get_admin_user, get_doctor_user, get_patient_user, get_hospital_user
from app.errors import ErrorCode, create_error_response
from app.utils.decorators import standardize_response

router = APIRouter()

@router.post("", response_model=AppointmentResponse)
@standardize_response
async def create_appointment(
    appointment_data: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Create a new appointment
    """
    # Check if doctor exists
    doctor = db.query(Doctor).filter(Doctor.id == appointment_data.doctor_id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Doctor not found",
                error_code=ErrorCode.RES_001
            )
        )

    # Check if patient exists
    patient = db.query(Patient).filter(Patient.id == appointment_data.patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Patient not found",
                error_code=ErrorCode.RES_001
            )
        )

    # Check if hospital exists (if provided)
    if appointment_data.hospital_id:
        hospital = db.query(Hospital).filter(Hospital.id == appointment_data.hospital_id).first()
        if not hospital:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="Hospital not found",
                    error_code=ErrorCode.RES_001
                )
            )

    # Create new appointment
    db_appointment = Appointment(
        doctor_id=appointment_data.doctor_id,
        patient_id=appointment_data.patient_id,
        hospital_id=appointment_data.hospital_id,
        time_slot=appointment_data.time_slot,
        type=appointment_data.type,
        status=AppointmentStatus.SCHEDULED,
        extras=appointment_data.extras
    )

    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)

    return db_appointment

@router.get("", response_model=AppointmentListResponse)
@standardize_response
async def get_appointments(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
) -> Any:
    """
    Get all appointments (admin only)
    """
    appointments = db.query(Appointment).offset(skip).limit(limit).all()
    total = db.query(Appointment).count()

    return {
        "appointments": appointments,
        "total": total
    }

@router.get("/{appointment_id}", response_model=AppointmentResponse)
@standardize_response
async def get_appointment(
    appointment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get appointment by ID
    """
    try:
        appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="Appointment not found",
                    error_code=ErrorCode.RES_001
                )
            )

        # Check if user has access to this appointment
        if current_user.role == UserRole.ADMIN:
            # Admins can access any appointment
            pass
        elif current_user.role == UserRole.DOCTOR:
            # Doctors can access their appointments
            # First try to get doctor by user_id
            doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()

            # If not found, try to get doctor by profile_id
            if not doctor and current_user.profile_id:
                doctor = db.query(Doctor).filter(Doctor.id == current_user.profile_id).first()

            if not doctor or doctor.id != appointment.doctor_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="Not enough permissions",
                        error_code=ErrorCode.AUTH_004
                    )
                )
        elif current_user.role == UserRole.PATIENT:
            # Patients can access their appointments
            # First try to get patient by profile_id (preferred way)
            if current_user.profile_id:
                patient = db.query(Patient).filter(Patient.id == current_user.profile_id).first()
            else:
                # Try to find patient by user_id
                patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()

                # If not found, try to find by direct ID match
                if not patient:
                    patient = db.query(Patient).filter(Patient.id == current_user.id).first()

            if not patient or patient.id != appointment.patient_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="Not enough permissions",
                        error_code=ErrorCode.AUTH_004
                    )
                )
        elif current_user.role == UserRole.HOSPITAL:
            # Hospitals can access appointments at their facility
            # First try to get hospital by user_id
            hospital = db.query(Hospital).filter(Hospital.user_id == current_user.id).first()

            # If not found, try to get hospital by profile_id
            if not hospital and current_user.profile_id:
                hospital = db.query(Hospital).filter(Hospital.id == current_user.profile_id).first()

            if not hospital or hospital.id != appointment.hospital_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="Not enough permissions",
                        error_code=ErrorCode.AUTH_004
                    )
                )
        else:
            # Other roles can't access appointments
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Not enough permissions",
                    error_code=ErrorCode.AUTH_004
                )
            )

        return appointment
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=f"An error occurred: {str(e)}",
                error_code=ErrorCode.SRV_001
            )
        )

@router.put("/{appointment_id}", response_model=AppointmentResponse)
@standardize_response
async def update_appointment(
    appointment_id: str,
    appointment_data: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Update appointment
    """
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Appointment not found",
                error_code=ErrorCode.RES_001
            )
        )

    # Check if user has access to update this appointment
    if current_user.role == UserRole.ADMIN:
        # Admins can update any appointment
        pass
    elif current_user.role == UserRole.DOCTOR:
        # Doctors can update their appointments
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        if not doctor or doctor.id != appointment.doctor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Not enough permissions",
                    error_code=ErrorCode.AUTH_004
                )
            )
    else:
        # Patients and hospitals can't update appointments
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=create_error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Not enough permissions",
                error_code=ErrorCode.AUTH_004
            )
        )

    # Update appointment fields
    for field, value in appointment_data.model_dump(exclude_unset=True).items():
        setattr(appointment, field, value)

    db.commit()
    db.refresh(appointment)

    return appointment

@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_appointment(
    appointment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cancel appointment
    """
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Appointment not found",
                error_code=ErrorCode.RES_001
            )
        )

    # Check if user has access to cancel this appointment
    if current_user.role == UserRole.ADMIN:
        # Admins can cancel any appointment
        pass
    elif current_user.role == UserRole.DOCTOR:
        # Doctors can cancel their appointments
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        if not doctor or doctor.id != appointment.doctor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Not enough permissions",
                    error_code=ErrorCode.AUTH_004
                )
            )
    elif current_user.role == UserRole.PATIENT:
        # Patients can cancel their appointments
        patient_id = None

        # First try to get patient by profile_id (preferred way)
        if current_user.profile_id:
            patient_id = current_user.profile_id
        else:
            # Try to find patient by user_id
            patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()

            # If not found, try to find by direct ID match
            if not patient:
                patient = db.query(Patient).filter(Patient.id == current_user.id).first()

            if patient:
                patient_id = patient.id

        if not patient_id or patient_id != appointment.patient_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Not enough permissions",
                    error_code=ErrorCode.AUTH_004
                )
            )
    else:
        # Hospitals can't cancel appointments
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=create_error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Not enough permissions",
                error_code=ErrorCode.AUTH_004
            )
        )

    # Update appointment status to cancelled
    appointment.status = AppointmentStatus.CANCELLED
    appointment.cancelled_by = current_user.id

    db.commit()

@router.put("/{appointment_id}/cancel", response_model=AppointmentResponse)
@standardize_response
async def cancel_appointment_with_reason(
    appointment_id: str,
    cancellation_data: AppointmentCancellation,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Cancel appointment with reason
    """
    try:
        appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="Appointment not found",
                    error_code=ErrorCode.RES_001
                )
            )

        # Check if user has access to cancel this appointment
        if current_user.role == UserRole.ADMIN:
            # Admins can cancel any appointment
            pass
        elif current_user.role == UserRole.DOCTOR:
            # Doctors can cancel their appointments
            # First try to get doctor by user_id
            doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()

            # If not found, try to get doctor by profile_id
            if not doctor and current_user.profile_id:
                doctor = db.query(Doctor).filter(Doctor.id == current_user.profile_id).first()

            if not doctor or doctor.id != appointment.doctor_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="Not enough permissions",
                        error_code=ErrorCode.AUTH_004
                    )
                )
        elif current_user.role == UserRole.PATIENT:
            # Patients can cancel their appointments
            # First try to get patient by profile_id (preferred way)
            if current_user.profile_id:
                patient = db.query(Patient).filter(Patient.id == current_user.profile_id).first()
            else:
                # Try to find patient by user_id
                patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()

                # If not found, try to find by direct ID match
                if not patient:
                    patient = db.query(Patient).filter(Patient.id == current_user.id).first()

            if not patient or patient.id != appointment.patient_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="Not enough permissions",
                        error_code=ErrorCode.AUTH_004
                    )
                )
        elif current_user.role == UserRole.HOSPITAL:
            # Hospitals can cancel appointments at their facility
            # First try to get hospital by user_id
            hospital = db.query(Hospital).filter(Hospital.user_id == current_user.id).first()

            # If not found, try to get hospital by profile_id
            if not hospital and current_user.profile_id:
                hospital = db.query(Hospital).filter(Hospital.id == current_user.profile_id).first()

            if not hospital or hospital.id != appointment.hospital_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="Not enough permissions",
                        error_code=ErrorCode.AUTH_004
                    )
                )
        else:
            # Other roles can't cancel appointments
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Not enough permissions",
                    error_code=ErrorCode.AUTH_004
                )
            )

        # Update appointment status to cancelled with reason
        appointment.status = AppointmentStatus.CANCELLED
        appointment.cancelled_by = current_user.id
        appointment.cancellation_reason = cancellation_data.cancellation_reason

        db.commit()
        db.refresh(appointment)

        return appointment
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=f"An error occurred: {str(e)}",
                error_code=ErrorCode.SRV_001
            )
        )

@router.get("/doctor/{doctor_id}", response_model=AppointmentListResponse)
@standardize_response
async def get_doctor_appointments(
    doctor_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get all appointments for a doctor
    """
    try:
        # Check if doctor exists
        doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="Doctor not found",
                    error_code=ErrorCode.RES_001
                )
            )

        # Check if user has access to view these appointments
        if current_user.role == UserRole.ADMIN:
            # Admins can view any doctor's appointments
            pass
        elif current_user.role == UserRole.DOCTOR:
            # Doctors can only view their own appointments
            # First try to get doctor by user_id
            current_doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()

            # If not found, try to get doctor by profile_id
            if not current_doctor and current_user.profile_id:
                current_doctor = db.query(Doctor).filter(Doctor.id == current_user.profile_id).first()

            if not current_doctor or current_doctor.id != doctor_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="Not enough permissions",
                        error_code=ErrorCode.AUTH_004
                    )
                )
        elif current_user.role == UserRole.PATIENT:
            # Patients can view appointments with their doctors
            # First try to get patient by profile_id (preferred way)
            if current_user.profile_id:
                patient = db.query(Patient).filter(Patient.id == current_user.profile_id).first()
            else:
                # Try to find patient by user_id
                patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()

                # If not found, try to find by direct ID match
                if not patient:
                    patient = db.query(Patient).filter(Patient.id == current_user.id).first()

            if not patient:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="Not enough permissions",
                        error_code=ErrorCode.AUTH_004
                    )
                )

            # Check if doctor is associated with this patient
            doctor_patient = db.query(DoctorPatientMapping).filter(
                DoctorPatientMapping.doctor_id == doctor_id,
                DoctorPatientMapping.patient_id == patient.id
            ).first()

            if not doctor_patient:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="Not enough permissions",
                        error_code=ErrorCode.AUTH_004
                    )
                )
        elif current_user.role == UserRole.HOSPITAL:
            # Hospitals can view appointments for doctors at their facility
            # First try to get hospital by user_id
            hospital = db.query(Hospital).filter(Hospital.user_id == current_user.id).first()

            # If not found, try to get hospital by profile_id
            if not hospital and current_user.profile_id:
                hospital = db.query(Hospital).filter(Hospital.id == current_user.profile_id).first()

            if not hospital:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="Not enough permissions",
                        error_code=ErrorCode.AUTH_004
                    )
                )

            # Check if doctor is associated with this hospital
            hospital_doctor = db.query(HospitalDoctorMapping).filter(
                HospitalDoctorMapping.hospital_id == hospital.id,
                HospitalDoctorMapping.doctor_id == doctor_id
            ).first()

            if not hospital_doctor:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="Not enough permissions",
                        error_code=ErrorCode.AUTH_004
                    )
                )
        else:
            # Other roles can't view doctor appointments
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Not enough permissions",
                    error_code=ErrorCode.AUTH_004
                )
            )

        appointments = db.query(Appointment).filter(Appointment.doctor_id == doctor_id).offset(skip).limit(limit).all()
        total = db.query(Appointment).filter(Appointment.doctor_id == doctor_id).count()

        return {
            "appointments": appointments,
            "total": total
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=f"An error occurred: {str(e)}",
                error_code=ErrorCode.SRV_001
            )
        )

@router.get("/patient/{patient_id}", response_model=AppointmentListResponse)
@standardize_response
async def get_patient_appointments(
    patient_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get all appointments for a patient
    """
    try:
        # Check if patient exists
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="Patient not found",
                    error_code=ErrorCode.RES_001
                )
            )

        # Check if user has access to view these appointments
        if current_user.role == UserRole.ADMIN:
            # Admins can view any patient's appointments
            pass
        elif current_user.role == UserRole.DOCTOR:
            # Doctors can view appointments for their patients
            # First try to get doctor by user_id
            doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()

            # If not found, try to get doctor by profile_id
            if not doctor and current_user.profile_id:
                doctor = db.query(Doctor).filter(Doctor.id == current_user.profile_id).first()

            if not doctor:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="Not enough permissions",
                        error_code=ErrorCode.AUTH_004
                    )
                )

            # Check if patient is associated with this doctor
            doctor_patient = db.query(DoctorPatientMapping).filter(
                DoctorPatientMapping.doctor_id == doctor.id,
                DoctorPatientMapping.patient_id == patient_id
            ).first()

            if not doctor_patient:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="Not enough permissions",
                        error_code=ErrorCode.AUTH_004
                    )
                )
        elif current_user.role == UserRole.PATIENT:
            # Patients can only view their own appointments
            # First try to get patient by profile_id (preferred way)
            if current_user.profile_id:
                current_patient = db.query(Patient).filter(Patient.id == current_user.profile_id).first()
            else:
                # Try to find patient by user_id
                current_patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()

                # If not found, try to find by direct ID match
                if not current_patient:
                    current_patient = db.query(Patient).filter(Patient.id == current_user.id).first()

            if not current_patient or current_patient.id != patient_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="Not enough permissions",
                        error_code=ErrorCode.AUTH_004
                    )
                )
        elif current_user.role == UserRole.HOSPITAL:
            # Hospitals can view appointments for their patients
            # First try to get hospital by user_id
            hospital = db.query(Hospital).filter(Hospital.user_id == current_user.id).first()

            # If not found, try to get hospital by profile_id
            if not hospital and current_user.profile_id:
                hospital = db.query(Hospital).filter(Hospital.id == current_user.profile_id).first()

            if not hospital:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="Not enough permissions",
                        error_code=ErrorCode.AUTH_004
                    )
                )

            # Check if patient is associated with this hospital
            hospital_patient = db.query(HospitalPatientMapping).filter(
                HospitalPatientMapping.hospital_id == hospital.id,
                HospitalPatientMapping.patient_id == patient_id
            ).first()

            if not hospital_patient:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="Not enough permissions",
                        error_code=ErrorCode.AUTH_004
                    )
                )
        else:
            # Other roles can't view patient appointments
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Not enough permissions",
                    error_code=ErrorCode.AUTH_004
                )
            )

        appointments = db.query(Appointment).filter(Appointment.patient_id == patient_id).offset(skip).limit(limit).all()
        total = db.query(Appointment).filter(Appointment.patient_id == patient_id).count()

        return {
            "appointments": appointments,
            "total": total
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=f"An error occurred: {str(e)}",
                error_code=ErrorCode.SRV_001
            )
        )

@router.get("/hospital/{hospital_id}", response_model=AppointmentListResponse)
async def get_hospital_appointments(
    hospital_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get all appointments for a hospital
    """
    # Check if hospital exists
    hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Hospital not found",
                error_code=ErrorCode.RES_001
            )
        )

    # Check if user has access to view these appointments
    if current_user.role == UserRole.ADMIN:
        # Admins can view any hospital's appointments
        pass
    elif current_user.role == UserRole.HOSPITAL:
        # Hospitals can only view their own appointments
        current_hospital = db.query(Hospital).filter(Hospital.user_id == current_user.id).first()
        if not current_hospital or current_hospital.id != hospital_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Not enough permissions",
                    error_code=ErrorCode.AUTH_004
                )
            )
    else:
        # Doctors and patients can't view all hospital appointments
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=create_error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Not enough permissions",
                error_code=ErrorCode.AUTH_004
            )
        )

    appointments = db.query(Appointment).filter(Appointment.hospital_id == hospital_id).offset(skip).limit(limit).all()
    total = db.query(Appointment).filter(Appointment.hospital_id == hospital_id).count()

    return {
        "appointments": appointments,
        "total": total
    }

@router.put("/{appointment_id}/status", response_model=AppointmentResponse)
async def update_appointment_status(
    appointment_id: str,
    status_data: AppointmentStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Update appointment status
    """
    try:
        appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="Appointment not found",
                    error_code=ErrorCode.RES_001
                )
            )

        # Check if user has access to update this appointment status
        if current_user.role == UserRole.ADMIN:
            # Admins can update any appointment status
            pass
        elif current_user.role == UserRole.DOCTOR:
            # Doctors can update their appointment status
            # First try to get doctor by user_id
            doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()

            # If not found, try to get doctor by profile_id
            if not doctor and current_user.profile_id:
                doctor = db.query(Doctor).filter(Doctor.id == current_user.profile_id).first()

            if not doctor or doctor.id != appointment.doctor_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="Not enough permissions",
                        error_code=ErrorCode.AUTH_004
                    )
                )
        elif current_user.role == UserRole.HOSPITAL:
            # Hospitals can update appointment status for appointments at their facility
            # First try to get hospital by user_id
            hospital = db.query(Hospital).filter(Hospital.user_id == current_user.id).first()

            # If not found, try to get hospital by profile_id
            if not hospital and current_user.profile_id:
                hospital = db.query(Hospital).filter(Hospital.id == current_user.profile_id).first()

            if not hospital or hospital.id != appointment.hospital_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="Not enough permissions",
                        error_code=ErrorCode.AUTH_004
                    )
                )
        elif current_user.role == UserRole.PATIENT:
            # Patients can only cancel their own appointments
            # First try to get patient by profile_id (preferred way)
            if current_user.profile_id:
                patient = db.query(Patient).filter(Patient.id == current_user.profile_id).first()
            else:
                # Try to find patient by user_id
                patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()

                # If not found, try to find by direct ID match
                if not patient:
                    patient = db.query(Patient).filter(Patient.id == current_user.id).first()

            if not patient or patient.id != appointment.patient_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="Not enough permissions",
                        error_code=ErrorCode.AUTH_004
                    )
                )

            # Patients can only cancel appointments, not change to other statuses
            if status_data.status != AppointmentStatus.CANCELLED:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="Patients can only cancel appointments",
                        error_code=ErrorCode.AUTH_004
                    )
                )
        else:
            # Other roles can't update appointment status
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Not enough permissions",
                    error_code=ErrorCode.AUTH_004
                )
            )

        # Update appointment status
        appointment.status = status_data.status

        # If cancelling, record who cancelled it
        if status_data.status == AppointmentStatus.CANCELLED:
            appointment.cancelled_by = current_user.id
            if hasattr(status_data, 'cancellation_reason') and status_data.cancellation_reason:
                appointment.cancellation_reason = status_data.cancellation_reason

        db.commit()
        db.refresh(appointment)

        return appointment
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=f"An error occurred: {str(e)}",
                error_code=ErrorCode.SRV_001
            )
        )