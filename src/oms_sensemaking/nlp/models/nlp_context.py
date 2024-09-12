class NlpContext:
    def __init__(self, user_dn):
        self.user_dn = user_dn

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()
