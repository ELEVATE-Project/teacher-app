"""
Authentication routes.
"""
from fastapi import APIRouter, HTTPException, status, Response
from schemas.auth import LoginRequest, SignUpRequest, AuthResponse
from services.auth_service import AuthService

router = APIRouter()


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: SignUpRequest, response: Response):
    """
    Register a new user.
    
    Args:
        user_data: User signup information
        
    Returns:
        AuthResponse with user data and access token
    """
    try:
        user, token = await AuthService.signup(user_data)
        # Set token as HttpOnly cookie for browser clients
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            secure=False,  # set True in production over HTTPS
            samesite="lax",
            max_age=60 * 60 * 24 * 7,
            path="/",
        )
        return AuthResponse(user=user, token=token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Signup failed: {str(e)}"
        )


@router.post("/login", response_model=AuthResponse)
async def login(credentials: LoginRequest, response: Response):
    """
    Authenticate user and return access token.
    
    Args:
        credentials: Login credentials (email and password)
        
    Returns:
        AuthResponse with user data and access token
    """
    try:
        user, token = await AuthService.login(credentials)
        # Set token as HttpOnly cookie for browser clients
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            secure=False,  # set True in production over HTTPS
            samesite="lax",
            max_age=60 * 60 * 24 * 7,
            path="/",
        )
        return AuthResponse(user=user, token=token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )
