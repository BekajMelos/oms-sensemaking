import json
import re
import warnings
from datetime import datetime
from hashlib import md5

import numpy as np
from pandas import json_normalize
from rdflib import RDF, XSD, BNode, Graph, Literal, Namespace

warnings.filterwarnings("error", category=UserWarning)


class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)


class DateEncoder(object):
    def __init__(self):
        self.datetime_pattern_Z = re.compile(r"(\d{4}-\d{2}-\d{2})(T| )(\d{2}:\d{2}:\d{2})Z")
        self.datetime_pattern = re.compile(r"(\d{4}-\d{2}-\d{2})(T| )([0-9]{2}:[0-9]{2}:[0-9]{2})")
        self.date_pattern = re.compile(r'\d{4}-\d{2}-\d{2}')
        self.numeric_date_valid = re.compile(r'\d{8}')

    def __call__(self, input_string):
        print(input_string)

        if self.datetime_pattern_Z.search(input_string):
            elem = self.datetime_pattern_Z.findall(input_string.strip())
            if len(elem) != 0:
                elem = elem[0]
                value_fmt = "".join([elem[0], "T", elem[2]]).strip("Z")
                try:
                    dt = datetime.strptime(value_fmt, "%Y-%m-%dT%H:%M:%S")
                    return dt.strftime("%Y-%m-%dT%H:%M:%S"), XSD.dateTime
                except Exception:
                    return None, None

        elif self.datetime_pattern.search(input_string.strip()):
            input_string = input_string.replace(" ", "T").strip()
            try:
                dt = datetime.strptime(input_string, "%Y-%m-%dT%H:%M:%S")
                return dt.strftime("%Y-%m-%dT%H:%M:%S"), XSD.dateTime
            except Exception:
                return None, None

        elif self.date_pattern.search(input_string):
            try:
                dt = datetime.strptime(input_string, "%Y-%m-%d")
                return dt.strftime("%Y-%m-%d"), XSD.date
            except Exception:
                return None, None

        elif self.numeric_date_valid.search(input_string) and len(input_string) == 8:
            try:
                dt = datetime.strptime(input_string, '%Y%m%d')
                return dt.strftime('%Y-%m-%d'), XSD.date
            except Exception:
                return None, None

        else:
            return None, None


class AccessControlMarking(object):
    def __init__(self, namespace=None):
        self.acm_keys = sorted(
            ['_source_acm_disponly_to', '_source_acm_f_macs', '_source_acm_fgi_open', '_source_acm_disp_only',
             '_source_acm_f_sar_id', '_source_acm_sci_ctrls', '_source_acm_banner', '_source_acm_classif',
             '_source_acm_dissem_countries', '_source_acm_portion', '_source_acm_f_missions',
             '_source_acm_owner_prod', '_source_acm_dissem_ctrls', '_source_acm_non_ic', '_source_acm_rel_to',
             '_source_acm_macs', '_source_acm_atom_energy', '_source_acm_f_regions', '_source_acm_f_clearance',
             '_source_acm_f_share', '_source_acm_f_sci_ctrls', '_source_acm_f_oc_org', '_source_acm_f_atom_energy',
             '_source_acm_sar_id', '_source_acm_accms', '_source_acm_f_accms', '_source_acm_fgi_protect',
             '_source_acm_version'
             ])  # sorted order
        self.namespace = namespace

    def __call__(self, data):

        signature = []
        for k in self.acm_keys:

            attr = data.get(k)
            # attr is a collection
            if isinstance(attr, list):
                if len(attr) > 0:
                    for a in sorted(attr):  # sorted order
                        if isinstance(a, str) and len(a.strip()) > 0:
                            signature.append(a.strip())
                        else:
                            signature.append(str(a.strip()))
            else:  # is a primitive
                if isinstance(attr, str) and len(attr.strip()) > 0:
                    signature.append(attr.strip())
                else:
                    signature.append(str(attr.strip()))

        acm_guid = md5("".join(signature).encode('utf-8')).hexdigest()
        return acm_guid


class JSON2RDF(object):
    def __init__(self, source_model=None, construct=None, ns_uri=None):
        self.types = None
        self.source_data = None

        # construct query
        with open(construct, 'r') as construct_query_text:
            self.construct = construct_query_text.read()

        self.record_ns = Namespace(ns_uri)
        qry = "SELECT * WHERE {?datatype_property a owl:DatatypeProperty; rdfs:label ?l; rdfs:range ?range}"
        self.source_model = Graph().parse(source_model, format='ttl')
        self.source_lookup = {r.get('l').value: {'uri': r.get('datatype_property'), 'datatype': r.get('range')} for r in
                              self.source_model.query(qry)}
        self.encode_date = DateEncoder()
        self.make_acm = AccessControlMarking()

    def _get_typed_value(self, value, datatype):
        if value is None:
            return None
        elif isinstance(value, str):
            if value != "" and len(value) > 0:
                if datatype in [XSD.date, XSD.dateTime, XSD.dateTimeStamp]:
                    value, datatype = self.encode_date(value)
                return Literal(value, datatype=datatype)
            else:
                return None
        else:
            return Literal(value, datatype=datatype)

    def __call__(self, jsonobj: dict):
        self.g = Graph()
        df = json_normalize(data=jsonobj, sep="_", meta_prefix="_")  # ingest flattened object to dataframe
        self.types = {k: df.dtypes.get(k).__str__() for k in df.dtypes.to_dict()}
        self.source_data = {k: df[k][0] for k in df}
        record = BNode()
        self.g.add((record, RDF.type, self.record_ns.Record))
        self.source_data['_derived_acm_guid'] = self.make_acm(self.source_data)

        for k in self.source_data:
            if k not in self.source_lookup:
                continue

            value = self.source_data[k]
            datatype = self.source_lookup.get(k).get('datatype')
            datatype_property = self.source_lookup.get(k).get('uri')

            if isinstance(value, list):

                if len(value) == 0:
                    continue

                for v in value:
                    typed_value = self._get_typed_value(v, datatype)
                    if typed_value is not None:
                        self.g.add((record, datatype_property, typed_value))

            else:
                typed_value = self._get_typed_value(value, datatype)
                if typed_value is not None:
                    self.g.add((record, datatype_property, typed_value))

        return self.g.query(self.construct), self.g
