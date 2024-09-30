"""NLP Sensemaker Service"""

import dataclasses
import logging
from uuid import UUID, uuid4

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.nlp.corenlp_client import CoreNlpClient
from oms_sensemaking.nlp.models.entities_and_relationships import EntitiesAndRelationships
from oms_sensemaking.nlp.nlp_reader import NlpReader, NlpStringReader
from oms_sensemaking.nlp.sensemakers.nlp_sensemaker import NlpSensemaker

LOGGER: logging.Logger = logging.getLogger(__name__)


class NlpService:
    """Intermediary between the API and the NLP Business Logic"""

    def run_nlp(self, nlp_reader: NlpReader, source_id: str | UUID, corenlp_host: CoreNlpClient):
        """
        Pipeline called by API to run the NLP Business Logic and report findings back to OMS
        :param nlp_reader: The body of text to be analyzed by the NLP Service
        :param corenlp_host: Host site for CoreNLP
        :param source_id: ID of the text's Source
        """

        # Use the NLP Sensemaker to process the text data for findings
        submission_data = nlp_reader.read()
        nlp_sensemaker = NlpSensemaker(corenlp_host)
        findings = nlp_sensemaker.process_data(submission_data)

        # Submit the findings to OMS (future work)
        self.submit_findings_to_oms(findings=findings, source_id=source_id)

        # Convert findings data to dicts for serializable FastAPI response
        findings_dict = dataclasses.asdict(findings)
        findings_dict["document_relationships"] = [dataclasses.asdict(rel) for rel in findings.document_relationships]

        # Return as dictionary to API for response
        return findings_dict

    def submit_findings_to_oms(self, findings: EntitiesAndRelationships, source_id: str | UUID) -> bool:
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
    text = "ThisissomesampletextrelatingEntity1toEntity2"
    doc_id = uuid4()
    source_id = "1"
    nlp_service = NlpService()
    reader = NlpStringReader(text=text, document_id=doc_id)
    nlp_service.run_nlp(reader, source_id, CoreNlpClient({}, SETTINGS.corenlp_localhost))
