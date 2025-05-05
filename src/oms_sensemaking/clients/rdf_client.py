import json
import logging
from typing import Optional

from fastapi import HTTPException
from oms_sdk.generated.generated_graphql_client import NodeQuery
from rdflib import RDF, Graph, Literal, Namespace, URIRef

from oms_sensemaking.api.schemas.rdf_format import RDFFormat
from oms_sensemaking.core.oms_crud import OmsCrudTool

LOGGER: logging.Logger = logging.getLogger(__name__)

class RDFClient:
    def get_rdf_from_id(self, obj_id: str, format: RDFFormat, oms_crud_tool: OmsCrudTool) -> Optional[str]:
        """
        Fetch an object by ID and convert it to an RDF string in the specified format.

        Args:
            obj_id (str): The unique identifier of the object to fetch.
            format (RDFFormat): The RDF serialization format ('turtle', 'json-ld', etc.).
            oms_crud_tool (OmsCrudTool): An instance of the OMS CRUD tool used to query the object.

        Returns:
            Optional[str]: A string containing the serialized RDF representation of the object,
                        or None if the object could not be fetched or converted.
        """
        LOGGER.info(f"RDF API request from object: {obj_id}")
        try:
            query = NodeQuery(guideIds=[obj_id])
            node = oms_crud_tool.get_nodes(query)
            obj_json = node.model_dump_json()
            return self.json_to_rdf(obj_json, format.value)
        except (ValueError, TimeoutError, AttributeError) as e:
            LOGGER.error(f"Failed to fetch RDF for object ID {obj_id} - {str(e)}")
        return None

    def json_to_rdf(self, obj, format) -> str:
        """
        Convert a JSON object to an RDF graph serialized in the specified format.

        Args:
            obj (dict): A JSON-like dictionary containing a "data" field with at least one object.
            format (str): The desired RDF serialization format ('turtle', 'json-ld', 'n3', 'nt').

        Returns:
            str: A string representing the RDF graph serialized in the specified format.
        """
        if format not in RDFFormat.__members__.values():
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
            raise HTTPException(status_code=400, detail="Missing 'guideId' in data object")

        subject = URIRef("https://oms.dodiis.ic.gov/ontology/guideId/" + subject_id)
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
            if key not in ["guideId", "permissions"]:  # Ignore 'permissions' and 'guideId' (already used)
                add_triples(subject, value, prefix=key + "_")

        return g.serialize(format=format, sort=True)
