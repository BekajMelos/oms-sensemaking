"""NLP Sensemaker Service"""

import dataclasses
import logging
from datetime import datetime
from uuid import uuid4

from dotenv import load_dotenv
from sqlalchemy import select

from oms_sensemaking.clients import db_session
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.models.base import utcnow_with_timezone
from oms_sensemaking.models.sensemaking import Finding, FindingType
from oms_sensemaking.nlp.corenlp_client import CoreNlpClient
from oms_sensemaking.nlp.models.entities_and_relationships import EntitiesAndRelationships
from oms_sensemaking.nlp.nlp_publisher import NlpOmsPublisher
from oms_sensemaking.nlp.nlp_reader import NlpReader, NlpStringReader
from oms_sensemaking.nlp.sensemakers.nlp_sensemaker import NlpSensemaker

LOGGER: logging.Logger = logging.getLogger(__name__)

load_dotenv()


class NlpService:
    """Intermediary between the API and the NLP Business Logic"""

    def __init__(self):
        self.oms_crud_tool = OmsCrudTool()

    def run_service(self, acm: dict, nlp_reader: NlpReader, source_id: str, corenlp_client: CoreNlpClient):
        """Pipeline called by API to run the NLP Business Logic and report findings back to OMS"""
        execution_time = utcnow_with_timezone()
        findings = self.run_nlp(nlp_reader=nlp_reader, corenlp_client=corenlp_client)

        # Submit the findings to OMS
        self.submit_findings_to_oms(findings=findings, source_id=source_id)

        # Submit findings to postgis
        self.submit_findings_to_postgis(acm=acm, findings=findings, execution_time=execution_time)

        return findings

    def run_nlp(self, nlp_reader: NlpReader, corenlp_client: CoreNlpClient) -> dict:
        """
        Runs the NLP Sensemaker Business Logic
        :param nlp_reader: The body of text to be analyzed by the NLP Service
        :param corenlp_client: Host site for CoreNLP
        """

        # Use the NLP Sensemaker to process the text data for findings
        submission_data = nlp_reader.read()
        nlp_sensemaker = NlpSensemaker(corenlp_client)
        findings = nlp_sensemaker.process_data(submission_data)

        # Return as dictionary to API for response
        return self.findings_to_dict(findings)

    def submit_findings_to_postgis(self, acm: dict, findings: dict, execution_time: datetime):
        """
        Submit findings as Finding objects to the findings table in postgis
        :param acm: the acm
        :param findings: the result of running the NLP NER Sensemaker converted to a dictionary
        :param execution_time: the time at which the algorithm was executed
        """
        # 1. Turn findings into Finding object
        finding_object = Finding(
            acm=acm,
            finding_id=uuid4(),
            finding_type=FindingType.NLP_FINDINGS,
            finding_data=findings,
            oms_version=SETTINGS.oms_version_env,
            published_at=utcnow_with_timezone(),
            algorithm_name=SETTINGS.nlp_algorithm_name,
            algorithm_version=SETTINGS.algorithm_version,
            algorithm_configuration=SETTINGS.nlp_configuration,
            executed_at=execution_time,
        )

        # 2. Submit Finding object to the Findings table
        with db_session() as db:
            db.add(finding_object)
            db.commit()
            db.refresh(finding_object)

    def get_all_findings_from_postgis(self):
        """Get the findings from the postgis database"""

        with db_session() as db:
            findings_query = db.execute(select(Finding).where(Finding.finding_type == FindingType.NLP_FINDINGS))
            result = findings_query.scalars().all()
        return result

    def submit_findings_to_oms(self, findings: dict, source_id: str):
        """
        Submit the Entities and Relationships to OMS
        :param findings: found Entities and Relationships
        :param source_id: ID of the text's Source
        """
        nlp_publisher = NlpOmsPublisher(source_id)
        nlp_publisher.publish(findings)

    def findings_to_dict(self, findings: EntitiesAndRelationships) -> dict:
        # Convert findings data to dicts for serializable FastAPI response
        findings_dict = dataclasses.asdict(findings)
        findings_dict["document_relationships"] = [dataclasses.asdict(rel) for rel in findings.document_relationships]
        return findings_dict

    def validate_source(self, source_id: str) -> bool:
        """Validate the source referenced by the source_id"""
        # Query OMS_SDK for a source with the given source_id
        return bool(self.oms_crud_tool.get_source(source_id))


# TODO: Delete main once the API is up and running. Do the following in the API call
if __name__ == "__main__":
    text = "This is some sample text relating Entity1 to Entity2"
    acm: dict = {}
    doc_id = "41d83ecb-4c60-4294-9c51-eb4d1e444df6"
    source_id = "1"
    nlp_service = NlpService()
    reader = NlpStringReader(text=text, document_id=doc_id)
    nlp_service.run_service(acm, reader, source_id, CoreNlpClient({}, SETTINGS.corenlp_localhost))
