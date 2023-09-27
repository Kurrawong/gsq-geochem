import sys
from rdflib import Graph
from pyshacl import validate
from pathlib import Path
import pickle

# load background vocabularies
vocabs = Graph()
vocabs_folder = Path("../../vocabs/")
for v in vocabs_folder.glob("*.ttl"):
    print(v)
    if v.with_suffix(".pkl").is_file():
        print("has Pickle")
        with open(v.with_suffix(".pkl"), "rb") as f:
            this_vocab = pickle.load(f)
    else:
        print("no Pickle")
        this_vocab = Graph().parse(v)
        with open(v.with_suffix(".pkl"), "wb") as f:
            pickle.dump(this_vocab, f)
    vocabs += this_vocab
    print(len(vocabs))

# load the given data
data = Graph().parse(sys.argv[1])
# expand Observation Collection predicates to Observations
data.update(open("oc-to-o.sparql").read())

# combine vocabs & data
combined = vocabs + data

# validate
v = validate(combined, shacl_graph=sys.argv[2])

print(v[2])
