"""Implementation of readers used in the NlpService"""

from abc import ABC, abstractmethod
from uuid import uuid4

from oms_sensemaking.nlp.models.submission_data import SubmissionData


class NlpReader(ABC):
    @abstractmethod
    def read(self) -> SubmissionData:
        """
        Provide a SubmissionData object to the NlpService
        """
        raise NotImplementedError()


class NlpStringReader(NlpReader):
    def __init__(self, text: str, document_id=None):
        """
        :param text: string to read
        :param document_id: unique identifier of document
        """
        self.text = text
        self.document_id = document_id if document_id else str(uuid4())

    def read(self) -> SubmissionData:
        """Read a string and formats it as SubmissionData"""
        return SubmissionData(document_id=self.document_id, text=self.text)


class NlpFileReader(NlpReader):
    def __init__(self, filepath: str, document_id=None):
        """
        Read text file and get contents as string
        :param filepath: path to text file
        :param document_id: unique identifier of document
        """
        self.filepath = filepath
        self.document_id = document_id if document_id else str(uuid4())

    def read_file(self) -> str:
        """Read a file and extract the text as a string"""
        with open(self.filepath, "r") as file:
            file_text = file.read()
        return file_text

    def read(self) -> SubmissionData:
        """Call file read and return it as a SubmissionData object"""
        return SubmissionData(self.document_id, self.read_file())
