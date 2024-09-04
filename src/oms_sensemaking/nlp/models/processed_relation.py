class ProcessedRelation:
    def __init__(self, from_token_index: int, to_token_index: int, relation_type: str):
        self.from_token_index = from_token_index
        self.to_token_index = to_token_index
        self.relation_type = relation_type

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()
