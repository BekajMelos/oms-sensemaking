import json
import logging
from typing import Optional

from fastapi import HTTPException
from oms_sdk.generated.generated_graphql_client import NodeQuery, RelationshipNodeQuery, RelationshipQuery
from rdflib import RDF, Graph, Literal, Namespace, URIRef

from oms_sensemaking.api.schemas.rdf_format import RDFFormat
from oms_sensemaking.core.oms_crud import OmsCrudTool

LOGGER: logging.Logger = logging.getLogger(__name__)


class RDFClient:
    def get_rdf_from_id(self, obj_id: str, format: RDFFormat, oms_crud_tool: OmsCrudTool) -> Optional[str]:
        """
        Fetch an object by ID and convert it to an RDF string in the specified format.

        Args:
            obj_id (str): The unique identifier of the object to fetch (a node's guideId).
            format (RDFFormat): The RDF serialization format ('turtle', 'json-ld', etc.).
            oms_crud_tool (OmsCrudTool): An instance of the OMS CRUD tool used to query the object.

        Returns:
            Optional[str]: A string containing the serialized RDF representation of the node object
                        and node's relationships, or None if the object could not be fetched or converted.
        """
        LOGGER.info(f"RDF API request from object: {obj_id}")
        try:
            node_query = NodeQuery(guideIds=[obj_id])
            node = oms_crud_tool.get_nodes(node_query)
            if not node.data:
                raise HTTPException(status_code=404, detail=f"Unable to retreive data for node with guideId '{obj_id}'")
            relationship_node_query = RelationshipNodeQuery(nodeIds=[node.data[0].id])
            relationships_query = RelationshipQuery(nodes=relationship_node_query)
            relationships = oms_crud_tool.get_relationships(relationships_query)

            relationships_json = relationships.model_dump_json()
            node_obj_json = node.model_dump_json()
            return self.json_to_rdf(node_obj_json, relationships_json, format.value)
        except (ValueError, TimeoutError, AttributeError) as e:
            LOGGER.error(f"Failed to fetch RDF for object ID {obj_id} - {str(e)}")
        return None

    def json_to_rdf(self, node_obj: str, relationships_obj: str, format: str) -> str:
        """
        Convert a JSON object to an RDF graph serialized in the specified format.

        Args:
            node_obj (str): A JSON-like dictionary containing a "data" field with at least one object.
            relationships_obj (str): A JSON-like dictionary containing a "data" field with at least one object.
            format (str): The desired RDF serialization format ('turtle', 'json-ld', 'n3', 'nt').

        Returns:
            str: A string representing the RDF graph serialized in the specified format.
        """
        if format not in RDFFormat.__members__.values():
            raise HTTPException(status_code=400, detail="Unsupported format")

        node_dict_obj = json.loads(node_obj)

        # Focus only on the first item in the "data" list
        if "data" not in node_dict_obj or not node_dict_obj["data"]:
            raise HTTPException(status_code=400, detail="Missing 'data' field")
        node_data_obj = node_dict_obj["data"][0]

        g = Graph()
        oms = Namespace("https://oms.dodiis.ic.gov/ontology/")
        acm = Namespace("https://oms.dodiis.ic.gov/ontology/acm/")
        g.bind("oms", oms)
        g.bind("acm", acm)

        subject_id = node_data_obj.get("guideId")
        if not subject_id:
            raise HTTPException(status_code=400, detail="Missing 'guideId' in data object")

        subject = URIRef("https://oms.dodiis.ic.gov/ontology/guideId/" + subject_id)
        g.add((subject, RDF.type, oms.node))

        for key, value in node_data_obj.items():
            if key not in ["guideId", "permissions"]:  # Ignore 'permissions' and 'guideId' (already used)
                self.add_triples(g, subject, value, acm, prefix=key + "_")

        self.present_relationships(relationships_obj, g, oms, acm)

        return g.serialize(format=format, sort=True)

    def get_predicate(self, key, acm_ns):
        if key.startswith("acm_"):
            return acm_ns[key[len("acm_") :]]
        return URIRef(key)

    def add_triples(self, graph, subj, obj, acm_ns, prefix=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                self.add_triples(graph, subj, v, acm_ns, prefix=prefix + k + "_")
        elif isinstance(obj, list):
            predicate = self.get_predicate(prefix.rstrip("_"), acm_ns)
            for item in obj:
                graph.add((subj, predicate, Literal(item)))
        elif obj is not None:
            predicate = self.get_predicate(prefix.rstrip("_"), acm_ns)
            graph.add((subj, predicate, Literal(obj)))

    def present_relationships(self, rel_obj, graph, oms_ns, acm_ns):
        rel_dict = json.loads(rel_obj)
        if "data" in rel_dict and len(rel_dict["data"]) > 0:  # relationships could not exist meaning "data" is empty
            for rel in rel_dict["data"]:
                rel_uri = URIRef(f"https://oms.dodiis.ic.gov/ontology/relationship/{rel['id']}")
                graph.add((rel_uri, RDF.type, oms_ns.relationship))
                for key, value in rel.items():
                    if key not in ["id"]:  # Ignore 'permissions' and 'guideId' (already used)
                        self.add_triples(graph, rel_uri, value, acm_ns, prefix=key + "_")
