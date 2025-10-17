"""Audit Log Error Client"""

import logging
from typing import Optional

import oms_sensemaking
from oms_sensemaking.clients.instances import db_session
from oms_sensemaking.models.logs import AuditLogError

LOGGER = logging.getLogger(__name__)

SENSEMAKING_MODULE = oms_sensemaking.__name__


class AuditLogErrorClient:
    def get_audit_log_errors(self, exception_name: Optional[str]):
        dict_to_display = {}
        with db_session() as db:
            query = (
                db.query(AuditLogError).order_by(AuditLogError.created_at.desc())  # 👈 newest first
            )
            if exception_name:
                query = query.filter(AuditLogError.exception_name == exception_name)

            errors = query.all()

        for error in errors:
            dict_to_display[error.created_at] = error
        return dict_to_display
