from fastapi import APIRouter, HTTPException, status, Depends
from supabase import Client
from .common_models import UserCreate,UserUpdate
import os
from supabase import create_client
from dotenv import load_dotenv
import logging
from src.login.login_checks import get_current_user_id
from .common_checks import get_supabase_client, generate_user_based_password
load_dotenv()
router = APIRouter(prefix="/users", tags=["users"])
logger = logging.getLogger(__name__)

import secrets
import string



@router.post("/create/user", status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    supabase: Client = Depends(get_supabase_client),user_id: str = Depends(get_current_user_id)
):
    # Check duplicate email
    try:
        logger.info("User creation attempt by user_id=%s for email=%s", user_id, payload.email)
        existing = (
            supabase
            .table("users")
            .select("id")
            .or_(f"email.eq.{payload.email},mobile.eq.{payload.mobile}")
            .maybe_single()
            .execute()
        )  # [web:171][web:179][web:182]
        # print(f"this is existing : \n\n\n\n{existing}\n\n\n\n\n")
        if existing is not None:
            logger.warning("User creation failed: email or mobile already exists email=%s mobile=%s", payload.email, payload.mobile)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email or mobile already exists",
            )
        password = await generate_user_based_password(payload.name, payload.email)

        # Insert row (no id / created_at provided, DB defaults are used)
        to_insert = {
            "name": payload.name,
            "email": payload.email,
            "office_mail": payload.office_mail,
            "password": password,  # plain text as requested (not safe)
            "role": payload.role,
            "mobile": payload.mobile,
            "createdby": payload.created_by,
        }

        res = supabase.table("users").insert(to_insert).execute()  # [web:161]
        # print(f"this is response : \n\n\n\n{res}\n\n\n\n\n")
        if not res:
            logger.error("User creation failed for email=%s", payload.email)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user",
            )

        # Return minimal info (you can shape this how you like)
        created = res.data[0]
        logger.info("User created successfully user_id=%s email=%s", created.get("id"), created.get("email"))
        return {
            "id": created.get("id"),
            "email": created.get("email"),
            "name": created.get("name"),
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.exception("Error creating user email=%s: %s", payload.email, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user",
        )





@router.get("/allusers", summary="Get all users")
def get_all_users(
    _: str = Depends(get_current_user_id),          # require auth
    supabase: Client = Depends(get_supabase_client)
):
    """
    Returns all users from the `users` table.
    """
    try:
        logger.info("Fetching all users requested by user_id=%s", _)
        res = supabase.table("users").select("*").execute()  # [web:15]

        if getattr(res, "error", None):
            logger.error("Failed to fetch users: %s", res.error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch users",
            )
        logger.info("Fetched %d users", len(res.data))
        # Supabase Python client returns rows in `data` [web:15][web:172]
        return res.data
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.exception("Error fetching users: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch users",
        )



@router.patch("/update/{user_id}", summary="Update user details")
def update_user(
    user_id: str,
    payload: UserUpdate,
    _: str = Depends(get_current_user_id),        # require auth
    supabase: Client = Depends(get_supabase_client),
):
    # Build dict of only provided fields
    try:

        logger.info("Updating user_id=%s", user_id)
        update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update",
            )

        # Optional: prevent email/mobile duplicates here if needed

        # Perform update
        res = (
            supabase
            .table("users")
            .update(update_data)
            .eq("id", user_id)
            .execute()
        )  # [web:15][web:171]

        if getattr(res, "error", None):
            logger.error("Failed to update user_id=%s: %s", user_id, res.error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user",
            )

        if not res.data:
            logger.warning("User not found for update user_id=%s", user_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return res.data[0]
    except HTTPException as he:
        raise he
    except Exception as e: 
        logger.exception("Error updating user_id=%s: %s", user_id, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user",
        )
    



@router.delete("/delete/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete user")
def delete_user(
    user_id: str,
    _: str = Depends(get_current_user_id),          # require auth
    supabase: Client = Depends(get_supabase_client),
):
    """
    Delete a user from the `users` table by id.
    """
    try:
        logger.info("Deleting user_id=%s", user_id)

        res = (
            supabase
            .table("users")
            .delete()
            .eq("id", user_id)
            .execute()
        )  # [web:239]

        if getattr(res, "error", None):
            logger.error("Failed to delete user_id=%s: %s", user_id, res.error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user",
            )

        # Supabase returns deleted rows in data when using representation [web:239]
        if not res.data:
            logger.warning("User not found for delete user_id=%s", user_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        logger.info("User deleted successfully user_id=%s", user_id)
        return  # 204 No Content

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error deleting user_id=%s: %s", user_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user",
        )