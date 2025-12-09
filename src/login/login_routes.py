from fastapi import APIRouter
from .auth_models import LoginRequest, TokenResponse
from .login_checks import *
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/login")



@router.post("/users", response_model=TokenResponse, summary="Login and get JWT tokens")
def login(
    payload: LoginRequest,
    supabase: Client = Depends(get_supabase_client),
):
    """
    - Validates user credentials against Supabase Auth (email + password).
    - On success, returns access & refresh JWTs.
    - On failure, returns 401/403 with safe error messages. [web:7][web:13][web:14]
    """
    print(f"💥 Login attempt for payload: {payload}")
    logger.info("Login attempt for email=%s", payload.email)
    try:
        user_id = authenticate_with_supabase(payload.email, payload.password, supabase)
        logger.info("Login successful for user_id=%s", user_id)
    except HTTPException as e:
        logger.warning(
            "Login failed for email=%s status=%s detail=%s",
            payload.email,
            e.status_code,
            e.detail,
        )
        raise e
    try:
        tokens = create_access_and_user_data(user_id,supabase=supabase)
        logger.debug("Tokens generated for user_id=%s", user_id)
    except Exception as e:
        print(f"💥 Token generation error: {e}")
        logger.exception("Token generation error for user_id=%s: %s", user_id, e)
        raise HTTPException(status_code=500, detail="Token generation failed")

    return tokens
 

@router.get("/me")
def read_me(user_id: str = Depends(get_current_user_id)):
    return {"user_id": user_id}