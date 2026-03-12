"""Rest Endpoint for Audit Log Error"""

import logging
from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, status

from oms_sensemaking.api.routers.utils import check_user_dn_in_whitelist
from oms_sensemaking.clients.audit_log_error_client import AuditLogErrorClient

LOGGER: logging.Logger = logging.getLogger(__name__)

router: APIRouter = APIRouter()


# def get_audit_error_log_client(user_dn: Annotated[str, Depends(require_user_dn)]) -> str:
#     """Read the User DN Header from the request and ensure this user is in the whitelist

#     :param user_dn: User DN
#     :return: User DN
#     """

#     if user_dn.lower() not in SETTINGS.user_dn_whitelist:
#         raise HTTPException(401, detail="Unauthorized")

#     return user_dn


@router.get("/audit")
def get_audit_log_errors(
    user_dn: Annotated[str, Depends(check_user_dn_in_whitelist)],
    exception_name: Optional[str] = None,
    page: int = Query(1, ge=1),
    pagesize: int = Query(500, ge=1, le=1000),
):
    """View Audit Error Logs"""
    LOGGER.info("Displaying Audit Error Logs to Whitelisted user. User %s", user_dn)
    audit_log_error_client = AuditLogErrorClient()
    errors = audit_log_error_client.get_audit_log_errors(user_dn, exception_name, page, pagesize)
    if not errors:
        return {"detail": "Unable to display Audit Log Errors. No data to display or incorrect query fields were used."}
    return errors


@router.delete("/audit", status_code=status.HTTP_204_NO_CONTENT)
def delete_audit_log_errors(
    exception_name: str | None = Query(None, description="Optional Exception name to query for"),
    created_at_start: datetime | None = Query(
        None, description="Optional ISO formatted datetime " "string. Filter by earliest " "created_at."
    ),
    created_at_end: datetime | None = Query(
        None, description="Optional ISO formatted datetime " "string. Filter by latest " "created_at."
    ),
) -> None:
    """Delete Audit Error Logs"""

    audit_log_error_client = AuditLogErrorClient()
    audit_log_error_client.delete_audit_log_errors(exception_name, created_at_start, created_at_end)
