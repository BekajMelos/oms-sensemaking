"""Endpoints that return information about the service."""
from fastapi import APIRouter

from oms_sensemaking import __description__, __title__, __version__
from oms_sensemaking.api.schemas.app_info import AppInfo

router: APIRouter = APIRouter()


@router.get('/', response_model=AppInfo, response_model_exclude_none=True)
@router.get('/about', response_model=AppInfo, response_model_exclude_none=True)
#@router.get semantic.py stuff
def about() -> AppInfo:
    """Returns service information."""
    return AppInfo(title=__title__, version=__version__, description=__description__)
