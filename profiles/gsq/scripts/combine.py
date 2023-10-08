from pathlib import Path
from rdflib import Graph


profile_home = Path(__file__).parent.parent.resolve()
vocabs_combined = profile_home / "vocabs-combined.ttl"
validator_combined = profile_home / "validator-combined.ttl"

# combine all vocabs into combined-vocabs.ttl
vocabs = Graph()
for v in Path(profile_home / "vocabs").glob("*.ttl"):
    vocabs += Graph().parse(v)

vocabs.serialize(destination=vocabs_combined, format="longturtle")
print(f"created {vocabs_combined}")

# combine expnder.ttl & validator.ttl into combined-validator.ttl
(Graph().parse(profile_home / "expander.ttl") + Graph().parse(profile_home / "validator.ttl"))\
    .serialize(destination=validator_combined, format="longturtle")
print(f"created {validator_combined}")
