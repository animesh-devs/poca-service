from fastapi import Depends, HTTPException, status, Header, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, Union, List
import logging

from app.db.database import get_db
from app.config import settings
from app.models.user import User, UserRole
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.hospital import Hospital
from app.errors import ErrorCode, create_error_response

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a new JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """Create a new JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user from the token"""
    # Create a more detailed error message
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=create_error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Could not validate credentials",
            error_code=ErrorCode.AUTH_003,
            details={"WWW-Authenticate": "Bearer"}
        )
    )

    token_expired_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=create_error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Token has expired",
            error_code=ErrorCode.AUTH_003,
            details={"WWW-Authenticate": "Bearer"}
        )
    )

    invalid_token_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=create_error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Invalid token format",
            error_code=ErrorCode.AUTH_003,
            details={"WWW-Authenticate": "Bearer"}
        )
    )

    user_not_found_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=create_error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="User not found or inactive",
            error_code=ErrorCode.AUTH_003,
            details={"WWW-Authenticate": "Bearer"}
        )
    )

    try:
        # Decode the JWT token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        exp: int = payload.get("exp")

        # Check if token has required fields
        if user_id is None or token_type is None or exp is None:
            raise invalid_token_exception

        # Check if token is an access token
        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=create_error_response(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    message="Invalid token type. Expected access token.",
                    error_code=ErrorCode.AUTH_003,
                    details={"WWW-Authenticate": "Bearer"}
                )
            )

        # Check if token has expired (additional check beyond JWT's built-in check)
        if datetime.fromtimestamp(exp) < datetime.utcnow():
            raise token_expired_exception

        # Get the user from the database
        user = db.query(User).filter(User.id == user_id).first()

        # Check if user exists and is active
        if user is None:
            raise user_not_found_exception

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="User account is inactive",
                    error_code=ErrorCode.AUTH_004
                )
            )

        return user
    except jwt.ExpiredSignatureError:
        # Handle expired token specifically
        raise token_expired_exception
    except jwt.JWTError:
        # Handle general JWT errors
        raise invalid_token_exception
    except Exception:
        # Catch-all for any other errors
        raise credentials_exception

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get the current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=create_error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Inactive user",
                error_code=ErrorCode.AUTH_004
            )
        )
    return current_user

async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Get the current user if they are an admin"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=create_error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Admin privileges required",
                error_code=ErrorCode.AUTH_004
            )
        )
    return current_user

async def get_doctor_user(current_user: User = Depends(get_current_user)) -> User:
    """Get the current user if they are a doctor"""
    if current_user.role != UserRole.DOCTOR and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=create_error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Doctor privileges required",
                error_code=ErrorCode.AUTH_004
            )
        )
    return current_user

async def get_patient_user(current_user: User = Depends(get_current_user)) -> User:
    """Get the current user if they are a patient"""
    if current_user.role != UserRole.PATIENT and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=create_error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Patient privileges required",
                error_code=ErrorCode.AUTH_004
            )
        )
    return current_user

async def get_hospital_user(current_user: User = Depends(get_current_user)) -> User:
    """Get the current user if they are a hospital"""
    if current_user.role != UserRole.HOSPITAL and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=create_error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Hospital privileges required",
                error_code=ErrorCode.AUTH_004
            )
        )
    return current_user

async def get_user_entity_id(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> str:
    """
    Get and validate the user_entity_id header.

    This header contains the ID of the entity (doctor, patient, hospital) that the user
    is currently operating as. It simplifies permission checks by allowing direct comparison
    with resource IDs.

    Entity relationships:
    - User-Doctor: 1:1 mapping (doctor.id == user.profile_id)
    - User-Patient: 1:n mapping (through user_patient_relations table)
    - User-Hospital: 1:1 mapping (hospital.id == user.profile_id)

    Returns:
        str: The validated entity ID

    Raises:
        HTTPException: If the header is missing or invalid for the user's role
    """
    # Get the user_entity_id from the header
    user_entity_id = request.headers.get("user-entity-id")
    logger = logging.getLogger(__name__)

    logger.info(f"Role: {current_user.role}, User ID: {current_user.id}.")

    # If header is not provided, try to use profile_id or find the appropriate entity
    if not user_entity_id:
        # For doctor and hospital roles, we can use profile_id
        if current_user.role in [UserRole.DOCTOR, UserRole.HOSPITAL] and current_user.profile_id:
            logger.info(f"Using profile_id {current_user.profile_id} for user {current_user.id}")
            return current_user.profile_id

        # For patient role, we need to check the user_patient_relations table
        elif current_user.role == UserRole.PATIENT:
            # Import here to avoid circular imports
            from app.models.mapping import UserPatientRelation, RelationType

            # Try to find the "self" relation first
            self_relation = db.query(UserPatientRelation).filter(
                UserPatientRelation.user_id == current_user.id,
                UserPatientRelation.relation == RelationType.SELF
            ).first()

            if self_relation:
                logger.info(f"Found self patient relation {self_relation.patient_id} for user {current_user.id}")
                return self_relation.patient_id

            # If no self relation, get the first patient relation
            any_relation = db.query(UserPatientRelation).filter(
                UserPatientRelation.user_id == current_user.id
            ).first()

            if any_relation:
                logger.info(f"Found patient relation {any_relation.patient_id} for user {current_user.id}")
                return any_relation.patient_id

        # For admin role, we can use the user's ID
        elif current_user.role == UserRole.ADMIN:
            logger.info(f"Using admin user ID {current_user.id} as entity ID")
            return current_user.id

        # If we couldn't determine an entity ID, require the header
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=create_error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="user-entity-id header is required for this operation",
                error_code=ErrorCode.AUTH_004
            )
        )

    # Validate that the entity ID is appropriate for the user's role
    if current_user.role == UserRole.ADMIN:
        # Admins can use any entity ID
        logger.info(f"Admin user {current_user.id} using entity ID {user_entity_id}")
        return user_entity_id

    elif current_user.role == UserRole.DOCTOR:
        # Doctor has 1:1 mapping with user
        # Validate that the entity ID belongs to this doctor
        if current_user.profile_id and current_user.profile_id == user_entity_id:
            logger.info(f"Doctor user {current_user.id} using profile_id {user_entity_id}")
            return user_entity_id

        doctor = db.query(Doctor).filter(
            Doctor.id == user_entity_id,
            Doctor.user_id == current_user.id
        ).first()

        if not doctor:
            logger.warning(f"Invalid doctor entity ID {user_entity_id} for user {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Invalid entity ID for this user",
                    error_code=ErrorCode.AUTH_004
                )
            )

        logger.info(f"Doctor user {current_user.id} using entity ID {user_entity_id}")
        return user_entity_id

    elif current_user.role == UserRole.PATIENT:
        # Patient has 1:n mapping with user through user_patient_relations
        # Validate that the entity ID belongs to a patient related to this user
        from app.models.mapping import UserPatientRelation

        relation = db.query(UserPatientRelation).filter(
            UserPatientRelation.user_id == current_user.id,
            UserPatientRelation.patient_id == user_entity_id
        ).first()

        if not relation:
            logger.warning(f"Invalid patient entity ID {user_entity_id} for user {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Invalid entity ID for this user",
                    error_code=ErrorCode.AUTH_004
                )
            )

        logger.info(f"Patient user {current_user.id} using entity ID {user_entity_id} with relation {relation.relation}")
        return user_entity_id

    elif current_user.role == UserRole.HOSPITAL:
        # Hospital has 1:1 mapping with user
        # Validate that the entity ID belongs to this hospital
        if current_user.profile_id and current_user.profile_id == user_entity_id:
            logger.info(f"Hospital user {current_user.id} using profile_id {user_entity_id}")
            return user_entity_id

        hospital = db.query(Hospital).filter(
            Hospital.id == user_entity_id,
            Hospital.user_id == current_user.id
        ).first()

        if not hospital:
            logger.warning(f"Invalid hospital entity ID {user_entity_id} for user {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Invalid entity ID for this user",
                    error_code=ErrorCode.AUTH_004
                )
            )

        logger.info(f"Hospital user {current_user.id} using entity ID {user_entity_id}")
        return user_entity_id

    return user_entity_id

async def get_current_user_ws(token: str, db: Session) -> Optional[User]:
    """Get the current user from a WebSocket connection"""
    import logging
    logger = logging.getLogger(__name__)

    try:
        # Decode the JWT token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        exp: int = payload.get("exp")

        # Check if token has required fields
        if user_id is None or token_type is None or exp is None:
            logger.warning(f"WebSocket auth failed: Missing required fields in token")
            return None

        # Check if token is an access token
        if token_type != "access":
            logger.warning(f"WebSocket auth failed: Invalid token type - {token_type}")
            return None

        # Check if token has expired
        if datetime.fromtimestamp(exp) < datetime.utcnow():
            logger.warning(f"WebSocket auth failed: Token expired")
            return None

        # Get the user from the database
        user = db.query(User).filter(User.id == user_id).first()

        # Check if user exists and is active
        if user is None:
            logger.warning(f"WebSocket auth failed: User not found - {user_id}")
            return None

        if not user.is_active:
            logger.warning(f"WebSocket auth failed: User inactive - {user_id}")
            return None

        logger.info(f"WebSocket auth successful for user {user.email} (ID: {user_id})")
        return user
    except jwt.ExpiredSignatureError:
        logger.warning(f"WebSocket auth failed: Token expired (JWT validation)")
        return None
    except jwt.JWTError as e:
        logger.warning(f"WebSocket auth failed: JWT error - {str(e)}")
        return None
    except Exception as e:
        logger.error(f"WebSocket auth failed: Unexpected error - {str(e)}")
        return None
