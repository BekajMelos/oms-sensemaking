"""Enums representing the correct format input for the RDF client."""

from enum import Enum


class RDFFormat(str, Enum):
    """Enum for format values of RDF output"""

    turtle = "turtle"
    jsonld = "json-ld"
    n3 = "n3"
    nt = "nt"
