import json
import logging

from pydantic import UUID4
from rdflib import Graph, Literal, URIRef

from oms_sensemaking.core.oms_crud import OmsCrudTool

LOGGER: logging.Logger = logging.getLogger(__name__)

class RDFClient:
    def get_rdf_from_id(self, obj_id: UUID4, oms_crud_tool: OmsCrudTool):
        """Return service information."""
        LOGGER.info(f"RDF API request from object: {obj_id}")
        try:
            node = oms_crud_tool.get_node(obj_id)
            obj_json = node.model_dump_json()
            return self.json_to_rdf(obj_json)
        except KeyError as e:
            LOGGER.error(f"KeyError: Missing expected key in the object JSON - {str(e)}")
        except TypeError as e:
            LOGGER.error(f"TypeError: Incorrect type in the object JSON - {str(e)}")
        except ValueError as e:
            LOGGER.error(f"ValueError: Invalid data for object ID {obj_id} - {str(e)}")
        except TimeoutError as e:
            LOGGER.error(f"TimeoutError: Timeout occurred while fetching the node - {str(e)}")
        except Exception as e:
            LOGGER.error(f"Unexpected error: {repr(e)}")
        return None

    def json_to_rdf(self, obj):
        dict_obj = json.loads(obj)
        g = Graph()

        subject_id = dict_obj.get("id")
        subject = URIRef(f"{subject_id}")

        def add_triples(subj, obj, prefix=""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    predicate = URIRef(f"{prefix + k}")
                    add_triples(subj, v, prefix=prefix + k + "_")
            elif isinstance(obj, list):
                predicate = URIRef(f"{prefix.rstrip('_')}")
                for item in obj:
                    g.add((subj, predicate, Literal(item)))
            elif obj is not None:
                predicate = URIRef(f"{prefix.rstrip('_')}")
                g.add((subj, predicate, Literal(obj)))

        for key, value in dict_obj.items():
            if key != "id" and key != "permissions":
                add_triples(subject, value, prefix=key + "_")

        return g.serialize(format="turtle")
