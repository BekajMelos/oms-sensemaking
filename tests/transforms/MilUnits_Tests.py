import unittest
from src.oms_sensemaking.transforms.json2rdf import JSON2RDF
import yaml
import json
from rdflib import Graph, Namespace
import os

import tracemalloc

tracemalloc.start()


class MyTestCase(unittest.TestCase):
    def setUp(self):
        config_data = open('transform-test-config.yml', 'r')
        self.configs = yaml.safe_load(config_data.read())
        config_data.close()

        self.test_data_path = self.configs.get('test_input_path')
        self.test_mil_unit_midb = self.configs.get('test_input_files')[0]  # list

        self.construct_query_path = self.configs.get('construct_query_path')
        self.source_model_path = self.configs.get("source_model_path")

        self.namespace_uri = self.configs.get("namespace_uri")

        self.output_path = self.configs.get("test_output_path")

    def test_transform(self):
        # JSON object required for the transformer
        test_obj_fin = open(f"{self.test_data_path}{self.test_mil_unit_midb}", 'r')
        test_obj = json.loads(test_obj_fin.read())
        test_obj_fin.close()

        self.assertTrue(len(test_obj) > 0)

        # instantiate an empty rdflib Graph
        aligned_graph = Graph()

        # create/apply namespace bindings
        acmtemp = Namespace("http://blackcape.io/ontology/control-markings/")
        aligned_graph.bind("acmtemp", acmtemp)
        cco = Namespace("http://www.ontologyrepository.com/CommonCoreOntologies/")
        aligned_graph.bind("cco", cco)
        dico = Namespace("http://schema.dia.mil/DefenseIntelligenceCoreOntology/")
        aligned_graph.bind("dico", dico)
        src = Namespace("http://blackcape.io/ontology/node#")
        aligned_graph.bind("src", src)
        cnyobj = Namespace("http://blackcape.io/ontology/country_obj/")
        aligned_graph.bind("cnyobj", cnyobj)
        cnyid = Namespace("http://blackcape.io/ontology/country_id/")
        aligned_graph.bind("cnyid", cnyid)

        # create the transformer executable
        self.mil_unit_transformer = JSON2RDF(
            construct=self.construct_query_path
            , source_model=self.source_model_path
            , ns_uri=self.namespace_uri)

        # pass the json object to the transformer executable, which returns
        # (1) the triple generator
        # (2) flattened RDF data (at least temporarily for review / refactoring concerns)
        aligned_triples, g = self.mil_unit_transformer(test_obj)

        for stmt in aligned_triples:
            aligned_graph.add(stmt)
        self.assertTrue(len(aligned_graph) > 0)

        # drop a copy of the RDF graph in test output
        ttl_output = open(f"{self.output_path}{self.test_mil_unit_midb.replace('.json', 'ttl')}", 'w')
        ttl_output.write(aligned_graph.serialize(format='ttl'))
        ttl_output.close()

    def tearDown(self):
        del (self.mil_unit_transformer)


if __name__ == '__main__':
    unittest.main()
