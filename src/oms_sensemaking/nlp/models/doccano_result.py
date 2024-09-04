from oms_sensemaking.nlp.models.doccano_entity import DoccanoEntity
from oms_sensemaking.nlp.models.doccano_relation import DoccanoRelation


class DoccanoResult:
    def __init__(
        self, id: int, text: str, entities: set[DoccanoEntity], relations: set[DoccanoRelation], comments: list[str]
    ):
        self.id = id
        self.text = text
        self.entities = entities
        self.relations = relations
        self.comments = comments

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()
