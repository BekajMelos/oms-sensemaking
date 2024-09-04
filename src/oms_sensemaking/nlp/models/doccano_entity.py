class DoccanoEntity:
    def __init__(self, *args):
        if len(args) > 1:
            id, label, start_offset, end_offset = args[0], args[1], args[2], args[3]
            self.id = id
            self.label = label
            self.start_offset = start_offset
            self.end_offset = end_offset
        elif isinstance(args[0], dict):
            doccano_entity = args[0]
            self.id = doccano_entity["id"]
            self.label = doccano_entity["label"]
            self.start_offset = doccano_entity["start_offset"]
            self.end_offset = doccano_entity["end_offset"]

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()
