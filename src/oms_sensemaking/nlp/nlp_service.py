"""NLP Sensemaker Service"""

import logging
from uuid import uuid4
from abc import ABC, abstractmethod

from oms_sensemaking.nlp.models.entities_and_relationships import EntitiesAndRelationships
from oms_sensemaking.nlp.models.submission_data import SubmissionData
from oms_sensemaking.nlp.sensemakers.nlp_sensemaker import NlpSensemaker

LOGGER: logging.Logger = logging.getLogger(__name__)

class NlpReader(ABC):
    @abstractmethod
    def read() -> SubmissionData:
        """
        Provide a SubmissionData object to the NlpService
        """
        raise NotImplementedError()

class NlpStringReader(NlpReader):
    def __init__(self, text):
        self.text = text

    def read() -> SubmissionData:
        return SubmissionData(document_id=uuid4(), text=text)

class NlpFileReader(NlpReader):

    def __init__(self, filepath, document_id=uuid4()):
        """
        Read text file and get contents as string
        :param filepath: path to text file
        :param document_id: unique identifier of document
        """
        self.filepath = filepath
        self.document_id = document_id

    def read_file(self) -> str:
        with open(self.filepath, "r") as file:
            file_text = file.read()
        return file_text

    def read(self) -> SubmissionData:
        return SubmissionData(self.document_id, self.read_file())

class NlpService:
    """Intermediary between the API and the NLP Business Logic"""

    def run_nlp(self, nlp_reader: NlpReader):
        """
        Pipeline called by API to run the NLP Business Logic and report findings back to OMS
        :param text: The body of text to be analyzed by the NLP Service
        """
        submission_data = nlp_reader.read()
        nlp_sensemaker = NlpSensemaker()
        ents_and_rels = nlp_sensemaker.process_data(submission_data)
        self.submit_findings_to_oms(ents_and_rels)
        return ents_and_rels

    def submit_findings_to_oms(self, findings: EntitiesAndRelationships) -> bool:
        # TODO: Implement this function to call the EntityDecorator
        print(findings)
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
    nlp_service = NlpService()
    nlp_reader = NlpStringReader()
    nlp_service.run_nlp(nlp_reader)
