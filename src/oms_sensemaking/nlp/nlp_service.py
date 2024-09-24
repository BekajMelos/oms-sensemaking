"""NLP Sensemaker Service"""

import logging
from uuid import UUID, uuid4

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.nlp.models.entities_and_relationships import EntitiesAndRelationships
from oms_sensemaking.nlp.nlp_reader import NlpReader, NlpStringReader
from oms_sensemaking.nlp.sensemakers.nlp_sensemaker import NlpSensemaker

LOGGER: logging.Logger = logging.getLogger(__name__)


class NlpService:
    """Intermediary between the API and the NLP Business Logic"""

    def run_nlp(self, nlp_reader: NlpReader, source_id: str | UUID, corenlp_host: str = SETTINGS.corenlp_dockerhost):
        """
        Pipeline called by API to run the NLP Business Logic and report findings back to OMS
        :param nlp_reader: The body of text to be analyzed by the NLP Service
        :param corenlp_host: Host site for CoreNLP
        :param source_id: ID of the text's Source
        """
        submission_data = nlp_reader.read()
        nlp_sensemaker = NlpSensemaker(corenlp_host=corenlp_host)
        ents_and_rels = nlp_sensemaker.process_data(submission_data)
        self.submit_findings_to_oms(ents_and_rels, source_id)
        return ents_and_rels

    def submit_findings_to_oms(self, findings: EntitiesAndRelationships, source_id: str) -> bool:
        """
        Submit the Entities and Relationships to OMS
        :param findings: found Entities and Relationships
        :param source_id: ID of the text's Source
        """
        # TODO: Implement this function to call the EntityDecorator
        LOGGER.debug(findings)
        LOGGER.debug(source_id)
        return True


# TODO: Delete main once the API is up and running. Do the following in the API call
if __name__ == "__main__":
    text = (
        "EU rejects German call to boycott British lamb. Peter Blackburn BRUSSELS 1996-08-22 "
        "The European Commission said on Thursday it disagreed with German advice to consumers "
        "to shun British lamb until scientists determine whether mad cow disease can be transmitted"
        " to sheep. Germany's representative to the European Union's veterinary committee Werner Zwingmann"
        " said on Wednesday consumers should buy sheepmeat from countries other than Britain until the "
        "scientific advice was clearer."
    )
    doc_id = uuid4()
    nlp_service = NlpService()
    reader = NlpStringReader(text=text, document_id=doc_id)
    nlp_service.run_nlp(reader, SETTINGS.corenlp_localhost)
