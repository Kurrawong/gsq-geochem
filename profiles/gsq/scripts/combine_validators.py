from pathlib import Path
from rdflib import Graph

# core
core_profile_home = Path(__file__).parent.parent.resolve().parent / "core"

core_validator = Graph().parse(core_profile_home / "validator.ttl")

core_expander = Graph().parse(core_profile_home / "expander.ttl")

core_combined = core_validator + core_expander

core_combined.serialize(core_profile_home / "validator-combined.ttl")


# GSQ
profile_home = Path(__file__).parent.parent.resolve()

validator = Graph().parse(profile_home / "validator.ttl")

expander = Graph().parse(profile_home / "expander.ttl")

validator_combined = validator + expander

validator_combined.serialize(profile_home / "validator-combined.ttl")


# compounded
(core_combined + validator_combined).serialize(profile_home / "validator-compounded.ttl")
