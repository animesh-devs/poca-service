from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, List
from datetime import datetime

from app.db.database import get_db
from app.models.user import User, UserRole
from app.models.doctor import Doctor
from app.models.suggestion import Suggestion
from app.schemas.suggestion import (
    SuggestionCreate, SuggestionUpdate, SuggestionResponse, SuggestionListResponse,
    SuggestionFeedback
)
from app.dependencies import get_current_user, get_admin_user, get_doctor_user
from app.errors import ErrorCode, create_error_response

router = APIRouter()

@router.post("", response_model=SuggestionResponse)
async def create_suggestion(
    suggestion_data: SuggestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Create a new suggestion (admin or doctor only)
    """
    try:
        # Check if user is admin or doctor
        if current_user.role != UserRole.ADMIN and current_user.role != UserRole.DOCTOR:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Admin or doctor privileges required",
                    error_code=ErrorCode.AUTH_004
                )
            )
        # Check if doctor exists
        doctor = db.query(Doctor).filter(Doctor.id == suggestion_data.doctor_id).first()
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="Doctor not found",
                    error_code=ErrorCode.RES_001
                )
            )

        # Check if current user is the doctor or an admin
        if current_user.role == UserRole.DOCTOR:
            # First try to get doctor by user_id
            current_doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()

            # If not found, try to get doctor by profile_id
            if not current_doctor and current_user.profile_id:
                current_doctor = db.query(Doctor).filter(Doctor.id == current_user.profile_id).first()

            if not current_doctor or current_doctor.id != suggestion_data.doctor_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="Not enough permissions",
                        error_code=ErrorCode.AUTH_004
                    )
                )

        # Create new suggestion
        db_suggestion = Suggestion(
            problem=suggestion_data.problem,
            description=suggestion_data.description,
            doctor_id=suggestion_data.doctor_id
        )

        db.add(db_suggestion)
        db.commit()
        db.refresh(db_suggestion)

        return db_suggestion
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

@router.get("", response_model=SuggestionListResponse)
async def get_suggestions(
    skip: int = 0,
    limit: int = 100,
    doctor_id: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get all suggestions
    """
    # Filter by doctor_id if provided
    if doctor_id:
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

        # Check if current user is the doctor or an admin
        if current_user.role == UserRole.DOCTOR:
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

        suggestions = db.query(Suggestion).filter(Suggestion.doctor_id == doctor_id).offset(skip).limit(limit).all()
        total = db.query(Suggestion).filter(Suggestion.doctor_id == doctor_id).count()
    else:
        # Admins can view all suggestions
        if current_user.role == UserRole.ADMIN:
            suggestions = db.query(Suggestion).offset(skip).limit(limit).all()
            total = db.query(Suggestion).count()
        # Patients can view suggestions for their doctors
        elif current_user.role == UserRole.PATIENT:
            # Get all doctors mapped to this patient
            from app.models.mapping import DoctorPatientMapping

            # Get doctor IDs for this patient
            mappings = db.query(DoctorPatientMapping).filter(
                DoctorPatientMapping.patient_id == current_user.profile_id
            ).all()

            doctor_ids = [mapping.doctor_id for mapping in mappings]

            # Get suggestions for these doctors
            suggestions = db.query(Suggestion).filter(
                Suggestion.doctor_id.in_(doctor_ids)
            ).offset(skip).limit(limit).all()

            total = db.query(Suggestion).filter(
                Suggestion.doctor_id.in_(doctor_ids)
            ).count()
        else:
            # Other roles can't view all suggestions
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Not enough permissions",
                    error_code=ErrorCode.AUTH_004
                )
            )

    return {
        "suggestions": suggestions,
        "total": total
    }

@router.get("/{suggestion_id}", response_model=SuggestionResponse)
async def get_suggestion(
    suggestion_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get suggestion by ID
    """
    suggestion = db.query(Suggestion).filter(Suggestion.id == suggestion_id).first()
    if not suggestion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Suggestion not found",
                error_code=ErrorCode.RES_001
            )
        )

    # Check if current user is the doctor who created the suggestion or an admin
    if current_user.role == UserRole.DOCTOR:
        # First try to get doctor by user_id
        current_doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()

        # If not found, try to get doctor by profile_id
        if not current_doctor and current_user.profile_id:
            current_doctor = db.query(Doctor).filter(Doctor.id == current_user.profile_id).first()

        if not current_doctor or current_doctor.id != suggestion.doctor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Not enough permissions",
                    error_code=ErrorCode.AUTH_004
                )
            )
    elif current_user.role not in [UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=create_error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Not enough permissions",
                error_code=ErrorCode.AUTH_004
            )
        )

    return suggestion

@router.put("/{suggestion_id}", response_model=SuggestionResponse)
async def update_suggestion(
    suggestion_id: str,
    suggestion_data: SuggestionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Update suggestion
    """
    suggestion = db.query(Suggestion).filter(Suggestion.id == suggestion_id).first()
    if not suggestion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Suggestion not found",
                error_code=ErrorCode.RES_001
            )
        )

    # Check if current user is the doctor who created the suggestion or an admin
    if current_user.role == UserRole.DOCTOR:
        # First try to get doctor by user_id
        current_doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()

        # If not found, try to get doctor by profile_id
        if not current_doctor and current_user.profile_id:
            current_doctor = db.query(Doctor).filter(Doctor.id == current_user.profile_id).first()

        if not current_doctor or current_doctor.id != suggestion.doctor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Not enough permissions",
                    error_code=ErrorCode.AUTH_004
                )
            )
    elif current_user.role not in [UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=create_error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Not enough permissions",
                error_code=ErrorCode.AUTH_004
            )
        )

    # Update suggestion fields
    for field, value in suggestion_data.model_dump(exclude_unset=True).items():
        setattr(suggestion, field, value)

    db.commit()
    db.refresh(suggestion)

    return suggestion

@router.delete("/{suggestion_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_suggestion(
    suggestion_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete suggestion
    """
    suggestion = db.query(Suggestion).filter(Suggestion.id == suggestion_id).first()
    if not suggestion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Suggestion not found",
                error_code=ErrorCode.RES_001
            )
        )

    # Check if current user is the doctor who created the suggestion or an admin
    if current_user.role == UserRole.DOCTOR:
        # First try to get doctor by user_id
        current_doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()

        # If not found, try to get doctor by profile_id
        if not current_doctor and current_user.profile_id:
            current_doctor = db.query(Doctor).filter(Doctor.id == current_user.profile_id).first()

        if not current_doctor or current_doctor.id != suggestion.doctor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Not enough permissions",
                    error_code=ErrorCode.AUTH_004
                )
            )
    elif current_user.role not in [UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=create_error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Not enough permissions",
                error_code=ErrorCode.AUTH_004
            )
        )

    db.delete(suggestion)
    db.commit()

@router.post("/{suggestion_id}/feedback", response_model=SuggestionResponse)
async def add_suggestion_feedback(
    suggestion_id: str,
    feedback_data: SuggestionFeedback,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Add feedback to a suggestion.

    This endpoint allows doctors, patients, or admins to provide feedback on a suggestion.
    Doctors can provide feedback on their own suggestions or suggestions assigned to them.
    Patients can provide feedback on suggestions from their doctors.
    Admins can provide feedback on any suggestion.

    Parameters:
    - suggestion_id: The ID of the suggestion to add feedback to
    - feedback_data: The feedback to add

    Returns:
    - The updated suggestion with the feedback added

    Raises:
    - 404: If the suggestion is not found
    - 403: If the user doesn't have permission to add feedback
    - 400: If the feedback is invalid
    """
    try:
        # Check if suggestion exists
        suggestion = db.query(Suggestion).filter(Suggestion.id == suggestion_id).first()
        if not suggestion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="Suggestion not found",
                    error_code=ErrorCode.RES_001
                )
            )

        # Check permissions based on user role
        if current_user.role == UserRole.DOCTOR:
            # First try to get doctor by user_id
            current_doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()

            # If not found, try to get doctor by profile_id
            if not current_doctor and current_user.profile_id:
                current_doctor = db.query(Doctor).filter(Doctor.id == current_user.profile_id).first()

            # Only the doctor who created the suggestion can add feedback
            if not current_doctor or current_doctor.id != suggestion.doctor_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="Not authorized to add feedback to this suggestion",
                        error_code=ErrorCode.AUTH_004
                    )
                )
        elif current_user.role == UserRole.PATIENT:
            # Patients can add feedback to suggestions from their doctors
            from app.models.mapping import DoctorPatientMapping

            # Get patient's doctors
            mappings = db.query(DoctorPatientMapping).filter(
                DoctorPatientMapping.patient_id == current_user.profile_id
            ).all()

            doctor_ids = [mapping.doctor_id for mapping in mappings]

            # Check if the suggestion's doctor is one of the patient's doctors
            if suggestion.doctor_id not in doctor_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="Not authorized to add feedback to this suggestion",
                        error_code=ErrorCode.AUTH_004
                    )
                )
        elif current_user.role != UserRole.ADMIN:
            # Other roles can't add feedback
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Not authorized to add feedback to suggestions",
                    error_code=ErrorCode.AUTH_004
                )
            )

        # Add feedback to suggestion
        suggestion.feedback = feedback_data.feedback
        suggestion.has_feedback = True
        suggestion.feedback_date = datetime.now()

        db.commit()
        db.refresh(suggestion)

        return suggestion
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
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
