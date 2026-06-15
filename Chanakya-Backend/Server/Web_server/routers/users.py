"""
User management routes.
"""
from fastapi import APIRouter, HTTPException, status, Depends, Header, Cookie
from schemas.user import UserResponse, UserUpdate
from services.user_service import UserService
from utils.jwt import decode_access_token
from typing import Optional

router = APIRouter()


async def get_current_user_id(
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None),
) -> str:
    """
    Extract and validate user ID from Authorization header.
    
    Args:
        authorization: Authorization header (format: "Bearer <token>")
        
    Returns:
        User ID from token
        
    Raises:
        HTTPException: If token is missing or invalid
    """
    token = None

    if authorization:
        # Extract token from "Bearer <token>"
        try:
            scheme, token_val = authorization.split()
            if scheme.lower() != "bearer":
                raise ValueError("Invalid authentication scheme")
            token = token_val
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format",
                headers={"WWW-Authenticate": "Bearer"},
            )
    elif access_token:
        # Fallback to cookie named 'access_token'
        token = access_token

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header or access_token cookie required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = decode_access_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_id


@router.get("/me", response_model=UserResponse)
async def get_current_user(user_id: str = Depends(get_current_user_id)):
    """
    Get current authenticated user.
    
    Args:
        user_id: Current user ID from token
        
    Returns:
        UserResponse with user data
    """
    user = await UserService.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """
    Get user by ID.
    
    Args:
        user_id: User ID
        
    Returns:
        UserResponse with user data
    """
    user = await UserService.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    user_id: str = Depends(get_current_user_id)
):
    """
    Update current authenticated user.
    
    Args:
        user_data: User update data
        user_id: Current user ID from token
        
    Returns:
        Updated UserResponse
    """
    try:
        return await UserService.update_user(user_id, user_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Update failed: {str(e)}"
        )


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(user_id: str = Depends(get_current_user_id)):
    """
    Delete current authenticated user.
    
    Args:
        user_id: Current user ID from token
    """
    success = await UserService.delete_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
