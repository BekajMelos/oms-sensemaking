"""Tests for the NlpSensemakerController"""

from uuid import uuid4

from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import Action, ObjectType

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.events import ObjectEvent
from oms_sensemaking.nlp.controllers import NlpApiReceiver, NlpSensemakerController, TextFileReader

action = Action.CREATE
object_type = ObjectType.SOURCE
user_dn = SETTINGS.user_dn
acm = DEFAULT_ACM


def test_controller_text_file_reader():
    filepath = "etc/data/madcow.txt"
    event = ObjectEvent(SETTINGS.user_dn, uuid4(), object_type, action)
    nlp: NlpSensemakerController = NlpSensemakerController(TextFileReader(filepath, acm, user_dn))
    assert nlp.handle_event(event)


def test_controller_api_receiver_consumer():
    sample_text = (
        "EU rejects German call to boycott British lamb. Peter Blackburn BRUSSELS 1996-08-22 "
        "The European Commission said on Thursday it disagreed with German advice to consumers "
        "to shun British lamb until scientists determine whether mad cow disease can be transmitted"
        " to sheep. Germany's representative to the European Union's veterinary committee Werner Zwingmann"
        " said on Wednesday consumers should buy sheepmeat from countries other than Britain until the "
        "scientific advice was clearer."
    )
    event = ObjectEvent(SETTINGS.user_dn, uuid4(), object_type, action)
    nlp: NlpSensemakerController = NlpSensemakerController(NlpApiReceiver(sample_text, acm, user_dn))
    assert nlp.handle_event(event)


def test_controller_api_receiver_consumer_no_text():
    empty_text = ""
    event = ObjectEvent(SETTINGS.user_dn, uuid4(), object_type, action)
    nlp: NlpSensemakerController = NlpSensemakerController(NlpApiReceiver(empty_text, acm, user_dn))
    assert nlp.handle_event(event)
