import json
import logging

from fastapi import HTTPException, Response
from oms_sdk.generated.generated_graphql_client import NodeQuery
from rdflib import RDF, Graph, Literal, Namespace, URIRef

from oms_sensemaking.core.oms_crud import OmsCrudTool

LOGGER: logging.Logger = logging.getLogger(__name__)

class RDFClient:
    def get_rdf_from_id(self, obj_id: str, format: str, oms_crud_tool: OmsCrudTool):
        """Return service information."""
        LOGGER.info(f"RDF API request from object: {obj_id}")
        try:
            query = NodeQuery(guideIds=[obj_id])
            node = oms_crud_tool.get_nodes(query)
            obj_json = node.model_dump_json()
            return self.json_to_rdf(obj_json, format)
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

    def json_to_rdf(self, obj, format):
        if format not in ["turtle", "json-ld", "n3", "nt"]:
            raise HTTPException(status_code=400, detail="Unsupported format")

        dict_obj = json.loads(obj)

        # Focus only on the first item in the "data" list
        if "data" not in dict_obj or not dict_obj["data"]:
            raise HTTPException(status_code=400, detail="Missing 'data' field")
        data_obj = dict_obj["data"][0]

        g = Graph()
        oms = Namespace("https://oms.dodiis.ic.gov/ontology/")
        acm = Namespace("https://oms.dodiis.ic.gov/ontology/acm/")
        g.bind("oms", oms)
        g.bind("acm", acm)

        subject_id = data_obj.get("guideId")
        if not subject_id:
            raise HTTPException(status_code=400, detail="Missing 'id' in data object")

        subject = URIRef("https://oms.dodiis.ic.gov/ontology/guideId/" + f"{subject_id}")
        g.add((subject, RDF.type, oms.node))

        def get_predicate(key):
            if key.startswith("acm_"):
                return acm[key[len("acm_"):]]
            return URIRef(key)

        def add_triples(subj, obj, prefix=""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    add_triples(subj, v, prefix=prefix + k + "_")
            elif isinstance(obj, list):
                predicate = get_predicate(prefix.rstrip('_'))
                for item in obj:
                    g.add((subj, predicate, Literal(item)))
            elif obj is not None:
                predicate = get_predicate(prefix.rstrip('_'))
                g.add((subj, predicate, Literal(obj)))

        for key, value in data_obj.items():
            if key not in ["guideId", "permissions"]:  # Ignore 'permissions' and 'id' (already used)
                add_triples(subject, value, prefix=key + "_")

        output = g.serialize(format=format, sort=True)
        return Response(content=output, media_type="text/plain")
