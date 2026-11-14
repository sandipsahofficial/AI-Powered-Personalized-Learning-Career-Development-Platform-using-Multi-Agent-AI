import sys
import os
import platform
import time
from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()


@router.get("/info", summary="System Information (Sanitized)")
async def get_system_info():
    """
    Returns sanitized platform runtime details for telemetry and debugging.
    Never exposes credentials, secrets, or internal tokens.
    """
    return {
        "platform": {
            "os": platform.system(),
            "os_release": platform.release(),
            "os_version": platform.version(),
            "architecture": platform.machine(),
            "cpu_count": os.cpu_count() or 1
        },
        "runtime": {
            "python_version": sys.version.split(" ")[0],
            "python_compiler": platform.python_compiler(),
            "app_version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "debug_mode": settings.DEBUG,
            "api_prefix": settings.API_V1_PREFIX
        },
        "network": {
            "backend_port": settings.BACKEND_PORT,
            "cors_origins_count": len(settings.CORS_ORIGINS)
        },
        "server_time_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
