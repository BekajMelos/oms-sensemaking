from uuid import UUID


class SubmissionData:
    def __init__(self, document_id: str | UUID, text: str):
        self.document_id = document_id
        self.text = text

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()
