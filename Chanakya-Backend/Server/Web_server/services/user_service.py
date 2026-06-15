"""
User service - handles user management operations.
"""
from fastapi import HTTPException, status
from models.user import User
from schemas.user import UserResponse, UserUpdate
from typing import Optional
from datetime import datetime


class UserService:
    """Service for user management operations."""
    
    @staticmethod
    async def get_user_by_id(user_id: str) -> Optional[UserResponse]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            UserResponse if found, None otherwise
        """
        try:
            user = await User.get(user_id)
            if not user:
                return None
            
            pref_lang = user.preferred_language
            if not isinstance(pref_lang, list):
                pref_lang = [pref_lang] if pref_lang else []
            return UserResponse(
                id=str(user.id),
                name=user.name,
                email=user.email,
                classesHandled=user.classes_handled,
                subjects=user.subjects,
                schoolLocation=user.school_location,
                preferredLanguage=pref_lang
            )
        except Exception:
            return None
    
    @staticmethod
    async def get_user_by_email(email: str) -> Optional[UserResponse]:
        """
        Get user by email.
        
        Args:
            email: User email
            
        Returns:
            UserResponse if found, None otherwise
        """
        user = await User.find_one(User.email == email)
        if not user:
            return None
        pref_lang = user.preferred_language
        if not isinstance(pref_lang, list):
            pref_lang = [pref_lang] if pref_lang else []

        return UserResponse(
            id=str(user.id),
            name=user.name,
            email=user.email,
            classesHandled=user.classes_handled,
            subjects=user.subjects,
            schoolLocation=user.school_location,
            preferredLanguage=pref_lang
        )
    
    @staticmethod
    async def update_user(user_id: str, user_data: UserUpdate) -> UserResponse:
        """
        Update user information.
        
        Args:
            user_id: User ID
            user_data: User update data
            
        Returns:
            Updated UserResponse
            
        Raises:
            HTTPException: If user not found
        """
        user = await User.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update fields
        update_data = user_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            # Map camelCase to snake_case
            if field == "classesHandled":
                user.classes_handled = value
            elif field == "schoolLocation":
                user.school_location = value
            elif field == "preferredLanguage":
                user.preferred_language = value
            else:
                setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        await user.save()
        
        pref_lang = user.preferred_language
        if not isinstance(pref_lang, list):
            pref_lang = [pref_lang] if pref_lang else []

        return UserResponse(
            id=str(user.id),
            name=user.name,
            email=user.email,
            classesHandled=user.classes_handled,
            subjects=user.subjects,
            schoolLocation=user.school_location,
            preferredLanguage=pref_lang
        )
    
    @staticmethod
    async def delete_user(user_id: str) -> bool:
        """
        Delete a user.
        
        Args:
            user_id: User ID
            
        Returns:
            True if deleted, False otherwise
        """
        user = await User.get(user_id)
        if not user:
            return False
        
        await user.delete()
        return True
