class TokenReference:
    def __init__(self, token: str, index: int, start_offset: int, end_offset: int, label: str, pos_tag: str):
        self.token = token
        self.index = index
        self.start_offset = start_offset
        self.end_offset = end_offset
        self.label = label
        self.pos_tag = pos_tag

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()
