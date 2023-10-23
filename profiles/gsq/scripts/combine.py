from pathlib import Path
from rdflib import Graph


profile_home = Path(__file__).parent.parent.resolve()
core_profile_home = profile_home.parent / "core"
vocabs_combined = profile_home / "vocabs" / "vocabs-combined.ttl"
validator_combined = profile_home / "validator-compounded.ttl"

# combine all vocabs into combined-vocabs.ttl
vocabs = Graph()
for v in Path(profile_home / "vocabs").glob("*.ttl"):
    vocabs += Graph().parse(v)

vocabs.serialize(destination=vocabs_combined, format="longturtle")
print(f"created {vocabs_combined}")

# combine core validator.ttl & expander.ttl with GSQ Profile validator.ttl and vocabs_combined
(
    Graph().parse(core_profile_home / "expander.ttl") +
    Graph().parse(core_profile_home / "validator.ttl") +
    Graph().parse(profile_home / "validator.ttl") +
    vocabs
).serialize(destination=validator_combined, format="longturtle")

print(f"created {validator_combined}")
