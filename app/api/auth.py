from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from jose import jwt, JWTError
from typing import Any

from app.db.database import get_db
from app.models.user import User, UserRole
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.hospital import Hospital
from app.schemas.auth import (
    Token, TokenPayload, UserCreate, UserLogin, RefreshToken,
    DoctorSignup, PatientSignup, HospitalSignup
)
from app.dependencies import (
    get_admin_user, create_access_token, create_refresh_token
)
from app.config import settings
from app.errors import ErrorCode, create_error_response

from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter()

def verify_password(plain_password, hashed_password):
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Hash a password"""
    return pwd_context.hash(password)

@router.post("/signup", response_model=Token)
async def signup(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
) -> Any:
    """
    Create a new user (admin only)
    """
    # Check if user with this email already exists
    db_user = db.query(User).filter(User.email == user_data.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Email already registered",
                error_code=ErrorCode.RES_002
            )
        )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        name=user_data.name,
        role=user_data.role,
        contact=user_data.contact,
        address=user_data.address
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Create access and refresh tokens
    access_token = create_access_token(
        data={"sub": db_user.id},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_refresh_token(data={"sub": db_user.id})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": db_user.id,
        "role": db_user.role
    }

@router.post("/doctor-signup", response_model=Token)
async def doctor_signup(
    doctor_data: DoctorSignup,
    db: Session = Depends(get_db)
) -> Any:
    """
    Create a new doctor account
    """
    # Check if user with this email already exists
    db_user = db.query(User).filter(User.email == doctor_data.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Email already registered",
                error_code=ErrorCode.RES_002
            )
        )

    # Create doctor profile
    db_doctor = Doctor(
        name=doctor_data.name,
        photo=doctor_data.photo,
        designation=doctor_data.designation,
        experience=doctor_data.experience,
        details=doctor_data.details,
        contact=doctor_data.contact
    )

    db.add(db_doctor)
    db.commit()
    db.refresh(db_doctor)

    # Create user account
    hashed_password = get_password_hash(doctor_data.password)
    db_user = User(
        email=doctor_data.email,
        hashed_password=hashed_password,
        name=doctor_data.name,
        role=UserRole.DOCTOR,
        contact=doctor_data.contact,
        profile_id=db_doctor.id
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Create access and refresh tokens
    access_token = create_access_token(
        data={"sub": db_user.id},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_refresh_token(data={"sub": db_user.id})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": db_user.id,
        "role": db_user.role
    }

@router.post("/patient-signup", response_model=Token)
async def patient_signup(
    patient_data: PatientSignup,
    db: Session = Depends(get_db)
) -> Any:
    """
    Create a new patient account
    """
    # Check if user with this email already exists
    db_user = db.query(User).filter(User.email == patient_data.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Email already registered",
                error_code=ErrorCode.RES_002
            )
        )

    # Create patient profile
    db_patient = Patient(
        name=patient_data.name,
        dob=patient_data.dob,
        gender=patient_data.gender,
        contact=patient_data.contact,
        photo=patient_data.photo
    )

    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)

    # Create user account
    hashed_password = get_password_hash(patient_data.password)
    db_user = User(
        email=patient_data.email,
        hashed_password=hashed_password,
        name=patient_data.name,
        role=UserRole.PATIENT,
        contact=patient_data.contact,
        profile_id=db_patient.id
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Create access and refresh tokens
    access_token = create_access_token(
        data={"sub": db_user.id},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_refresh_token(data={"sub": db_user.id})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": db_user.id,
        "role": db_user.role
    }

@router.post("/hospital-signup", response_model=Token)
async def hospital_signup(
    hospital_data: HospitalSignup,
    db: Session = Depends(get_db)
) -> Any:
    """
    Create a new hospital account
    """
    # Check if user with this email already exists
    db_user = db.query(User).filter(User.email == hospital_data.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Email already registered",
                error_code=ErrorCode.RES_002
            )
        )

    # Create hospital profile
    db_hospital = Hospital(
        name=hospital_data.name,
        address=hospital_data.address,
        city=hospital_data.city,
        state=hospital_data.state,
        country=hospital_data.country,
        contact=hospital_data.contact,
        pin_code=hospital_data.pin_code,
        email=hospital_data.email,
        specialities=hospital_data.specialities,
        website=hospital_data.website
    )

    db.add(db_hospital)
    db.commit()
    db.refresh(db_hospital)

    # Create user account
    hashed_password = get_password_hash(hospital_data.password)
    db_user = User(
        email=hospital_data.email,
        hashed_password=hashed_password,
        name=hospital_data.name,
        role=UserRole.HOSPITAL,
        contact=hospital_data.contact,
        address=hospital_data.address,
        profile_id=db_hospital.id
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Create access and refresh tokens
    access_token = create_access_token(
        data={"sub": db_user.id},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_refresh_token(data={"sub": db_user.id})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": db_user.id,
        "role": db_user.role
    }

# Simple in-memory rate limiting for failed login attempts
# In a production environment, this should be replaced with a Redis-based solution
from datetime import datetime, timedelta
import logging

# Track failed login attempts: {email: [(timestamp, ip_address), ...]}
failed_login_attempts = {}
# Max failed attempts before temporary lockout
MAX_FAILED_ATTEMPTS = 5
# Lockout duration in minutes
LOCKOUT_DURATION_MINUTES = 15

logger = logging.getLogger(__name__)

@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    # Get client IP address for rate limiting
    client_ip = request.client.host if request.client else "unknown"

    # Check for too many failed login attempts
    email = form_data.username
    current_time = datetime.utcnow()

    if email in failed_login_attempts:
        # Clean up old attempts (older than lockout duration)
        failed_login_attempts[email] = [
            attempt for attempt in failed_login_attempts[email]
            if (current_time - attempt[0]).total_seconds() < LOCKOUT_DURATION_MINUTES * 60
        ]

        # Check if user is locked out
        if len(failed_login_attempts[email]) >= MAX_FAILED_ATTEMPTS:
            oldest_attempt = failed_login_attempts[email][0][0]
            lockout_time = oldest_attempt + timedelta(minutes=LOCKOUT_DURATION_MINUTES)

            if current_time < lockout_time:
                remaining_seconds = int((lockout_time - current_time).total_seconds())
                remaining_minutes = remaining_seconds // 60
                remaining_seconds %= 60

                logger.warning(f"Login attempt blocked due to rate limiting: {email} from {client_ip}")

                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=create_error_response(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        message=f"Too many failed login attempts. Please try again in {remaining_minutes}m {remaining_seconds}s.",
                        error_code=ErrorCode.AUTH_005
                    )
                )

    # Find user by email
    user = db.query(User).filter(User.email == email).first()

    # Check credentials
    if not user or not verify_password(form_data.password, user.hashed_password):
        # Record failed login attempt
        if email not in failed_login_attempts:
            failed_login_attempts[email] = []

        failed_login_attempts[email].append((current_time, client_ip))

        attempts_left = MAX_FAILED_ATTEMPTS - len(failed_login_attempts[email])

        logger.warning(f"Failed login attempt for {email} from {client_ip}. {attempts_left} attempts left before lockout.")

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=create_error_response(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message=f"Incorrect email or password. {attempts_left} attempts remaining before temporary lockout.",
                error_code=ErrorCode.AUTH_001
            ),
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        logger.warning(f"Login attempt for inactive user: {email} from {client_ip}")

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=create_error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="This account has been deactivated. Please contact support.",
                error_code=ErrorCode.AUTH_004
            )
        )

    # Successful login - clear failed attempts
    if email in failed_login_attempts:
        del failed_login_attempts[email]

    # Create access and refresh tokens
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_refresh_token(data={"sub": user.id})

    logger.info(f"Successful login for user {email} (ID: {user.id}) from {client_ip}")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": user.id,
        "role": user.role
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: RefreshToken,
    db: Session = Depends(get_db)
) -> Any:
    """
    Refresh access token
    """
    try:
        # Decode the refresh token
        payload = jwt.decode(
            token_data.refresh_token, settings.SECRET_KEY, algorithms=["HS256"]
        )
        token_data = TokenPayload(**payload)

        # Check if token is a refresh token
        if token_data.type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=create_error_response(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    message="Invalid token type",
                    error_code=ErrorCode.AUTH_003
                )
            )

        # Get user from database
        user = db.query(User).filter(User.id == token_data.sub).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="User not found",
                    error_code=ErrorCode.RES_001
                )
            )

        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Inactive user",
                    error_code=ErrorCode.AUTH_004
                )
            )

        # Create new access token
        access_token = create_access_token(
            data={"sub": user.id},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        return {
            "access_token": access_token,
            "refresh_token": token_data.refresh_token,
            "token_type": "bearer",
            "user_id": user.id,
            "role": user.role
        }
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=create_error_response(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Invalid token",
                error_code=ErrorCode.AUTH_003
            )
        )
