import json
import numpy as np
import re
from pandas import json_normalize
from rdflib import * 
from datetime import datetime

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)
    
class DateEncoder():
    def __init__(self):
        self.datetime_pattern_Z = re.compile('([0-9]{4}-[0-9]{2}-[0-9]{2})(T| )([0-9]{2}\:[0-9]{2}\:[0-9]{2})(Z)')
        self.datetime_pattern = re.compile('[0-9]{4}-[0-9]{2}-[0-9]{2}(T| )[0-9]{2}\:[0-9]{2}\:[0-9]{2}')
        self.date_pattern = re.compile('[0-9]{4}-[0-9]{2}-[0-9]{2}')
        
    def __call__(self,input_string):
        if self.datetime_pattern_Z.search(input_string):
            elem = self.datetime_pattern_Z.findall(input_string.strip())
            if len(elem) != 0:
                elem = elem
                return "".join([elem[0][0],"T",elem[0][2]]) , XSD.dateTime
   
        elif self.datetime_pattern.search(input_string.strip()):
            return input_string.replace(" ","T").strip() , XSD.dateTime
            
        elif self.date_pattern.search(input_string):
            return input_string, XSD.date
        
        else:
            return None, None
        
        
class JSON2RDF():
    def __init__(self, source_model=None, construct= None, ns_uri = "https://blackcape.io/source-model/osmb-midb/node#"):
        self.types = None
        self.source_data = None
        self.construct = open(construct,'r').read()
        self.record_ns = Namespace(ns_uri)
        qry="SELECT * WHERE {?datatype_property a owl:DatatypeProperty; rdfs:label ?l; rdfs:range ?range}"
        self.source_model = Graph().parse('source_model.ttl', format = 'ttl')
        self.source_lookup = {r.get('l').value:{'uri': r.get('datatype_property'), 'datatype': r.get('range') } for r in self.source_model.query(qry)}
        self.encode_date = DateEncoder()
        
        
    def __get_typed_value(self,value, datatype):
        if value is None: 
            return None
        elif (isinstance(value,str)):
            if value != "" and len(value) > 0:
                
                if datatype in [XSD.date, XSD.dateTime, XSD.dateTimeStamp]:
                    value, datatype = self.encode_date(value)
                return Literal(value,datatype=datatype) 
            else:
                return None
        else :
            return Literal(value,datatype=datatype) 
        
    def __call__(self,jsonobj:dict):
        g=Graph()
        df=json_normalize(data = jsonobj) ## ingest flattend object to dataframe
        #self.types  = { re.sub("\.","_",k):df.dtypes.get(k).__str__() for k in df.dtypes.to_dict() }
        self.source_data = { re.sub("\.","_",k):df[k][0] for k in df } 
        record = BNode()
        g.add((record, RDF.type, self.record_ns.Record))
        for k in self.source_data:
            if k not in self.source_lookup: continue
            
            value = self.source_data[k]
            datatype = self.source_lookup.get(k).get('datatype') 

            datatype_property = self.source_lookup.get(k).get('uri') 

            
            if isinstance(value,list):

                if len(value) == 0:
                    continue

                for v in value:
                    typed_value = self.__get_typed_value(v, datatype)
                    if typed_value is not None:
                        g.add((record, datatype_property ,typed_value ))
            else:
                typed_value = self.__get_typed_value(value, datatype)
                if typed_value is not None:
                    g.add((record, datatype_property ,typed_value ))
        self.g = g
        return g.query(self.construct) 


    
    

