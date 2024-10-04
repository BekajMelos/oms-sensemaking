from oms_sensemaking.api.schemas.oms import Attribute, Node, Relationship


class NlpPublisher:
    def __init__(self, source_id: str):
        self.source_id = source_id
        self.id_mapping = {}

    def publisher_pipeline(self, findings: dict):
        """Run the publisher on the findings"""
        self.generate_ids(findings)

        attributes = self.format_attributes(findings)
        nodes = self.format_nodes(findings)
        relationships = self.format_relationships(findings)

        self.publish_attributes(attributes)
        self.publish_nodes(nodes)
        self.publish_relationships(relationships)

    def generate_ids(self, findings: dict):
        """Set self.id_mapping for nodes and relationships and generate a mapping between them"""
        # 1. Loop through the listed entities
        # 2. For each entity, generate a uuid
        # 3. Saved in self.id_mapping, map the entity-index to the uuid
        pass

    def format_nodes(self, findings: dict) -> list[Node]:
        """Format the Node objects from the findings"""
        # 1. Get the findings[ner_entities] and findings[document_entity]
        # 2. For each, format as a Node and add to list of Nodes
        pass

    def format_relationships(self, findings: dict) -> list[Relationship]:
        """Format the Relationship objects from the findings"""
        # 1. Get the findings[ner_relationships] and findings[document_relationships]
        # 2. For each, format as a Relationship and add to list of Relationships
        pass

    def format_attributes(self, findings: dict) -> list[Attribute]:
        """Format attribute for a Node or Relationship"""
        # TODO: decide what goes in an attribute (if anything)
        pass

    def publish_nodes(self, nodes: list[Node]) -> bool:
        """Publish the Nodes to OMS"""
        # 1. for each node, publish it to OMS
        pass

    def publish_relationships(self, relationships: list[Relationship]) -> bool:
        """Publish the relationships to OMS"""
        # 1. for each relationship, publish it to OMS
        pass

    def publish_attributes(self, attributes: list[Attribute]):
        """Publish the attributes to oms"""
        # 1. for each attribute, publish it to OMS linked to the corresponding node
        pass

    def get_nodes(self):
        """Get existing Nodes from OMS"""
        pass

    def get_relationships(self):
        """Get existing Relationships from OMS"""
        pass
