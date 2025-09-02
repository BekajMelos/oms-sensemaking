"""Rest Endpoints for AAC Management"""

import logging
from typing import Annotated

from fastapi import Depends, HTTPException, Request

from oms_sensemaking.config import SETTINGS

LOGGER: logging.Logger = logging.getLogger(__name__)


USER_DN = "user_dn"


def extract_user_dn(request: Request) -> str | None:
    """Extract User DN from Header

    :param request: Request Headers
    :return: User DN or None
    """
    return request.headers.get(USER_DN)


def require_user_dn(user_dn: Annotated[str, Depends(extract_user_dn)]) -> str:
    """Validate that User DN is set

    :param user_dn: User DN from headers
    :return: User DN
    """
    if not user_dn:
        raise HTTPException(401, detail="Unauthorized. Missing User DN")
    return user_dn


def check_user_dn_in_whitelist(user_dn: Annotated[str, Depends(require_user_dn)]) -> str:
    """Read the User DN Header from the request and ensure this user is in the whitelist

    :param user_dn: User DN
    :return: User DN
    """

    if user_dn.lower() not in SETTINGS.user_dn_whitelist:
        raise HTTPException(401, detail="Unauthorized")

    return user_dn
