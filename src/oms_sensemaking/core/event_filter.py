from oms_sdk.generated.generated_graphql_client.enums import Action, ObjectType

from oms_sensemaking.core.events import (
    AuditLogEvent,
    EventFilter,
)


class CanPassAnyInputFilter:
    """Any filter conditions in filter_set can be satisfied to pass"""

    def __init__(self, filter_set: list[EventFilter]):
        self.filter_set = filter_set

    def passes_filter(self, audit_log_event: AuditLogEvent):
        return any(filter.passes_filter(audit_log_event) for filter in self.filter_set)


class MustPassAllInputFilter:
    """All filter conditions in filter_set must be satisfied to pass"""

    def __init__(self, filter_set: list[EventFilter]):
        self.filter_set = filter_set

    def passes_filter(self, audit_log_event: AuditLogEvent):
        return all(filter.passes_filter(audit_log_event) for filter in self.filter_set)


class ObjectInputFilter:
    def __init__(self, acceptable_object_types: list[ObjectType]):
        self.acceptable_object_types = acceptable_object_types

    def passes_filter(self, audit_log_event: AuditLogEvent):
        return audit_log_event.objectType in self.acceptable_object_types


class ActionInputFilter:
    def __init__(self, acceptable_actions: list[Action]):
        self.acceptable_actions = acceptable_actions

    def passes_filter(self, audit_log_event: AuditLogEvent):
        return audit_log_event.action in self.acceptable_actions


class IriInputFilter:
    def __init__(self, acceptable_iris: list[Action]):
        self.acceptable_iris = acceptable_iris

    def passes_filter(self, audit_log_event: AuditLogEvent):
        return audit_log_event.headers.iri in self.acceptable_iris
