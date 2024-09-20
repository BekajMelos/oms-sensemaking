"""NLP Sensemaker Service"""

import logging
from uuid import uuid4

from oms_sensemaking.nlp.models.entities_and_relationships import EntitiesAndRelationships
from oms_sensemaking.nlp.models.submission_data import SubmissionData
from oms_sensemaking.nlp.sensemakers.nlp_sensemaker import NlpSensemaker

LOGGER: logging.Logger = logging.getLogger(__name__)


class NlpService:
    """Intermediary between the API and the NLP Business Logic"""

    # TODO: Adjust input based on what we decide with Core is needed
    def run_nlp_service(self, text) -> bool:
        """
        Pipeline called by API to run the NLP Business Logic and report findings back to OMS
        :param text: The body of text to be analyzed by the NLP Service
        """
        submission_data = SubmissionData(document_id=uuid4(), text=text)
        findings = self.run_nlp_sensemaker(submission_data)
        self.submit_findings_to_oms(findings)
        return True

    def run_nlp_sensemaker(self, data: SubmissionData) -> EntitiesAndRelationships:
        """
        Run the NLP Business Logic via the NlpSensemaker
        :param data: A SubmissionData dataclass object containing a text body (str) and a document id (UUID)
        :return: EntitiesAndRelationships object with findings from NLP Business Logic
        """
        nlp_sensemaker = NlpSensemaker()
        ents_and_rels = nlp_sensemaker.process_data(SubmissionData(document_id=data.document_id, text=data.text))
        return ents_and_rels

    def get_text_from_file(self, filepath: str) -> str:
        # TODO: may be able to delete this later if we don't need/want to run NLP from command line
        """
        Read text file and get contents as string
        :param filepath: path to text file
        :return: string representation of text file contents
        """
        with open(filepath, "r") as file:
            file_text = file.read()
        return file_text

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
    nlp_service.run_nlp_service(text)
