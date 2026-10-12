from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from app.core.config import settings

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verifies the JWT token from Supabase."""
    token = credentials.credentials
    try:
        # Supabase uses HS256 to sign tokens
        payload = jwt.decode(
            token, 
            settings.SUPABASE_JWT_SECRET, 
            algorithms=["HS256"],
            audience="authenticated",
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

def get_current_user(payload: dict = Security(verify_token)):
    """Dependency to get the current authenticated user's payload."""
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    
    # Return the user info extracted from the token
    return {
        "id": user_id,
        "email": payload.get("email", ""),
        "role": payload.get("role", "")
    }
