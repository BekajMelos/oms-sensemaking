"""Rest Endpoint for Audit Log Error"""

import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field

from oms_sensemaking.api.routers.utils import check_user_dn_in_whitelist
from oms_sensemaking.clients.audit_log_error_client import AuditLogErrorClient

LOGGER: logging.Logger = logging.getLogger(__name__)

router: APIRouter = APIRouter()


def get_audit_log_error_client() -> AuditLogErrorClient:
    """Return an AuditLogErrorClient"""
    return AuditLogErrorClient()


# class FilterParams(BaseModel):
#     model_config = {"extra": "forbid"}

#     exception_name: str | None = Field(None, description="Optional Exception name to query for")
#     created_at_start: datetime | None = Field(None, description="Optional ISO formatted datetime string. "
#                                                    "Filter by earliest created_at.")
#     created_at_end: datetime | None = Field(None, description="Optional ISO formatted datetime string. "
#                                                    "Filter by latest created_at.")


class PaginationParams(BaseModel):
    model_config = {"extra": "forbid"}

    page: int = Field(1, ge=1, description="Page to query")
    pagesize: int = Field(500, ge=1, le=1000, description="Number of responses per page")


@router.get("/audit")
def get_audit_log_errors(
    user_dn: Annotated[str, Depends(check_user_dn_in_whitelist)],
    audit_log_error_client: Annotated[AuditLogErrorClient, Depends(get_audit_log_error_client)],
    exception_name: Annotated[str | None, Query(description="Optional Exception name to query for")] = None,
    created_at_start: Annotated[
        datetime | None, Query(description="Optional ISO formatted datetime string. Filter by earliest created_at.")
    ] = None,
    created_at_end: Annotated[
        datetime | None, Query(description="Optional ISO formatted datetime string. Filter by latest created_at.")
    ] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    pagesize: Annotated[int, Query(ge=1, le=1000)] = 500,
    # created_at_start: datetime | None = Query(
    #     None, description="Optional ISO formatted datetime " "string. Filter by earliest " "created_at."
    # ),
    # created_at_end: datetime | None = Query(
    #     None, description="Optional ISO formatted datetime " "string. Filter by latest " "created_at."
    # ),
    # page_params: Annotated[PaginationParams, Query()],
):
    """View Audit Error Logs"""
    LOGGER.info("Displaying Audit Error Logs to Whitelisted user. User %s", user_dn)

    errors = audit_log_error_client.get_audit_log_errors(
        user_dn, exception_name, created_at_start, created_at_end, page, pagesize
    )
    if not errors:
        return {"detail": "No Audit Log Errors found"}
    return errors


@router.delete("/audit", status_code=status.HTTP_204_NO_CONTENT)
def delete_audit_log_errors(
    user_dn: Annotated[str, Depends(check_user_dn_in_whitelist)],
    audit_log_error_client: Annotated[AuditLogErrorClient, Depends(get_audit_log_error_client)],
    exception_name: Annotated[str | None, Query(description="Optional Exception name to query for")] = None,
    created_at_start: Annotated[
        datetime | None, Query(description="Optional ISO formatted datetime string. Filter by earliest created_at.")
    ] = None,
    created_at_end: Annotated[
        datetime | None, Query(description="Optional ISO formatted datetime string. Filter by latest created_at.")
    ] = None,
) -> None:
    """Delete Audit Error Logs"""
    audit_log_error_client.delete_audit_log_errors(exception_name, created_at_start, created_at_end)
