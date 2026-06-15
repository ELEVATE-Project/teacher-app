"""
Authentication service - handles login and signup logic.
"""
from fastapi import HTTPException, status
from datetime import datetime
from models.user import User
from schemas.auth import SignUpRequest, LoginRequest
from schemas.user import UserResponse
from utils.password import hash_password, verify_password
from utils.jwt import create_access_token
from beanie.exceptions import RevisionIdWasChanged


class AuthService:
    """Service for authentication operations."""
    
    @staticmethod
    async def signup(user_data: SignUpRequest) -> tuple[UserResponse, str]:
        """
        Register a new user.
        
        Args:
            user_data: User signup data
            
        Returns:
            Tuple of (UserResponse, access_token)
            
        Raises:
            HTTPException: If email already exists or passwords don't match
        """
        # Validate password confirmation
        if user_data.password != user_data.confirmPassword:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passwords do not match"
            )
        
        # Check if user already exists
        existing_user = await User.find_one(User.email == user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        hashed_pwd = hash_password(user_data.password[:72])
        
        new_user = User(
            name=user_data.name,
            email=user_data.email,
            hashed_password=hashed_pwd,
            classes_handled=user_data.classesHandled,
            subjects=user_data.subjects,
            school_location=user_data.schoolLocation,
            preferred_language=user_data.preferredLanguage
        )
        
        try:
            await new_user.insert()
            # Log successful signup
            print(f"\n✅ USER SIGNUP SUCCESSFUL")
            print(f"   Name: {new_user.name}")
            print(f"   Email: {new_user.email}")
            print(f"   ID: {new_user.id}")
            print(f"   Classes: {new_user.classes_handled}")
            print(f"   Subjects: {new_user.subjects}")
            print(f"   Location: {new_user.school_location}")
            print(f"   Languages: {new_user.preferred_language}\n")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create user: {str(e)}"
            )
        
        # Generate token
        token = create_access_token(str(new_user.id))
        
        # Return user response
        user_response = UserResponse(
            id=str(new_user.id),
            name=new_user.name,
            email=new_user.email,
            classesHandled=new_user.classes_handled,
            subjects=new_user.subjects,
            schoolLocation=new_user.school_location,
            preferredLanguage=(new_user.preferred_language if isinstance(new_user.preferred_language, list) else ([new_user.preferred_language] if new_user.preferred_language else []))
        )
        
        return user_response, token
    
    @staticmethod
    async def login(credentials: LoginRequest) -> tuple[UserResponse, str]:
        """
        Authenticate a user and return token.
        
        Args:
            credentials: Login credentials
            
        Returns:
            Tuple of (UserResponse, access_token)
            
        Raises:
            HTTPException: If credentials are invalid
        """
        # Find user by email
        user = await User.find_one(User.email == credentials.email)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not verify_password(credentials.password[:72], user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Generate token
        token = create_access_token(str(user.id))
        
        # Log successful login
        print(f"\n✅ USER LOGIN SUCCESSFUL")
        print(f"   Email: {user.email}")
        print(f"   Name: {user.name}")
        print(f"   ID: {user.id}")
        print(f"   Token Generated: {token[:20]}...")
        print(f"   Timestamp: {datetime.utcnow()}\n")
        
        # Return user response
        user_response = UserResponse(
            id=str(user.id),
            name=user.name,
            email=user.email,
            classesHandled=user.classes_handled,
            subjects=user.subjects,
            schoolLocation=user.school_location,
            preferredLanguage=(user.preferred_language if isinstance(user.preferred_language, list) else ([user.preferred_language] if user.preferred_language else []))
        )
        
        return user_response, token
