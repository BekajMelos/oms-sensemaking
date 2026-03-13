"""Audit Log Error Client"""

import logging
from datetime import datetime

from sqlalchemy import delete

from oms_sensemaking.clients.instances import aac_client, db_session
from oms_sensemaking.models.logs import AuditLogError

LOGGER = logging.getLogger(__name__)


class AuditLogErrorClient:
    """Class for retrieving Audit Error Logs from the database"""

    def get_audit_log_errors(
            self,
            user_dn,
            exception_name: str | None,
            created_at_start: datetime | None,
            created_at_end: datetime | None,
            page: int,
            pagesize: int):
        """
        Get Audit Error Logs from the database

        :param user_dn: User DN
        :param exception_name: Optional filter for exception_name
        :param created_at_start: Optional filter for exception_name
        :param created_at_end: Optional filter for exception_name
        :param page: Page number to retrieve
        :param pagesize: Number of records to retrieve in the page
        :return: List of matching Audit Log Errors
        """
        display: list[dict] = []

        with db_session() as db:
            query = db.query(AuditLogError).order_by(AuditLogError.created_at.desc())

            if exception_name:
                query = query.where(AuditLogError.exception_name == exception_name)

            if created_at_start:
                query = query.where(AuditLogError.created_at >= created_at_start)

            if created_at_end:
                query = query.where(AuditLogError.created_at <= created_at_end)

            errors = query.limit(int(pagesize)).offset((int(page) - 1) * int(pagesize)).all()

        if not errors:
            LOGGER.info("No Audit Error Logs to display")
            return display

        response = aac_client.check_access_for_acms(user_dn, [{"ACM": error.acm} for error in errors])

        for i, error_obj in enumerate(response):
            access_errors_from_aac_response = error_obj.get("Errors")
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

    def delete_audit_log_errors(
        self, exception_name: str | None, created_at_start: datetime | None, created_at_end: datetime | None
    ):
        """
        Delete Audit Error Logs from the database

        :param exception_name: Optional filter for exception_name
        :param created_at_start: Optional filter for exception_name
        :param created_at_end: Optional filter for exception_name
        :return: List of matching Audit Log Errors
        """

        if not any((exception_name, created_at_start, created_at_end)):
            LOGGER.info("No filter criteria to delete")
            return

        query = delete(AuditLogError)

        if exception_name:
            query = query.where(AuditLogError.exception_name == exception_name)

        if created_at_start:
            query = query.where(AuditLogError.created_at >= created_at_start)

        if created_at_end:
            query = query.where(AuditLogError.created_at <= created_at_end)

        with db_session() as db:
            LOGGER.debug(f"Deleting with query: {query}")
            db.execute(query)
            db.commit()
