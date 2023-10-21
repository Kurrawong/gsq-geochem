from pathlib import Path
from rdflib import Graph

profile_home = Path(__file__).parent.parent.resolve()

validator = Graph().parse(profile_home / "validator.ttl")

expander = Graph().parse(profile_home / "expander.ttl")

(validator + expander).serialize(profile_home / "validator-combined.ttl")
