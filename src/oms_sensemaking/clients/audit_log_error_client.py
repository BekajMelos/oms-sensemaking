"""Audit Log Error Client"""

import logging
from typing import Optional

import oms_sensemaking
from oms_sensemaking.clients.instances import db_session
from oms_sensemaking.models.logs import AuditLogError

LOGGER = logging.getLogger(__name__)

SENSEMAKING_MODULE = oms_sensemaking.__name__


class AuditLogErrorClient:
    def get_audit_log_errors(self, exception_name: Optional[str], page: int, pagesize: int):
        display = []
        with db_session() as db:
            query = db.query(AuditLogError).order_by(AuditLogError.created_at.desc())
            if exception_name:
                query = query.filter(AuditLogError.exception_name == exception_name)

            errors = query.limit(int(pagesize)).offset((int(page) - 1) * int(pagesize)).all()

        for error in errors:
            display.append(
                {
                    "created_at": error.created_at,
                    "id": error.id,
                    "object_id": error.object_id,
                    "object_type": error.object_type,
                    "event_type": error.event_type,
                    "module_name": error.module_name,
                    "line_no": error.line_no,
                    "function_name": error.function_name,
                    "code": error.code,
                    "exception_name": error.exception_name,
                    "version": error.version,
                    "message": error.message,
                    "exc_text": error.exc_text,
                    "acm": error.acm,
                }
            )
        return display
