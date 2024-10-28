"""Provides utilities for working with submitted data."""


class SubmissionData:
    """Represents submitted data."""

    def __init__(self, document_id: str, text: str):
        """
        Create a new instance of SubmissionData.

        :param document_id: The unique identifier of the document.
        :param text: The text content of the document.
        """
        self.document_id = document_id
        self.text = text

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()
