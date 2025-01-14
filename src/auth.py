from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

def verify_api_key(api_key_header: str = Security(api_key_header)) -> bool:
    """Verify if the API Key in request header is valid"""
    if check_api_key(api_key_header):
        return True
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authenticated"
    )

# Checking API key against backend needs to be implamented
# All API keys will be valid unless they start with "dud0-"
def check_api_key(api_key: str):
    """Check if API key is valid"""
    return not api_key.startswith("dud0-")
