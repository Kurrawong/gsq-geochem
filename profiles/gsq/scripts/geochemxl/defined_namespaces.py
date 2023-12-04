from rdflib.namespace import DefinedNamespace, Namespace
from rdflib.term import URIRef


class BORE(DefinedNamespace):
    _NS = Namespace("https://linked.data.gov.au/def/bore/")
    _fail = True

    GeologicalSite: URIRef  # A geological feature or set of features that may be sampled or observed to determine the geological properties of an ultimate feature of interest
    Bore: URIRef  # A single or set of narrow shafts bored in the ground with a single ground surface starting point. A Bore may be constructed for many different purposes, including the extraction of water, other liquids (such as petroleum) or gases (such as natural gas), as part of a geotechnical investigation, environmental site assessment, mineral exploration, temperature measurement, as a pilot hole for installing piers or underground utilities, for geothermal installations, or for underground storage of unwanted substances, e.g. in carbon capture and storage
    Borehole: URIRef  # An individual shaft within a Bore
    BoreholeInterval: URIRef
    DrillingTime: URIRef
    Survey: URIRef

    hadDrillingMethod: URIRef  # The method used to create the Bore
    hadSurvey: URIRef
    hasInclination: URIRef  # The inclination of a Borehole at the surface from the horizontal
    hasPurpose: URIRef  # The main purpose of the Bore
    hasStatus: URIRef  # The operational status of the Bore
    hasTotalDepth: URIRef
    hasTotalDepthLogger: URIRef
    hasDiameter: URIRef
    hasDip: URIRef
    hasAzimuth: URIRef
    hasCollarDip: URIRef
    hasCollarAzimuth: URIRef


FOIS = Namespace("https://linked.data.gov.au/dataset/gsq-fois/")
SAMPLES = Namespace("https://linked.data.gov.au/dataset/gsq-samples/")
QKINDS = Namespace("http://qudt.org/vocab/quantitykind/")
TENEMENTS = Namespace("https://linked.data.gov.au/dataset/gsq-tenements/")
QLDBORES = Namespace("https://linked.data.gov.au/dataset/gsq-bores/")
LABORATORIES = Namespace("https://linked.data.gov.au/dataset/gsq-bores/")


class TENEMENT(DefinedNamespace):
    _NS = Namespace("https://linked.data.gov.au/def/mining-tenements/")
    _fail = True
    prefix = "minten"

    Tenement: URIRef
    TenementArea: URIRef
    MapSheet: URIRef

    hasProject: URIRef


class MININGROLES(DefinedNamespace):
    _NS = Namespace("https://linked.data.gov.au/def/mining-roles/")
    _fail = True

    TenementHolder: URIRef
    TenementOperator: URIRef
    Surveyer: URIRef
    Driller: URIRef
    SampleAnalyser: URIRef


class SAMPLE(DefinedNamespace):
    _NS = Namespace("https://linked.data.gov.au/def/mining-roles/")
    _fail = True

    TenementHolder: URIRef
    TenementOperator: URIRef
    Surveyer: URIRef
    Driller: URIRef
