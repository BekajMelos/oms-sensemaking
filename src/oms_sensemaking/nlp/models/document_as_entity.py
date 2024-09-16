class DocumentAsEntity:
    def __init__(self, document_id: str, text: str):
        self.document_id = document_id
        self.text = text
        self.entityType = "DOCUMENT"  # key format entityType matches the same field as CoreNLP Entities

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()
