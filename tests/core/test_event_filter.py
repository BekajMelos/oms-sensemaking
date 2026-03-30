from oms_sdk.generated.generated_graphql_client.enums import Action, ObjectType
from pytest_mock import MockerFixture

from oms_sensemaking.core.event_filter import (
    ActionInputFilter,
    CanPassAnyInputFilter,
    IriInputFilter,
    MustPassAllInputFilter,
    ObjectInputFilter,
)
from oms_sensemaking.core.event_model import AuditLogHeaders
from oms_sensemaking.core.events import (
    AuditLogEvent,
    EventFilter,
)


def test_object_input_filter(mocker: MockerFixture):
    acceptable_inputs = [ObjectType.NODE]
    filter = ObjectInputFilter(acceptable_inputs)

    event = mocker.Mock(spec=AuditLogEvent)
    event.objectType = ObjectType.NODE
    assert filter.passes_filter(event)


def test_action_input_filter(mocker: MockerFixture):
    acceptable_inputs = [Action.CREATE]
    filter = ActionInputFilter(acceptable_inputs)

    event = mocker.Mock(spec=AuditLogEvent)
    event.action = Action.CREATE
    assert filter.passes_filter(event)


def test_iri_input_filter(mocker: MockerFixture):
    acceptable_inputs = ["https://some/iri"]
    filter = IriInputFilter(acceptable_inputs)

    event = mocker.Mock(spec=AuditLogEvent)
    event.headers = AuditLogHeaders("https://some/iri")
    assert filter.passes_filter(event)


def test_can_pass_any_input_filter(mocker: MockerFixture):
    event = mocker.Mock(spec=AuditLogEvent)
    any_filter = CanPassAnyInputFilter([AlwaysFailEventFilter(), AlwaysPassEventFilter()])
    assert any_filter.passes_filter(event)


def test_must_pass_all_input_filter(mocker: MockerFixture):
    event = mocker.Mock(spec=AuditLogEvent)
    all_filter = MustPassAllInputFilter([AlwaysPassEventFilter(), AlwaysPassEventFilter()])
    assert all_filter.passes_filter(event)


class AlwaysFailEventFilter(EventFilter):
    def passes_filter(self, audit_log_event: AuditLogEvent):
        return False


class AlwaysPassEventFilter(EventFilter):
    def passes_filter(self, audit_log_event: AuditLogEvent):
        return True
