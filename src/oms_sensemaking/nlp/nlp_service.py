"""NLP Sensemaker Service"""

import dataclasses
import logging
from datetime import datetime
from uuid import UUID, uuid4

from oms_sensemaking.clients import db_session
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.models.base import utcnow_with_timezone
from oms_sensemaking.models.sensemaking import Finding, FindingType
from oms_sensemaking.nlp.corenlp_client import CoreNlpClient
from oms_sensemaking.nlp.models.entities_and_relationships import EntitiesAndRelationships
from oms_sensemaking.nlp.nlp_reader import NlpReader, NlpStringReader
from oms_sensemaking.nlp.sensemakers.nlp_sensemaker import NlpSensemaker

LOGGER: logging.Logger = logging.getLogger(__name__)


class NlpService:
    """Intermediary between the API and the NLP Business Logic"""

    def run_nlp(self, acm: dict, nlp_reader: NlpReader, source_id: str | UUID, corenlp_client: CoreNlpClient):
        """
        Pipeline called by API to run the NLP Business Logic and report findings back to OMS
        :param nlp_reader: The body of text to be analyzed by the NLP Service
        :param corenlp_host: Host site for CoreNLP
        :param source_id: ID of the text's Source
        """

        # Use the NLP Sensemaker to process the text data for findings
        submission_data = nlp_reader.read()
        nlp_sensemaker = NlpSensemaker(corenlp_client)
        ex_time = utcnow_with_timezone()
        findings = nlp_sensemaker.process_data(submission_data)

        # Submit the findings to OMS (future work)
        self.submit_findings_to_oms(findings=findings, source_id=source_id)

        # Convert findings data to dicts for serializable FastAPI response
        findings_dict = dataclasses.asdict(findings)
        findings_dict["document_relationships"] = [dataclasses.asdict(rel) for rel in findings.document_relationships]

        # Submit findings to postgis
        self.submit_findings_to_postgis(acm=acm, findings=findings_dict, execution_time=ex_time)

        # Return as dictionary to API for response
        return findings_dict

    def submit_findings_to_postgis(self, acm: dict, findings: dict, execution_time: datetime) -> bool:
        """
        Submit findings as Finding objects to the findings table in postgis
        :param acm: the acm
        :param findings: the result of running the NLP NER Sensemaker converted to a dictionary
        :param execution_time: the time at which the algorithm was executed
        """
        # 1. Turn findings into Finding object
        finding_object = Finding(
            acm=acm,
            finding_id=uuid4(),  # TODO: If submitting ind. nodes, create uuid for each and save in dict
            finding_type=FindingType.NLP_RECOGNIZED_ENTITY,  # TODO: change or add more types
            finding_data=findings,
            oms_version="Grimlock-INC-5",  # TODO: Get from env
            published_at=utcnow_with_timezone(),
            algorithm_name="NER",
            algorithm_version="0.0.1",  # TODO: Get from config
            algorithm_configuration={},
            executed_at=execution_time,
        )

        # 2. Submit Finding object to the Findings table
        with db_session() as db:
            db.add(finding_object)
            db.commit()
            db.refresh(finding_object)

        # 3. Return success object
        return True

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
    text = "This is some sample text relating Entity1 to Entity2"
    acm: dict = {}
    doc_id = "41d83ecb-4c60-4294-9c51-eb4d1e444df6"
    source_id = "1"
    nlp_service = NlpService()
    reader = NlpStringReader(text=text, document_id=doc_id)
    nlp_service.run_nlp(acm, reader, source_id, CoreNlpClient({}, SETTINGS.corenlp_localhost))
