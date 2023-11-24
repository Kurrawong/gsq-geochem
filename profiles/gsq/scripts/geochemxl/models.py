import datetime
import math
from itertools import chain
from typing import List, Union, Optional
from pathlib import Path
from openpyxl import Workbook
from pydantic import BaseModel, field_validator
from pydantic import ValidationError
from rdflib import Graph, Literal, URIRef, BNode
from rdflib.namespace import GEO, OWL, PROV, RDF, RDFS, SDO, SKOS, SOSA, XSD
from .defined_namespaces import BORE, FOIS, SAMPLES
from .utils import *
EX = Namespace("http://example.com/")

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

    @field_validator("iri")
    def iri_must_be_for_known_agent(cls, v):
        g = Graph().parse(VOCABS_DIR_30 / "agent.ttl")
        for iri in g.subjects(RDF.type, None):
            if v == str(iri):
                return v
        for id in g.objects(None, SDO.identifier):
            if v == str(id):
                return g.value(predicate=SDO.identifier, object=id)
        raise ValueError(
            "The IRI of the Agent must be for a known Agent. See the Geochem Portal "
            f"(https://geochem.dev.kurrawong.ai) for the list of known Agents. You supplied {v.iri}"
        )

    def to_graph(self) -> Graph:
        g = Graph(bind_namespaces="rdflib")
        v = URIRef(self.iri)
        g.add((v, RDF.type, PROV.Agent))

        return g


class Attribution(BaseModel):
    iri: str
    agent: Agent
    had_role: str

    def to_graph(self) -> Graph:
        g = Graph(bind_namespaces="rdflib")
        v = URIRef(self.iri)
        g.add((v, RDF.type, PROV.Agent))

        return g


class Concept(BaseModel):
    iri: str


class Result(BaseModel):
    iri: str
    unit_code: Concept
    value: Union[Concept, str]
    margin_of_error: float

    def to_graph(self) -> Graph:
        g = Graph(bind_namespaces="rdflib")
        v = URIRef(self.iri)
        g.add((v, RDF.type, PROV.Agent))

        return g


class Observation(BaseModel):
    iri: str
    used_procedure: Concept
    made_by_sensor: Concept
    observed_property: Concept
    has_feature_of_interest: Concept
    result_time: Union[datetime.date, datetime.datetime]
    has_result: Result
    margin_of_error: Optional[float]

    def to_graph(self) -> Graph:
        g = Graph(bind_namespaces="rdflib")
        v = URIRef(self.iri)
        g.add((v, RDF.type, PROV.Agent))

        return g


class ObservationCollection(BaseModel):
    iri: str
    has_member: Observation


class Dataset(BaseModel):
    iri: str
    name: str
    description: str
    date_created: datetime.date
    date_modified: datetime.date
    author: Agent
    keywords: list = []
    # qualified_attribution: Attribution
    # has_part: ObservationCollection

    @field_validator("author", mode="before")
    def report_agent_in_dataset_error(cls, v):
        try:
            return Agent(iri=v)
        except ValidationError as e:
            raise ValueError(f"Within the creation of a Dataset, the input Agent for 'author' is invalid: \n{e}")

    def to_graph(self) -> Graph:
        g = Graph(bind_namespaces="rdflib")
        v = URIRef(self.iri)
        g.add((v, RDF.type, SDO.Dataset))
        g.add((v, SDO.name, Literal(self.name)))
        g.add((v, SDO.description, Literal(self.description)))
        g.add((v, SDO.dateCreated, Literal(self.date_created, datatype=XSD.date)))
        g.add((v, SDO.dateModified, Literal(self.date_modified, datatype=XSD.date)))
        qa = BNode()
        g.add((v, PROV.qualifiedAttribution, qa))
        g.add((qa, PROV.agent, URIRef(self.author.iri)))
        g.add((qa, PROV.hadRole, URIRef("http://def.isotc211.org/iso19115/-1/2018/CitationAndResponsiblePartyInformation/code/CI_RoleCode/author")))

        return g


class Geometry(BaseModel):
    as_wkt: str

    def to_graph(self) -> Graph:
        g = Graph(bind_namespaces="rdflib")
        geom = BNode()
        g.add((geom, RDF.type, GEO.Geometry))
        g.add((geom, GEO.asWKT, Literal(self.as_wkt, datatype=GEO.wktLiteral)))

        return g


class FeatureOfInterest(BaseModel):
    iri: str
    has_geometry: Geometry

    def to_graph(self) -> Graph:
        g = Graph(bind_namespaces="rdflib")

        v = URIRef(self.iri)
        geom = self.has_geometry.to_graph()
        g += geom
        g.add((v, GEO.hasGeometry, geom.value(predicate=RDF.type, object=GEO.Geometry)))

        return g


class DrillHole(FeatureOfInterest):
    def to_graph(self) -> Graph:
        g = super().to_graph()
        g.bind("bore", BORE)
        v = URIRef(self.iri)
        g.add((v, SDO.additionalType, BORE.Bore))
        g.add((v, RDF.type, SOSA.FeatureOfInterest))

        return g


class Sample(BaseModel):
    iri: str
    collection_date: datetime.date
    dispatch_date: datetime.date
    specific_gravity: Optional[float]
    magnetic_susceptibility: Optional[str]
    remarks: Optional[str] = None

    @field_validator("magnetic_susceptibility")
    def parse_mag_sus(cls, v):
        try:
            parts = v.split("x10")
            return float(parts[0]) * math.exp(int(parts[1]))
        except Exception as e:
            raise ConversionError(
                "Could not parse magnetic susceptibility. Must be of the form -Ax10B, e.g. -5x100-3. "
                f"You gave the value {v}"
            )

    def to_graph(self) -> Graph:
        g = Graph(bind_namespaces="rdflib")
        g.bind("sample", SAMPLES)
        v = URIRef(self.iri)
        g.add((v, RDF.type, SOSA.Sample))
        sampling = BNode()
        g.add((sampling, RDF.type, SOSA.Sampling))
        g.add((v, SOSA.isResultOf, sampling))
        g.add((sampling, SOSA.resultTime, Literal(self.collection_date)))
        if self.specific_gravity is not None:
            obs1 = BNode()
            g.add((v, SOSA.isFeatureOfInterestOf, obs1))
            g.add((obs1, RDF.type, SOSA.Observation))
            g.add((obs1, SOSA.hasFeatureOfInterest, v))
            g.add((obs1, SOSA.observedProperty, URIRef("http://qudt.org/vocab/quantitykind/Density")))
            res1 = BNode()
            g.add((res1, RDF.type, SOSA.Result))
            g.add((obs1, SOSA.hasResult, res1))
            g.add((res1, SDO.value, Literal(self.specific_gravity)))
            g.add((res1, SDO.unitCode, URIRef("http://qudt.org/vocab/unit/GM-PER-CentiM3")))

        if self.magnetic_susceptibility is not None:
            obs2 = BNode()
            g.add((v, SOSA.isFeatureOfInterestOf, obs2))
            g.add((obs2, RDF.type, SOSA.Observation))
            g.add((obs2, SOSA.hasFeatureOfInterest, v))
            g.add((obs2, SOSA.observedProperty, URIRef("http://qudt.org/vocab/quantitykind/MagneticSusceptability")))
            res2 = BNode()
            g.add((res2, RDF.type, SOSA.Result))
            g.add((obs2, SOSA.hasResult, res2))
            g.add((res2, SDO.value, Literal(self.magnetic_susceptibility)))

        return g


class DrillHoleSample(Sample):
    is_sample_of: str
    sample_type: str
    depth_from: float
    depth_to: float

    @field_validator("sample_type")
    def known_sample_type(cls, v):
        c = is_a_concept_in(v, Path(__file__).parent.parent.resolve().parent / "vocabs" / "sample-types.ttl")
        if c[0]:
            return v
        else:
            raise ConversionError(c[1])

    def to_graph(self) -> Graph:
        g = super().to_graph()
        v = URIRef(self.iri)
        foi = FOIS[self.is_sample_of]
        g.add((v, SOSA.isSampleOf, URIRef(foi)))
        g.add((v, SOSA.isSampleOf, URIRef(foi)))
        g.add((v, SDO.depth, Literal(self.depth_from)))
        g.add((v, SDO.depth, Literal(self.depth_to)))

        return g


class SurfaceSample(Sample):
    sample_material: str
    sample_type_surface: str
    mesh_size: str
    soil_sample_depth: str
    soil_colour: str
    soil_ph: str
    has_geometry: Geometry
    location_survey_type: str

    # @field_validator("sample_material")
    # def known_sample_material(cls, v):
    #     c = is_a_concept_in(v, FIELD_VOCABS["sample_material"])
    #     if c[0]:
    #         return v
    #     else:
    #         raise ConversionError(c[1])

    # @field_validator("sample_type_surface")
    # def known_sample_type_surface(cls, v):
    #     c = is_a_concept_in(v, FIELD_VOCABS["sample_type_surface"])
    #     if c[0]:
    #         return v
    #     else:
    #         raise ConversionError(c[1])

    @field_validator("mesh_size")
    def known_mesh_size(cls, v):
        c = is_a_concept_in(v, FIELD_VOCABS["mesh_size"])
        if c[0]:
            return v
        else:
            raise ConversionError(c[1])

    # @field_validator("soil_colour")
    # def known_soil_colour(cls, v):
    #     c = is_a_concept_in(v, FIELD_VOCABS["soil_colour"])
    #     if c[0]:
    #         return v
    #     else:
    #         raise ConversionError(c[1])

    def to_graph(self) -> Graph:
        g = super().to_graph()
        v = URIRef(self.iri)
        g.add((v, SDO.material, URIRef(self.sample_material)))
        g.add((v, EX.sampleTypeSurface, URIRef(self.sample_type_surface)))
        g.add((v, EX.meshSize, URIRef(self.mesh_size)))
        g.add((v, SDO.color, URIRef(self.soil_colour)))

        return g