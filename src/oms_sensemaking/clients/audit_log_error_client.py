"""Audit Log Error Client"""

import logging
from typing import Optional

from oms_sensemaking.clients.instances import aac_client, db_session
from oms_sensemaking.models.logs import AuditLogError

LOGGER = logging.getLogger(__name__)


class AuditLogErrorClient:
    def get_audit_log_errors(self, user_dn, exception_name: Optional[str], page: int, pagesize: int):
        display: list[dict] = []
        with db_session() as db:
            query = db.query(AuditLogError).order_by(AuditLogError.created_at.desc())
            if exception_name:
                query = query.filter(AuditLogError.exception_name == exception_name)

            errors = query.limit(int(pagesize)).offset((int(page) - 1) * int(pagesize)).all()
        if not errors:
            LOGGER.info("No Audit Error Logs to display")
            return display
        response = aac_client.check_access_for_acms(user_dn, [{"ACM": error.acm} for error in errors])
        for i in range(len(response)):
            access_errors_from_aac_response = response[i].get("Errors")
            if access_errors_from_aac_response:
                # Skip this index, do not include in final display list
                continue
            current_error_from_query = errors[i]
            display.append(
                {
                    "created_at": current_error_from_query.created_at,
                    "id": current_error_from_query.id,
                    "object_id": current_error_from_query.object_id,
                    "object_type": current_error_from_query.object_type,
                    "event_type": current_error_from_query.event_type,
                    "module_name": current_error_from_query.module_name,
                    "line_no": current_error_from_query.line_no,
                    "function_name": current_error_from_query.function_name,
                    "code": current_error_from_query.code,
                    "exception_name": current_error_from_query.exception_name,
                    "version": current_error_from_query.version,
                    "message": current_error_from_query.message,
                    "exc_text": current_error_from_query.exc_text,
                    "acm": current_error_from_query.acm,
                }
            )
        return display
