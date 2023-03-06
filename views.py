from fastapi import Depends, Request
from fastapi.templating import Jinja2Templates
from starlette.responses import HTMLResponse

from lnbits.core.models import User
from lnbits.decorators import check_user_exists

from . import atmbitbit_ext, atmbitbit_renderer
from .exchange_rates import exchange_rate_providers_serializable, fiat_currencies
from .helpers import get_callback_url

templates = Jinja2Templates(directory="templates")


@atmbitbit_ext.get("/", response_class=HTMLResponse)
async def index(req: Request, user: User = Depends(check_user_exists)):
    atmbitbit_vars = {
        "callback_url": get_callback_url(req),
        "exchange_rate_providers": exchange_rate_providers_serializable,
        "fiat_currencies": fiat_currencies,
    }
    return atmbitbit_renderer().TemplateResponse(
        "atmbitbit/index.html",
        {"request": req, "user": user.dict(), "atmbitbit_vars": atmbitbit_vars},
    )
