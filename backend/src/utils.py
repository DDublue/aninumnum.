from fastapi.responses import RedirectResponse
from urllib.parse import urlencode

from src.config import settings


def frontend_direct(**params) -> RedirectResponse:
    url = settings.frontend_url + "/#"
    if params:
        url += urlencode(params)
    return RedirectResponse(url)
