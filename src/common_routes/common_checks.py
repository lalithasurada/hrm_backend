from supabase import Client
import secrets
import string
import os
from supabase import create_client
from fastapi import APIRouter, HTTPException, status, Depends


import logging

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

async def generate_user_based_password(
    name: str,
    email: str,
    length: int = 16,
) -> str:
    """
    Generate a random password that loosely uses user details
    (e.g., initials, domain), but is still mostly random.
    """
    try:

        # Character pools
        letters = string.ascii_letters
        digits = string.digits
        specials = "!@#$%^&*()-_=+"

        # 1) Derive a few deterministic bits from user data (optional flavor)
        name_part = (name.strip().split(" ")[0][:3] or "usr").title()
        email_user = (email.split("@")[0][:3] or "acc").lower()

        base = name_part + email_user  # e.g., "Rajraj" or "Samdev"

        # 2) Fill the rest with secure random characters
        remaining_len = max(length - len(base), 8)  # enforce minimum randomness
        pool = letters + digits + specials

        random_tail = "".join(secrets.choice(pool) for _ in range(remaining_len))

        # 3) Mix and shuffle
        raw = (base + random_tail)[:length]
        # Shuffle characters to avoid predictable prefix
        chars = list(raw)
        secrets.SystemRandom().shuffle(chars)

        return "".join(chars)
    except Exception as e:
        logger.error("Error generating password for name=%s email=%s: %s", name, email, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate password",
        )



def get_supabase_client() -> Client:
    try:
        logger.debug("Creating Supabase client for user routes")
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")  # use service key for writes [web:161]
        print(f"Supabase URL: {url}, Key: {key}")
        if not url or not key:
            logger.warning("Supabase URL or key not configured")
            raise RuntimeError("Supabase URL/key not configured")
        return create_client(url, key)
    except RuntimeError as re:
        raise re
    except Exception as e:
        logger.error("Error creating Supabase client: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create Supabase client",
        )




