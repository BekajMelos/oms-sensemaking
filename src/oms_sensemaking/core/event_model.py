import pika
import pika.spec


class Properties(pika.spec.BasicProperties):
    """Basic wrapper for encapsulating message properties from a consumer"""

    pass


class HeaderParser:
    def parse(self, properties: Properties):
        return AuditLogHeaders(properties.headers.get("iri", ""))


class AuditLogHeaders:
    def __init__(self, iri) -> None:
        self.iri = iri


def to_dict(self):
    return {"iri": self.iri}


class DefaultHeaders(AuditLogHeaders):
    def __init__(self) -> None:
        super().__init__("")
