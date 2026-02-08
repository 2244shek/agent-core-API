import logging
from fastapi import Request
from fastapi.responses import JSONResponse

# Set up structured logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agent-core")

async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "An internal agent error occurred. Please try again later."},
    )