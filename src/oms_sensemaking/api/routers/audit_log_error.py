"""Rest Endpoint for Audit Log Error"""

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query

from oms_sensemaking.api.routers.utils import check_user_dn_in_whitelist
from oms_sensemaking.clients.audit_log_error_client import AuditLogErrorClient

LOGGER: logging.Logger = logging.getLogger(__name__)

router: APIRouter = APIRouter()


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
