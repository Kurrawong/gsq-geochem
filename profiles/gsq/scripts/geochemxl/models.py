import datetime
from itertools import chain
from typing import List, Union

from openpyxl import Workbook
from pydantic import BaseModel, field_validator
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import GEO, OWL, PROV, RDF, RDFS, SDO, SKOS, SOSA, XSD

try:
    from utils import all_strings_in_list_are_iris, string_is_http_iri
except ImportError:
    import sys

    sys.path.append("..")
    from geochemxl.utils import all_strings_in_list_are_iris, string_is_http_iri

ORGANISATIONS = {
    "CGI": URIRef("https://linked.data.gov.au/org/cgi"),
    "GA": URIRef("https://linked.data.gov.au/org/ga"),
    "GGIC": URIRef("https://linked.data.gov.au/org/ggic"),
    "GSQ": URIRef("https://linked.data.gov.au/org/gsq"),
    "ICSM": URIRef("https://linked.data.gov.au/org/icsm"),
    "DES": URIRef("https://linked.data.gov.au/org/des"),
    "BITRE": URIRef("https://linked.data.gov.au/org/bitre"),
    "CASA": URIRef("https://linked.data.gov.au/org/casa"),
    "ATSB": URIRef("https://linked.data.gov.au/org/atsb"),
}

ORGANISATIONS_INVERSE = {uref: name for name, uref in ORGANISATIONS.items()}


class Agent(BaseModel):
    iri: str


class Attribution(BaseModel):
    iri: str
    agent: Agent
    had_role: str


class Concept(BaseModel):
    iri: str


class Result(BaseModel):
    iri: str
    unit_code: Concept
    value: Union[Concept, str]
    margin_of_error: float


class Observation(BaseModel):
    iri: str
    used_procedure: Concept
    made_by_sensor: Concept
    observed_property: Concept
    has_feature_of_interest: Concept
    result_time: Union[datetime.date, datetime.datetime]
    has_result: Result
    margin_of_error: float


class ObservationCollection(BaseModel):
    iri: str
    has_member: Observation


class Dataset(BaseModel):
    iri: str
    # title: str
    # description: str
    # date_created: datetime.date
    # date_modified: datetime.date
    # keywords: list
    # qualified_attribution: Attribution
    # has_part: ObservationCollection

    def to_graph(self):
        g = Graph(bind_namespaces="rdflib")
        v = URIRef(self.iri)

        return g


class Geometry(BaseModel):
    as_wkt: str


class FeatureOfInterest(BaseModel):
    iri: str
    has_geometry: Geometry


class Sample(BaseModel):
    iri: str
    is_sample_of: FeatureOfInterest


