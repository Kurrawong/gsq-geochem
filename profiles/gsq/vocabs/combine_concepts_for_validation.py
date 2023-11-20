from pathlib import Path
from rdflib import Graph
from rdflib.namespace import RDF, SKOS

VOCABS_DIR = Path(__file__).parent / "vocabs-codelists"
OUTPUT_FILE = Path(__file__).parent / "concepts-combined.ttl"

combined = Graph()

files = list(VOCABS_DIR.glob("*.ttl"))
files.append(Path("vocabs-uom/uom.ttl"))
for f in sorted(files):
    g = Graph().parse(f)
    for c in g.subjects(RDF.type, SKOS.Concept):
        for o in g.objects(c, SKOS.inScheme):
            combined.add((c, RDF.type, SKOS.Concept))
            combined.add((c, SKOS.inScheme, o))
            combined.add((c, SKOS.notation, g.value(subject=c, predicate=SKOS.notation)))
            combined.add((o, SKOS.notation, g.value(subject=o, predicate=SKOS.notation)))

    for col in g.subjects(RDF.type, SKOS.Collection):
        combined.add((col, SKOS.notation, g.value(subject=col, predicate=SKOS.notation)))
        for mem in g.objects(col, SKOS.member):
            combined.add((col, SKOS.member, mem))

combined.serialize(OUTPUT_FILE, format="longturtle")
