from fastapi import APIRouter
from starlette.staticfiles import StaticFiles

from lnbits.db import Database
from lnbits.helpers import template_renderer

db = Database("ext_atmbitbit")

atmbitbit_static_files = [
    {
        "path": "/atmbitbit/static",
        "app": StaticFiles(packages=[("lnbits", "extensions/atmbitbit/static")]),
        "name": "atmbitbit_static",
    }
]

atmbitbit_ext: APIRouter = APIRouter(prefix="/atmbitbit", tags=["AtmBitBit"])


def atmbitbit_renderer():
    return template_renderer(["lnbits/extensions/atmbitbit/templates"])


from .lnurl_api import *  # noqa: F401,F403
from .views import *  # noqa: F401,F403
from .views_api import *  # noqa: F401,F403
