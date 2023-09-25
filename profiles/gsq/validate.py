import sys
from rdflib import Graph
from pyshacl import validate

data = Graph().parse(sys.argv[1])
data.update(open("oc-to-c.sparql").read())

v = validate(data, shacl_graph=sys.argv[2])

print(v[2])
