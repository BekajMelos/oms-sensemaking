# Adding a Rule to the Inference Sensemaker

## Problem

You need to add a new rule to the Inference Sensemaker.

## Solution

This involves adding a file containing the rule to `src/oms_sensemaking/inference/rules` and 
adding it to the rule mapping in `src/oms_sensemaking/inference/sensemakers/inference.py`.

Below is an example of a rule that checks to see if a node has a Name attribute and if it does, 
an attribute is created indicating that a name exists for the node.

  ```
  import uuid
  from dataclasses import dataclass, field

  from oms_sdk.generated.generated_graphql_client import (
      AttributeType,
  )
  from oms_sdk.generated.generated_graphql_client.input_types import (
      AttributeQuery,
      CreateAttributeInput,
      StringQuery,
  )

  from oms_sensemaking.clients.instances import oms_client
  from oms_sensemaking.config import SETTINGS
  from oms_sensemaking.core.sensemakers import FindingBase
  from oms_sensemaking.inference.rules.base_rule import BaseRule
  from oms_sensemaking.inference.rules.rule_context import RuleContext
  from oms_sensemaking.models.sensemaking import FindingType


  @dataclass
  class AddHasNameFinding(FindingBase):
      FINDING_TYPE: FindingType = field(init=False, default=FindingType.INF_HAS_NAME)
      acm: dict
      attr_id: uuid.UUID

      def get_acm(self) -> dict:
          return self.acm


  class AddHasNameAttribute(BaseRule):
      """
      Detect when a node has a Name attribute,
      when a node has a Name attribute, add a new HasName attribute
      pointing to the node
      """

      def __init__(self, name: str = ""):
          super().__init__(name)
          self.version = (1, 0, 0)
          self.config = {
              "inference_add_has_name_attribute_iri": SETTINGS.inference_add_has_name_attribute_iri,
              "inference_add_has_name_attribute_meta_data_iri": SETTINGS.inference_add_has_name_attribute_meta_data_iri,
              "inference_tags": SETTINGS.inference_tags,
          }

      def evaluate(self, rule_context: RuleContext) -> bool:
          """
          Determine if the Attribute is a Name attribute for a node
          """

          return (
              rule_context.attribute
              and rule_context.attribute.nodeId
              and rule_context.attribute.attributeIri == SETTINGS.inference_add_has_name_attribute_iri
              and rule_context.attribute.attributeValue
          )

      def action(self, rule_context: RuleContext):
          """
          Create a metadata attribute for a node that indicates that it has a name
          """

          attr = rule_context.attribute
          attribute = CreateAttributeInput(
              attributeIri=SETTINGS.inference_add_has_name_attribute_meta_data_iri,
              attributeValue="true",
              attributeType=AttributeType.BOOLEAN,
              confidence=attr.confidence,
              sourceId=attr.sourceId,
              nodeId=attr.nodeId,
              acm=attr.acm,
              tags=SETTINGS.inference_tags,
              labels=[
                  SETTINGS.sm_inferenced_label,
                  SETTINGS.inference_sm_label,
                  SETTINGS.add_has_name_sm_label,
                  self.version_string,
              ],
          )

          response = oms_client.create_attribute(attribute)

          finding = AddHasNameFinding(attr.acm, response.id)
          self._finding_writer.save_findings([finding], self)

      def has_action_already_ran(self, rule_context: RuleContext):
          """
          Determine if a metadata attribute has already been created for a node
          """

          attr = rule_context.attribute
          if not attr:
              return False

          attribute_query = AttributeQuery(
              attributeIri=SETTINGS.inference_add_has_name_attribute_meta_data_iri,
              attributeValue=StringQuery(equals="true"),
              attributeType={
                  "is": AttributeType.BOOLEAN,
              },
              confidence={"is": (attr.confidence)},
              sourceId=attr.sourceId,
              nodeIds=[attr.nodeId],
              tags=SETTINGS.inference_tags,
              labels=[
                  SETTINGS.sm_inferenced_label,
                  SETTINGS.inference_sm_label,
                  SETTINGS.add_has_name_sm_label,
                  self.version_string,
              ],
          )

          res = oms_client.get_attributes(attribute_query)

          return len(res.data) > 0
  
  ```

After adding this to `src/oms_sensemaking/inference/rules`, it would be added to the sensemaker in
`src/oms_sensemaking/inference/sensemakers/inference.py`:

  ```
  from oms_sensemaking.inference.rules.add_has_name_attribute import AddHasNameAttribute

  class InferenceSensemaker(Sensemaker):
      def __init__(self):
          """Create a new instance of InferenceSensemaker."""
          super().__init__()
          self.version = (1, 0, 0)
          self.config = {"rules": []}
          self.engine = Engine()
          rule_mappings = {
              "toggle_add_garrison_rule": InOrOutOfGarrison("InOrOutOfGarrison"),
              "toggle_add_has_name_rule": AddHasNameAttribute("AddHasNameAttribute"),
              "toggle_incursion_rule": Incursion("Incursion"),
          }
          for setting_name, rule in rule_mappings.items():
              if getattr(SETTINGS, setting_name, False):  # Check if toggle is True
                  self.config["rules"].append(rule)
                  self.engine.add_rule(rule)
  ```
