class DoccanoRelation:
    def __init__(self, *args):
        if len(args) > 1:
            id, from_id, to_id, type = args[0], args[1], args[2], args[3]
            self.id = id
            self.from_id = from_id
            self.to_id = to_id
            self.type = type
        elif isinstance(args[0], dict):
            doccano_relation = args[0]
            self.id = doccano_relation["id"]
            self.from_id = doccano_relation["from_id"]
            self.to_id = doccano_relation["to_id"]
            self.type = doccano_relation["type"]

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()
