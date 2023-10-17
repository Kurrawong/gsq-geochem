from rdflib.namespace import DefinedNamespace, Namespace
from rdflib.term import URIRef


class BORE(DefinedNamespace):
    _NS = Namespace("https://linked.data.gov.au/def/borehole/")
    _fail = True

    GeologicalSite: URIRef  # A geological feature or set of features that may be sampled or observed to determine the geological properties of an ultimate feature of interest
    Bore: URIRef  # A single or set of narrow shafts bored in the ground with a single ground surface starting point. A Bore may be constructed for many different purposes, including the extraction of water, other liquids (such as petroleum) or gases (such as natural gas), as part of a geotechnical investigation, environmental site assessment, mineral exploration, temperature measurement, as a pilot hole for installing piers or underground utilities, for geothermal installations, or for underground storage of unwanted substances, e.g. in carbon capture and storage
    Borehole: URIRef  # An individual shaft within a Bore
    hadDrillingMethod: URIRef  # The method used to create the Bore
    hasInclination: URIRef  # The inclination of a Borehole at the surface from the horizontal
    hasPurpose: URIRef  # The main purpose of the Bore
    hasStatus: URIRef  # The operational status of the Bore


FOIS = Namespace("https://linked.data.gov.au/dataset/gsq-fois/")
SAMPLES = Namespace("https://linked.data.gov.au/dataset/gsq-samples/")