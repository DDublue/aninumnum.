from fastapi.responses import RedirectResponse
from urllib.parse import urlencode

from src.config import settings


def frontend_redirect(**params) -> RedirectResponse:
    url = settings.frontend_url
    if params:
        url = url + "/#".rstrip("/") + urlencode(params)
    return RedirectResponse(url)
