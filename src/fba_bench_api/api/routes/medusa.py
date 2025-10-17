from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

router = APIRouter()

LOG_FILE_PATH = Path("medusa_experiments/logs/medusa_trainer.log")


@router.get("/medusa/logs", response_class=PlainTextResponse)
async def get_medusa_logs():
    """
    Retrieves the content of the Medusa trainer log file.

    UI-friendly behavior: if the log file does not exist or cannot be read yet,
    return 200 OK with empty body instead of 404/500 so the frontend can render gracefully.
    """
    if not LOG_FILE_PATH.is_file():
        # Return empty content instead of 404 to avoid breaking the UI
        return PlainTextResponse("", status_code=200)
    try:
        log_content = LOG_FILE_PATH.read_text(encoding="utf-8")
        return log_content
    except Exception:
        # Return empty content on read errors to keep the UI stable
        return PlainTextResponse("", status_code=200)
