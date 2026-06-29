import os

from fastapi.templating import Jinja2Templates

from app.utils.datetime_local import format_datetime_local

templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
)


def _localtime_filter(value, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    return format_datetime_local(value, fmt=fmt, include_zone=False)


def _localtime_short_filter(value) -> str:
    return format_datetime_local(value, fmt="%H:%M:%S", include_zone=False)


templates.env.filters["localtime"] = _localtime_filter
templates.env.filters["localtime_short"] = _localtime_short_filter
