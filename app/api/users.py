from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any

from app.db.database import get_db
from app.models.user import User
from app.schemas.user import UserUpdate, UserResponse, UserListResponse, UserListItem
from app.dependencies import get_current_user, get_admin_user
from app.errors import ErrorCode, create_error_response
from app.utils.decorators import standardize_response

router = APIRouter()

@router.get("/me", response_model=UserResponse)
@standardize_response
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get current user profile
    """
    # All authenticated users can access their own profile
    return current_user

@router.put("/me", response_model=UserResponse)
@standardize_response
async def update_current_user_profile(
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Update current user profile
    """
    # Update user fields
    for field, value in user_data.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)

    return current_user

@router.get("", response_model=UserListResponse)
@standardize_response
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user)  # Admin check, but we don't use the user
) -> Any:
    """
    Get all users (admin only)
    """
    users = db.query(User).offset(skip).limit(limit).all()
    total = db.query(User).count()

    return {
        "users": [UserListItem.model_validate(user) for user in users],
        "total": total
    }

@router.get("/{user_id}", response_model=UserResponse)
@standardize_response
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get user by ID
    """
    # Only admins can view other users
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=create_error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Invalid entity ID for this user",
                error_code=ErrorCode.AUTH_004
            )
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="User not found",
                error_code=ErrorCode.RES_001
            )
        )

    return user

@router.put("/{user_id}", response_model=UserResponse)
@standardize_response
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Update user
    """
    # Only admins can update other users
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=create_error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Invalid entity ID for this user",
                error_code=ErrorCode.AUTH_004
            )
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="User not found",
                error_code=ErrorCode.RES_001
            )
        )

    # Update user fields
    for field, value in user_data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    return user
