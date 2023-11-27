import argparse
import datetime
import sys
from typing import BinaryIO, Optional, List
from uuid import uuid4
from pyproj import Transformer

from rdflib.namespace import GEO, SDO, SOSA, PROV
from .defined_namespaces import MININGROLES, TENEMENT, TENEMENTS, QLDBORES, BORE
from rdflib import Namespace
EX = Namespace("http://example.com/")

from .models import Dataset, DrillHole, DrillHoleSample, SurfaceSample, Geometry
from .utils import *
from .utils import check_template_version_supported

GSQ_PROFILE_DIR = Path(__file__).parent.parent.resolve().parent


def extract_sheet_dataset_metadata(wb: openpyxl.Workbook, combined_concepts: Graph) -> Dataset:
    check_template_version_supported(wb)

    sheet = wb["DATASET_METADATA"]

    return Dataset(
        iri=sheet["B5"].value
        if string_is_http_iri(sheet["B5"].value) else "http://example.com/dataset/" + str(uuid4()),
        name=sheet["B6"].value,
        description=sheet["B7"].value,
        date_created=sheet["B8"].value,
        date_modified=sheet["B9"].value,
        author=get_iri_from_code(sheet["B10"].value, combined_concepts),
    )


def validate_sheet_validation_dictionary(wb: openpyxl.Workbook, combined_concepts: Graph):
    check_template_version_supported(wb)

    # load user dict if not present
    if not combined_concepts.value(subject=URIRef("http://example.com/user-defined-vocab"), predicate=RDF.type):
        extract_sheet_user_dictionary(wb, combined_concepts)

    sheet = wb["VALIDATION_DICTIONARY"]

    # for every code in the VALIDATION_DICTIONARY sheet, check that either it's the notation of a Concept in the
    # combined_concepts or it's defined in the USER_DICTIONARY
    col = 1
    while True:
        codelist = sheet.cell(row=4, column=col).value

        if codelist is None:
            break
        else:
            if not combined_concepts.value(predicate=SKOS.notation, object=Literal(codelist)):
                raise ConversionError(f"Codelist {codelist} on worksheet VALIDATION_DICTIONARY is not known")

            row = 5
            while True:
                code = sheet.cell(row=row, column=col).value
                if code is None:
                    break
                else:
                    if not combined_concepts.value(predicate=SKOS.notation, object=Literal(code)):
                        raise ConversionError(f"Code {code} in codelist {codelist} on worksheet VALIDATION_DICTIONARY "
                                              f"is not known")
                row += 1

        col += 1

    allowed_codes = []
    for o in combined_concepts.objects(None, SKOS.notation):
        allowed_codes.append(str(o))


def extract_sheet_user_dictionary(wb: openpyxl.Workbook, combined_concepts: Graph) -> Graph():
    check_template_version_supported(wb)

    sheet = wb["USER_DICTIONARY"]

    row = 9
    if sheet["C9"].value == "MEGA":
        row = 10

    g = Graph()

    cs = URIRef("http://example.com/user-defined-vocab")
    g.add((cs, RDF.type, SKOS.ConceptScheme))
    g.add((cs, SKOS.prefLabel, Literal("User-defined Vocabulary")))
    g.add((cs, SKOS.notation, Literal("USER-VOC")))

    while True:
        if sheet[f"B{row}"].value is not None:
            bn = BNode()
            g.add((bn, RDF.type, SKOS.Concept))
            if sheet[f"C{row}"].value is None:
                raise ConversionError(
                    "You must supply a CODE value for each code you define in the USER_DICTIONARY sheet")
            g.add((bn, SKOS.notation, Literal(sheet[f"C{row}"].value)))
            g.add((bn, SKOS.inScheme, cs))
            if sheet[f"D{row}"].value is None:
                print()
                raise ConversionError(
                    "You must supply a DESCRIPTION value for each code you define in the USER_DICTIONARY sheet")
            g.add((bn, SKOS.definition, Literal(sheet[f"D{row}"].value)))

            row += 1
        else:
            break

    combined_concepts += g


def validate_sheet_uom(wb: openpyxl.Workbook, combined_concepts: Graph):
    check_template_version_supported(wb)
    
    # load user UoM if not present
    if not combined_concepts.value(subject=URIRef("http://example.com/user-uom"), predicate=RDF.type):
        extract_sheet_user_uom(wb, combined_concepts)

    sheet = wb["UNITS_OF_MEASURE"]

    col = 1
    while True:
        codelist = sheet.cell(row=1, column=col).value

        if codelist is None:
            break
        else:
            if not combined_concepts.value(predicate=SKOS.notation, object=Literal(codelist)):
                raise ConversionError(f"Codelist {codelist} on worksheet UNITS_OF_MEASURE is not known")

            row = 2
            while True:
                code = sheet.cell(row=row, column=col).value
                if code is None:
                    break
                else:
                    code = code.split("(")[1].split(")")[0]
                    if not combined_concepts.value(predicate=SKOS.notation, object=Literal(code)):
                        raise ConversionError(f"Code {code} in codelist {codelist} on worksheet UNITS_OF_MEASURE "
                                              f"is not known")
                row += 1

        col += 1

    allowed_codes = []
    for o in combined_concepts.objects(None, SKOS.notation):
        allowed_codes.append(str(o))


def extract_sheet_user_uom(wb: openpyxl.Workbook, combined_concepts: Graph) -> Graph():
    check_template_version_supported(wb)

    sheet = wb["USER_UNITS_OF_MEASURE"]
    
    row = 9
    if sheet["C9"].value == "kg/L":
        row = 10

    g = Graph()

    cs = URIRef("http://example.com/user-defined-uom")
    g.add((cs, RDF.type, SKOS.ConceptScheme))
    g.add((cs, SKOS.prefLabel, Literal("User-defined Units of Measure")))
    g.add((cs, SKOS.notation, Literal("USER-UOM")))

    while True:
        if sheet[f"B{row}"].value is not None:
            bn = BNode()
            g.add((bn, RDF.type, SKOS.Concept))
            g.add((bn, SKOS.inScheme, cs))
            if sheet[f"B{row}"].value is None:
                raise ConversionError(
                    "You must select a COLLECTION value for each code you define in the USER_UNITS_OF_MEASURE sheet")
            col = combined_concepts.value(predicate=SKOS.notation, object=Literal(sheet[f"B{row}"].value))
            g.add((col, SKOS.member, bn))
            g.add((col, SKOS.inScheme, cs))
            if sheet[f"C{row}"].value is None:
                raise ConversionError(
                    "You must supply a UNIT_CODE value for each unit you define in the USER_UNITS_OF_MEASURE sheet")
            g.add((bn, SKOS.notation, Literal(sheet[f"C{row}"].value)))
            if sheet[f"C{row}"].value is None:
                raise ConversionError(
                    "You must supply a LABEL value for each code you define in the USER_UNITS_OF_MEASURE sheet")
            g.add((bn, SKOS.prefLabel, Literal(sheet[f"D{row}"].value, lang="en")))
            if sheet[f"C{row}"].value is None:
                raise ConversionError(
                    "You must supply a DEFINITION value for each code you define in the USER_UNITS_OF_MEASURE sheet")
            g.add((bn, SKOS.definition, Literal(sheet[f"E{row}"].value, lang="en")))

            row += 1
        else:
            break

    combined_concepts += g


def extract_sheet_tenement(wb: openpyxl.Workbook, combined_concepts: Graph) -> Graph:
    check_template_version_supported(wb)

    sheet_name = "TENEMENT"
    sheet = wb[sheet_name]

    row = 9
    if sheet["C9"].value == 12345:
        row = 10

    g = Graph()

    while True:
        if sheet[f"B{row}"].value is not None:
            # make vars of all the sheet values
            data = {
                "required": {
                    "tenement_type": sheet[f"B{row}"].value,
                    "tenement_no": sheet[f"C{row}"].value,
                    "tenement_holder": sheet[f"D{row}"].value,
                    "project_name": sheet[f"E{row}"].value,
                    "tenement_operator": sheet[f"F{row}"].value,
                    "geodetic_datum": sheet[f"G{row}"].value,
                    "map_sheet_no": sheet[f"H{row}"].value,
                },
                "optional": {
                    "remark": sheet[f"I{row}"].value,
                }
            }

            # check required sheet values are present
            for k, v in data["required"].items():
                if v is None:
                    raise ConversionError(
                        f"For each row in the {sheet_name} worksheet, you must supply a {k.upper()} value")

            # check lookup values are valid
            validate_code(
                data["required"]["tenement_type"], "LEASE_NAME", "TENEMENT_TYPE", row, sheet_name, combined_concepts
            )

            validate_code(
                data["required"]["geodetic_datum"], "COORD_SYS_ID", "GEODETIC_DATUM", row, sheet_name, combined_concepts
            )

            # make RDFLib objects of the values
            tenement_iri = URIRef(TENEMENTS + str(data["required"]["tenement_no"]))
            tenement_type_iri = get_iri_from_code(data["required"]["tenement_type"], combined_concepts)
            tenement_holder_lit = Literal(data["required"]["tenement_holder"])
            project_name_lit = Literal(data["required"]["project_name"])
            tenement_operator_lit = Literal(data["required"]["tenement_operator"])
            geodetic_datum_iri = get_iri_from_code(data["required"]["geodetic_datum"], combined_concepts)
            map_sheet_no_lit = [
                Literal(x.strip(), datatype=TENEMENT.MapSheet)
                for x in str(data["required"]["map_sheet_no"]).split(",")
            ]

            if data["optional"]["remark"] is not None:
                remark_lit = Literal(data["optional"]["remark"])

            # make the graph
            g.add((tenement_iri, RDF.type, TENEMENT.Tenement))

            g.add((tenement_iri, SDO.additionalType, tenement_type_iri))

            qa = BNode()
            g.add((tenement_iri, PROV.qualifiedAttribution, qa))
            g.add((qa, PROV.agent, tenement_holder_lit))
            g.add((qa, PROV.hadRole, MININGROLES.TenementHolder))

            g.add((tenement_iri, TENEMENT.hasProject, project_name_lit))

            qa2 = BNode()
            g.add((tenement_iri, PROV.qualifiedAttribution, qa2))
            g.add((qa2, PROV.agent, tenement_operator_lit))
            g.add((qa2, PROV.hadRole, MININGROLES.TenementOperator))

            ta = BNode()
            g.add((ta, RDF.type, GEO.Feature))
            g.add((ta, RDF.type, TENEMENT.TenementArea))

            g.add((tenement_iri, SDO.location, ta))

            tg = BNode()
            g.add((tg, RDF.type, GEO.Geometry))
            g.add((tg, RDFS.comment, Literal(f"CRS is {geodetic_datum_iri}")))
            for map_sheet in map_sheet_no_lit:
                g.add((tg, SDO.identifier, map_sheet))

            g.add((ta, GEO.hasGeometry, tg))

            if data["optional"]["remark"] is not None:
                g.add((tenement_iri, RDFS.comment, remark_lit))

            row += 1
        else:
            break

    g.bind(TENEMENT.prefix, TENEMENT)
    return g


def extract_sheet_drillhole_location(wb: openpyxl.Workbook, combined_concepts: Graph) -> Graph:
    check_template_version_supported(wb)

    sheet_name = "DRILLHOLE_LOCATION"
    sheet = wb[sheet_name]

    row = 9
    if sheet["B9"].value == "DD12345":
        row = 10

    g = Graph()

    while True:
        if sheet[f"B{row}"].value is not None:
            # make vars of all the sheet values
            data = {
                "required": {
                    "drillhole_id": sheet[f"B{row}"].value,
                    "easting": sheet[f"C{row}"].value,
                    "northing": sheet[f"D{row}"].value,
                    "elevation": sheet[f"E{row}"].value,
                    "total_depth": sheet[f"F{row}"].value,
                    "drill_type": sheet[f"H{row}"].value,
                    "drill_diameter": sheet[f"I{row}"].value,
                    "dip": sheet[f"J{row}"].value,
                    "azimuth": sheet[f"K{row}"].value,
                    "drill_start_date": sheet[f"M{row}"].value,
                    "drill_end_date": sheet[f"N{row}"].value,
                    "location_survey_type": sheet[f"O{row}"].value,
                    "pre_collar_method": sheet[f"Q{row}"].value,
                    "pre_collar_depth": sheet[f"R{row}"].value,
                    "drill_contractor": sheet[f"S{row}"].value,
                },
                "optional": {
                    "total_depth_logger": sheet[f"G{row}"].value,
                    "current_class": sheet[f"L{row}"].value,
                    "survey_company": sheet[f"P{row}"].value,
                    "remark": sheet[f"T{row}"].value,
                }
            }

            # check required sheet values are present
            for k, v in data["required"].items():
                if v is None:
                    raise ConversionError(
                        f"For each row in the {sheet_name} worksheet, you must supply a {k.upper()} value")

            # check lookup values are valid
            validate_code(
                data["required"]["drill_type"], "DRILL_TYPE", "DRILL_TYPE", row, sheet_name,
                combined_concepts
            )

            validate_code(
                data["required"]["drill_diameter"], "DRILL_DIAMETER", "DRILL_DIAMETER", row, sheet_name,
                combined_concepts
            )

            if data["optional"]["current_class"] is not None:
                validate_code(
                    data["optional"]["current_class"], "CURRENT_CLASS", "CURRENT_CLASS", row, sheet_name,
                    combined_concepts
                )

            validate_code(
                data["required"]["location_survey_type"], "LOC_SURVEY_TYPE", "LOCATION_SURVEY_TYPE", row, sheet_name,
                combined_concepts
            )

            validate_code(
                data["required"]["pre_collar_method"], "DRILL_TYPE", "PRE_COLLAR_METHOD", row, sheet_name,
                combined_concepts
            )

            # numerical validation
            easting = dip = data["required"]["easting"]
            if type(easting) != int or easting < 0:
                raise ConversionError(
                    f"The value {easting} for EASTING in row {row} of sheet {sheet_name} is not an integer greater than 0"
                    f" as required")

            northing = dip = data["required"]["northing"]
            if type(easting) != int or easting < 0:
                raise ConversionError(
                    f"The value {northing} for NORTHING in row {row} of sheet {sheet_name} is not an integer "
                    f"greater than 0 as required")

            elevation = data["required"]["elevation"]
            if type(elevation) not in [float, int]:
                raise ConversionError(
                    f"The value {elevation} for ELEVATION in row {row} of sheet {sheet_name} is not an number"
                    f" as required")

            total_depth = data["required"]["total_depth"]
            if type(total_depth) not in [float, int] and total_depth < 0:
                raise ConversionError(
                    f"The value {total_depth} for TOTAL_DEPTH in row {row} of sheet {sheet_name} is not an number"
                    f" as required")

            dip = data["required"]["dip"]
            if 0 > dip > 90:
                raise ConversionError(
                    f"The value {dip} for DIP in row {row} of sheet {sheet_name} is not between 0 and 90 as required")

            azimuth = data["required"]["dip"]
            if 0 > azimuth > 360:
                raise ConversionError(
                    f"The value {azimuth} for DIP in row {row} of sheet {sheet_name} is not between "
                    f"0 and 360 as required")

            drill_start_date = data["required"]["drill_start_date"]
            if type(drill_start_date) != datetime.datetime:
                raise ConversionError(
                    f"The value {drill_start_date} for DRILL_START_DATE in row {row} of sheet {sheet_name} "
                    f"is not a date as required")

            drill_end_date = data["required"]["drill_end_date"]
            if type(drill_end_date) != datetime.datetime:
                raise ConversionError(
                    f"The value {drill_end_date} for DRILL_END_DATE in row {row} of sheet {sheet_name} "
                    f"is not a date as required")

            pre_collar_depth = data["required"]["pre_collar_depth"]
            if type(pre_collar_depth) not in [float, int] and total_depth < 0:
                raise ConversionError(
                    f"The value {pre_collar_depth} for PRE_COLLAR_DEPTH in row {row} of sheet {sheet_name} "
                    f"is not an number as required")

            # make RDFLib objects of the values
            drillhole_iri = URIRef(QLDBORES + str(data["required"]["drillhole_id"]))
            transformer = Transformer.from_crs("EPSG:32755", "EPSG:4326")
            lon, lat = transformer.transform(easting, northing)
            wkt = Literal(f"POINTZ({lon} {lat}, {elevation})", datatype=GEO.wktLiteral)
            total_depth_lit = Literal(total_depth)
            if data["optional"]["total_depth_logger"] is not None:
                total_depth_logger_lit = Literal(data["required"]["total_depth_logger"])
            drill_type_iri = get_iri_from_code(data["required"]["drill_type"], combined_concepts)
            drill_diameter_iri = get_iri_from_code(data["required"]["drill_diameter"], combined_concepts)
            dip_lit = Literal(dip)
            azimuth_lit = Literal(azimuth)
            if data["optional"]["current_class"] is not None:
                current_class_iri = get_iri_from_code(data["optional"]["current_class"], combined_concepts)
            drill_start_date_date = Literal(datetime.datetime.strftime(data["required"]["drill_start_date"], "%Y-%m-%d"), datatype=XSD.date)
            drill_end_date_date = Literal(datetime.datetime.strftime(data["required"]["drill_end_date"], "%Y-%m-%d"), datatype=XSD.date)
            location_survey_type_iri = get_iri_from_code(data["required"]["location_survey_type"], combined_concepts)
            if data["optional"]["survey_company"] is not None:
                survey_company_lit = Literal(data["optional"]["survey_company"])
            pre_collar_method_iri = get_iri_from_code(data["required"]["pre_collar_method"], combined_concepts)
            pre_collar_depth_lit = Literal(data["required"]["pre_collar_depth"])
            drill_contractor_lit = Literal(data["required"]["drill_contractor"])
            if data["optional"]["remark"] is not None:
                remark_lit = Literal(data["optional"]["remark"])

            # make the graph
            g.add((drillhole_iri, RDF.type, BORE.Bore))

            geom = BNode()
            g.add((drillhole_iri, GEO.hasGeometry, geom))
            g.add((geom, RDF.type, GEO.Geometry))
            g.add((geom, RDF.type, wkt))

            g.add((drillhole_iri, SDO.depth, total_depth_lit))

            if data["optional"]["total_depth_logger"] is not None:
                g.add((drillhole_iri, BORE.totalDepthLogger, total_depth_logger_lit))

            g.add((drillhole_iri, BORE.hadDrillingMethod, drill_type_iri))
            g.add((drillhole_iri, BORE.hasDiameter, drill_diameter_iri))
            g.add((drillhole_iri, BORE.hasDip, dip_lit))
            g.add((drillhole_iri, BORE.hasAzimuth, azimuth_lit))

            if data["optional"]["current_class"] is not None:
                g.add((drillhole_iri, BORE.hasPurpose, current_class_iri))

            dt = BNode()
            g.add((dt, RDF.type, BORE.DrillingTime))
            g.add((dt, PROV.startedAtTime, drill_start_date_date))
            g.add((dt, PROV.endedAtTime, drill_end_date_date))
            g.add((drillhole_iri, TIME.hasTime, dt))

            g.add((drillhole_iri, EX.locationSurveyType, location_survey_type_iri))

            if data["optional"]["survey_company"] is not None:
                sc = BNode()
                g.add((drillhole_iri, PROV.qualifiedAttribution, sc))
                g.add((sc, PROV.agent, survey_company_lit))
                g.add((sc, PROV.hadRole, MININGROLES.Surveyer))

            g.add((drillhole_iri, EX.preCollarMethod, pre_collar_method_iri))

            g.add((drillhole_iri, EX.preCollarDepth, pre_collar_depth_lit))

            dc = BNode()
            g.add((drillhole_iri, PROV.qualifiedAttribution, dc))
            g.add((dc, PROV.agent, drill_contractor_lit))
            g.add((dc, PROV.hadRole, MININGROLES.Driller))

            if data["optional"]["remark"] is not None:
                g.add((drillhole_iri, RDFS.comment, remark_lit))

            row += 1
        else:
            break

    g.bind("bore", BORE)
    g.bind("ex", EX)

    return g


def extract_sheet_drillhole_survey(wb: openpyxl.Workbook, combined_concepts: Graph, drillhole_ids: List[str]) -> Graph:
    check_template_version_supported(wb)

    sheet_name = "DRILLHOLE_SURVEY"
    sheet = wb[sheet_name]

    row = 9
    if sheet["B9"].value == "DD1234":
        row = 10

    g = Graph()

    while True:
        if sheet[f"B{row}"].value is not None:
            # make vars of all the sheet values
            data = {
                "required": {
                    "drillhole_id": sheet[f"B{row}"].value,
                    "survey_instrument": sheet[f"C{row}"].value,  # RPT_SURVEY_TYPE
                    "survey_depth": sheet[f"F{row}"].value,
                    "azimuth": sheet[f"G{row}"].value,
                    "dip": sheet[f"I{row}"].value,
                },
                "optional": {
                    "survey_company": sheet[f"D{row}"].value,
                    "survey_date": sheet[f"E{row}"].value,
                    "azimuth_accuracy": sheet[f"H{row}"].value,
                    "inclination_accuracy": sheet[f"J{row}"].value,
                    "magnetic_field": sheet[f"K{row}"].value,
                    "remark": sheet[f"L{row}"].value,
                }
            }

            # check required sheet values are present
            for k, v in data["required"].items():
                if v is None:
                    raise ConversionError(
                        f"For each row in the {sheet_name} worksheet, you must supply a {k.upper()} value")

            # check lookup values are valid
            validate_code(
                data["required"]["survey_instrument"], "RPT_SURVEY_TYPE", "SURVEY_INSTRUMENT", row, sheet_name,
                combined_concepts
            )

            # numerical validation
            survey_depth = data["required"]["survey_depth"]
            if type(survey_depth) not in [float, int] and survey_depth < 0:
                raise ConversionError(
                    f"The value {survey_depth} for TOTAL_DEPTH in row {row} of sheet {sheet_name} is not an number"
                    f" as required")

            azimuth = data["required"]["dip"]
            if 0 > azimuth > 360:
                raise ConversionError(
                    f"The value {azimuth} for DIP in row {row} of sheet {sheet_name} is not between "
                    f"0 and 360 as required")

            dip = data["required"]["dip"]
            if 0 > dip > 90:
                raise ConversionError(
                    f"The value {dip} for DIP in row {row} of sheet {sheet_name} is not between 0 and 90 as required")

            survey_date = data["optional"]["survey_date"]
            if type(survey_date) != datetime.datetime:
                raise ConversionError(
                    f"The value {survey_date} for SURVEY_DATE in row {row} of sheet {sheet_name} "
                    f"is not a date as required")

            azimuth_accuracy = data["optional"]["azimuth_accuracy"]
            if azimuth_accuracy is not None:
                if 0 > azimuth_accuracy > 100:
                    raise ConversionError(
                        f"The value {azimuth_accuracy} for DRILL_END_DATE in row {row} of sheet {sheet_name} "
                        f"is not between 0 and 100 as required")

            inclination_accuracy = data["optional"]["azimuth_accuracy"]
            if inclination_accuracy is not None:
                if 0 > inclination_accuracy > 100:
                    raise ConversionError(
                        f"The value {inclination_accuracy} for DRILL_END_DATE in row {row} of sheet {sheet_name} "
                        f"is not between 0 and 100 as required")

            magnetic_field = data["optional"]["magnetic_field"]
            if magnetic_field is not None:
                if 0 > magnetic_field > 10000000:
                    raise ConversionError(
                        f"The value {magnetic_field} for DRILL_END_DATE in row {row} of sheet {sheet_name} "
                        f"is not between 0 and 10000000 as required")

            # cross-sheet validation
            drillhole_id = str(data["required"]["drillhole_id"])
            if drillhole_id not in drillhole_ids:
                raise ConversionError(
                    f"The value {drillhole_id} for DRILLHOLE_ID in row {row} of sheet {sheet_name} "
                    f"is not present on sheet DRILLHOLE_LOCATION, DRILLHOLE_ID, as required")

            # make RDFLib objects of the values
            drillhole_iri = QLDBORES[drillhole_id]
            survey_instrument_iri = get_iri_from_code(data["required"]["survey_instrument"], combined_concepts)
            if data["optional"]["survey_company"] is not None:
                survey_company_lit = Literal(data["optional"]["survey_company"])
            if data["optional"]["survey_date"] is not None:
                survey_date_lit = Literal(datetime.datetime.strftime(data["optional"]["survey_date"], "%Y-%m-%d"), datatype=XSD.date)
            survey_depth_lit = Literal(data["required"]["survey_depth"])
            azimuth_lit = Literal(azimuth)
            if data["optional"]["azimuth_accuracy"] is not None:
                azimuth_accuracy_lit = Literal(data["optional"]["azimuth_accuracy"])
            dip_lit = Literal(dip)
            if data["optional"]["inclination_accuracy"] is not None:
                inclination_accuracy_lit = Literal(data["optional"]["inclination_accuracy"])
            if data["optional"]["magnetic_field"] is not None:
                magnetic_field_lit = Literal(data["optional"]["magnetic_field"])
            if data["optional"]["remark"] is not None:
                remark_lit = Literal(data["optional"]["remark"])

            # make the graph
            g.add((drillhole_iri, RDF.type, BORE.Bore))
            s = BNode()
            g.add((drillhole_iri, BORE.hadSurvey, s))
            g.add((s, RDF.type, BORE.Survey))  # an ObservationCollection
            g.add((s, SOSA.madeBySensor, survey_instrument_iri))
            if data["optional"]["survey_company"] is not None:
                sc = BNode()
                g.add((s, PROV.qualifiedAttribution, sc))
                g.add((sc, PROV.agent, survey_company_lit))
                g.add((sc, PROV.hadRole, MININGROLES.Surveyer))
            if data["optional"]["survey_date"] is not None:
                t = BNode()
                g.add((t, RDF.type, TIME.Instant))
                g.add((t, TIME.inXSDDateTime, survey_date_lit))
                g.add((s, TIME.hasTime, t))

            depth_obs = BNode()
            depth_res = BNode()
            g.add((s, SOSA.member, depth_obs))
            g.add((depth_obs, SOSA.observedProperty, BORE.hasTotalDepth))
            g.add((depth_obs, SOSA.hasFeatureOfInterest, drillhole_iri))
            g.add((depth_obs, SOSA.hasResult, depth_res))
            g.add((depth_res, SDO.value, survey_depth_lit))
            g.add((depth_res, SDO.unitCode, URIRef("http://qudt.org/vocab/unit/M")))

            az_obs = BNode()
            az_res = BNode()
            g.add((s, SOSA.member, az_obs))
            g.add((az_obs, SOSA.observedProperty, BORE.hasAzimuth))
            g.add((az_obs, SOSA.hasFeatureOfInterest, drillhole_iri))
            g.add((az_obs, SOSA.hasResult, az_res))
            g.add((az_res, SDO.value, azimuth_lit))
            g.add((az_res, SDO.unitCode, URIRef("http://qudt.org/vocab/unit/DEG")))

            if azimuth_accuracy is not None:
                g.add((az_res, SDO.marginOfError, azimuth_accuracy_lit))

            dip_obs = BNode()
            dip_res = BNode()
            g.add((s, SOSA.member, dip_obs))
            g.add((dip_obs, SOSA.observedProperty, BORE.hasDip))
            g.add((dip_obs, SOSA.hasFeatureOfInterest, drillhole_iri))
            g.add((dip_obs, SOSA.hasResult, dip_res))
            g.add((dip_res, SDO.value, dip_lit))
            g.add((dip_res, SDO.unitCode, URIRef("http://qudt.org/vocab/unit/DEG")))

            if inclination_accuracy is not None:
                g.add((dip_res, SDO.marginOfError, inclination_accuracy_lit))

            if magnetic_field is not None:
                mag_obs = BNode()
                mag_res = BNode()
                g.add((s, SOSA.member, mag_obs))
                g.add((mag_obs, SOSA.observedProperty, EX.hasMagneticFieldStrength))
                g.add((mag_obs, SOSA.hasFeatureOfInterest, drillhole_iri))
                g.add((mag_obs, SOSA.hasResult, mag_res))
                g.add((mag_res, SDO.value, magnetic_field_lit))
                g.add((mag_res, SDO.unitCode, URIRef("http://qudt.org/vocab/unit/NanoT")))

            if data["optional"]["remark"] is not None:
                g.add((s, RDFS.comment, remark_lit))

            row += 1
        else:
            break

    g.bind("bore", BORE)
    g.bind("unit", Namespace("http://qudt.org/vocab/unit/"))

    return g


def extract_sheet_drillhole_sample(wb: openpyxl.Workbook, combined_concepts: Graph) -> Graph:
    check_template_version_supported(wb)

    sheet_name = "DRILLHOLE_SAMPLE"
    sheet = wb[sheet_name]


def extract_sheet_surface_sample(wb: openpyxl.Workbook, combined_concepts: Graph) -> Graph:
    check_template_version_supported(wb)

    sheet = wb["SURFACE_SAMPLE"]
    sheet_name = "SURFACE_SAMPLE"
    sheet = wb[sheet_name]


def extract_sheet_sample_preparation(wb: openpyxl.Workbook, combined_concepts: Graph) -> Graph:
    check_template_version_supported(wb)

    sheet_name = "SAMPLE_PREPARATION"
    sheet = wb[sheet_name]


def extract_sheet_geochemistry_meta(wb: openpyxl.Workbook, combined_concepts: Graph) -> Graph:
    check_template_version_supported(wb)

    sheet_name = "GEOCHEMISTRY_META"
    sheet = wb[sheet_name]


def extract_sheet_sample_geochemistry(wb: openpyxl.Workbook, combined_concepts: Graph) -> Graph:
    check_template_version_supported(wb)

    sheet_name = "SAMPLE_GEOCHEMISTRY"
    sheet = wb[sheet_name]


def extract_sheet_qaqc_meta(wb: openpyxl.Workbook, combined_concepts: Graph) -> Graph:
    check_template_version_supported(wb)

    sheet_name = "QAQC_META"
    sheet = wb[sheet_name]


def extract_sheet_qaqc_geochemistry(wb: openpyxl.Workbook, combined_concepts: Graph) -> Graph:
    check_template_version_supported(wb)

    sheet_name = "QAQC_GEOCHEMISTRY"
    sheet = wb[sheet_name]


def extract_sheet_sample_pxrf(wb: openpyxl.Workbook, combined_concepts: Graph) -> Graph:
    check_template_version_supported(wb)

    sheet_name = "SAMPLE_PXRF"
    sheet = wb[sheet_name]


def extract_sheet_drillhole_lithology(wb: openpyxl.Workbook, combined_concepts: Graph) -> Graph:
    check_template_version_supported(wb)

    sheet_name = "DRILLHOLE_LITHOLOGY"
    sheet = wb[sheet_name]


def extract_sheet_drillhole_structure(wb: openpyxl.Workbook, combined_concepts: Graph) -> Graph:
    check_template_version_supported(wb)

    sheet_name = "DRILLHOLE_STRUCTURE"
    sheet = wb[sheet_name]


def extract_sheet_surface_lithology(wb: openpyxl.Workbook, combined_concepts: Graph) -> Graph:
    check_template_version_supported(wb)

    sheet_name = "SURFACE_LITHOLOGY"
    sheet = wb[sheet_name]


def extract_sheet_surface_structure(wb: openpyxl.Workbook, combined_concepts: Graph) -> Graph:
    check_template_version_supported(wb)

    sheet_name = "SURFACE_STRUCTURE"
    sheet = wb[sheet_name]


def extract_sheet_lith_dictionary(wb: openpyxl.Workbook, combined_concepts: Graph) -> Graph:
    check_template_version_supported(wb)

    sheet_name = "LITH_DICTIONARY"
    sheet = wb[sheet_name]


def extract_sheet_min_dictionary(wb: openpyxl.Workbook, combined_concepts: Graph) -> Graph:
    check_template_version_supported(wb)

    sheet_name = "MIN_DICTIONARY"
    sheet = wb[sheet_name]


def extract_sheet_reserves_resources(wb: openpyxl.Workbook, combined_concepts: Graph) -> Graph:
    check_template_version_supported(wb)

    sheet_name = "RESERVES_RESOURCES"
    sheet = wb[sheet_name]




def extract_drillholes(wb: openpyxl.Workbook) -> list[Graph]:
    # only handle v 3.0
    if not template_version == 3.0:
        return []

    sheet = wb["DRILLHOLE_LOCATION"]

    drillholes = []

    # only process example row if example data altered
    if sheet["B9"].value != "DD12345":
        row = 9
    else:
        row = 10

    while True:
        if sheet[f"B{row}"].value is not None:
            geom = Geometry(as_wkt=convert_easting_northing_elevation_to_wkt(sheet[f"C{row}"].value, sheet[f"D{row}"].value, sheet[f"E{row}"].value))
            drillholes.append(
                DrillHole(
                    iri=FOIS[sheet[f"B{row}"].value],
                    has_geometry=geom
                )
            )

            row += 1
        else:
            break

    return drillholes


def extract_samples(wb: openpyxl.Workbook, known_drillholes: []) -> list[Graph]:
    # only handle v 3.0
    if not template_version == 3.0:
        return []

    samples = []

    sheet = wb["DRILLHOLE_SAMPLE"]

    # only process example row if example data altered
    if sheet["B9"].value != "DD12345":
        row = 9
    else:
        row = 10

    while True:
        if sheet[f"C{row}"].value is not None:
            foi_id = sheet[f"B{row}"].value
            sample_id = sheet[f"C{row}"].value
            if str(FOIS[foi_id]) not in known_drillholes:
                raise ConversionError(
                    f"The given Drillhole ID {foi_id} for Sample {sample_id} is unknown. "
                    f"Must be present in the DRILLHOLE_LOCATION tab. "
                    f"Known Drillhole IDs are: {', '.join([x.split('/')[-1] for x in known_drillholes])}"
                )

            samples.append(
                DrillHoleSample(
                    is_sample_of=sheet[f"B{row}"].value,
                    iri=SAMPLES[sample_id],
                    sample_type=sheet[f"D{row}"].value,
                    depth_from=sheet[f"E{row}"].value,
                    depth_to=sheet[f"F{row}"].value,
                    collection_date=sheet[f"G{row}"].value,
                    dispatch_date=sheet[f"H{row}"].value,
                    instrument_type=sheet[f"I{row}"].value,
                    specific_gravity=sheet[f"J{row}"].value,
                    magnetic_susceptibility=sheet[f"K{row}"].value,
                    remarks=sheet[f"L{row}"].value
                )
            )

            row += 1
        else:
            break

    sheet = wb["SURFACE_SAMPLE"]

    # only process example row if example data altered
    row = 12
    if sheet["B9"].value != "SS12345":
        row = 9

    if sheet["B10"].value != "SS12346":
        row = 10

    if sheet["B11"].value != "SS12347":
        row = 11

    while True:
        if sheet[f"B{row}"].value is not None:
            sample_id = sheet[f"B{row}"].value
            geom = Geometry(
                as_wkt=convert_easting_northing_elevation_to_wkt(
                    sheet[f"I{row}"].value,
                    sheet[f"J{row}"].value,
                    sheet[f"K{row}"].value)
            )
            samples.append(
                SurfaceSample(
                    iri=SAMPLES[sample_id],
                    sample_material=sheet[f"C{row}"].value,
                    sample_type_surface=sheet[f"D{row}"].value,
                    mesh_size=sheet[f"E{row}"].value,
                    soil_sample_depth=sheet[f"F{row}"].value,
                    soil_colour=sheet[f"G{row}"].value,
                    soil_ph=sheet[f"H{row}"].value,
                    has_geometry=geom,
                    location_survey_type=sheet[f"L{row}"].value,
                    collection_date=sheet[f"M{row}"].value,
                    dispatch_date=sheet[f"N{row}"].value,
                    instrument_type=sheet[f"O{row}"].value,
                    specific_gravity=sheet[f"P{row}"].value,
                    magnetic_susceptibility=sheet[f"Q{row}"].value,
                    remarks=sheet[f"R{row}"].value,
                )
            )
        else:
            break

    return samples


def excel_to_rdf(
    file_to_convert_path: Path | BinaryIO,
    output_file_path: Optional[Path] = None,
    external_metadata: Optional[Union[Path, str]] = None
):
    """Converts a sheet within an Excel workbook to an RDF file"""
    wb = load_workbook(file_to_convert_path)
    template_version = get_template_version(wb)

    CONCEPTS_COMBINED_GRAPH = Graph().parse(GSQ_PROFILE_DIR / "vocabs" / f"concepts-combined-{template_version}.ttl")

    # test that we have a valid template variable.
    if template_version not in KNOWN_TEMPLATE_VERSIONS:
        raise ValueError(
            f"Unknown Template Version. Known Template Versions are {', '.join(KNOWN_TEMPLATE_VERSIONS)},"
            f" you supplied {template_version}"
        )

    tv = float(template_version)

    grf = extract_dataset(wb, tv, external_metadata).to_graph()

    for drillhole in extract_drillholes(wb, tv):
        grf += drillhole.to_graph()

    known_drillholes = []
    for foi in grf.subjects(RDF.type, SOSA.FeatureOfInterest):
        known_drillholes.append(str(foi))

    for sample in extract_samples(wb, tv, known_drillholes):
        grf += sample.to_graph()

    # link Drillholes to Dataset
    for s in grf.subjects(RDF.type, SDO.Dataset):
        for s2 in grf.subjects(RDF.type, SOSA.FeatureOfInterest):
            grf.add((s, SDO.hasPart, s2))

    grf.bind("qk", Namespace("http://qudt.org/vocab/quantitykind/"))
    grf.bind("unit", Namespace("http://qudt.org/vocab/unit/"))
    grf.bind("foi", FOIS)
    grf.bind("samples", SAMPLES)

    if output_file_path is not None:
        grf.serialize(destination=str(output_file_path), format="longturtle")
    else:  # print to std out
        return grf.serialize(format="longturtle")


def make_parser(args):
    parser = argparse.ArgumentParser(
        prog="geoexcelrdf", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "-i",
        "--info",
        help="The version and other info of this instance of Geochem Excel Converter",
        action="store_true",
    )

    parser.add_argument(
        "file_to_convert",
        nargs="?",  # allow 0 or 1 file name as argument
        type=Path,
        help="The Excel file to convert to a SKOS vocabulary in RDF or an RDF file to convert to an Excel file",
    )

    parser.add_argument(
        "-o",
        "--outputfile",
        help="An optionally-provided output file path. If not provided, output is to standard out",
        required=False,
    )

    parser.add_argument(
        "-e",
        "--external_metadata",
        help="Metadata for the Dataset object that is supplied outside the Excel file in an RDF file",
        type=Path,
        required=False,
        default=None
    )

    parser.add_argument(
        "-u",
        "--update_workbook",
        help="Update a given Excel Workbook's vocabularies",
        action="store_true",
    )

    return parser.parse_args(args)


def main(args=None):

    if args is None:  # run via entrypoint
        args = sys.argv[1:]

    args = make_parser(args)

    if not args:
        # show help if no args are given
        args.print_help()
        args.exit()

    elif args.info:
        from .__init__ import __version__

        print(f"geochemxl version: {__version__}")
        from .utils import KNOWN_TEMPLATE_VERSIONS

        print(
            f"Known template versions: {', '.join(sorted(KNOWN_TEMPLATE_VERSIONS, reverse=True))}"
        )
    elif args.update_workbook:
        print("Updating template")
        if args.file_to_convert is None:
            raise ValueError("If you select the option '-u', you must specify an Excel file to update")
        elif not Path(args.file_to_convert).is_file():
            raise ValueError("Files to update must exist")
        elif not args.file_to_convert.suffix.lower().endswith(tuple(EXCEL_FILE_ENDINGS)):
            raise ValueError("Files to update must end in .xslx")

        wb = load_workbook(args.file_to_convert)
        template_version = get_template_version(wb)

        # test that we have a valid template variable
        from .utils import KNOWN_TEMPLATE_VERSIONS
        if template_version not in KNOWN_TEMPLATE_VERSIONS:
            raise ValueError(
                f"Unknown Template Version. Known Template Versions are {', '.join(KNOWN_TEMPLATE_VERSIONS)},"
                f" you supplied {template_version}"
            )
        ws = wb["VALIDATION_DICTIONARY"]

        for vocab_id, vocab_path in FIELD_VOCABS.items():
            col = VOCAB_COLUMNS[vocab_id]
            row = 5
            for i in make_vocab_a_list_of_notations(vocab_path):
                ws[f"{col}{row}"] = i
                row += 1

        from openpyxl.worksheet.datavalidation import DataValidation
        dv = DataValidation(
            type="list",
            formula1="=VALIDATION_DICTIONARY!$J$5:$J$13",
            showDropDown=False
        )
        ws2 = wb["DRILLHOLE_SAMPLE"]
        ws2.add_data_validation(dv)

        print(create_vocab_validation_formula(wb, "VALIDATION_DICTIONARY", "DRILL_TYPE"))
        print(create_vocab_validation_formula(wb, "DICTIONARY", "CODE"))

        wb.save(Path(args.file_to_convert).with_suffix(".y.xlsx"))
    elif args.file_to_convert:
        print(f"Processing file {args.file_to_convert}")

        # input file looks like an Excel file, so convert Excel -> RDF
        if not args.file_to_convert.suffix.lower().endswith(tuple(EXCEL_FILE_ENDINGS)):
            raise ConversionError("Only Excel files can be converted")
        else:
            try:
                o = excel_to_rdf(
                    args.file_to_convert,
                    output_file_path=args.outputfile,
                    external_metadata=args.external_metadata
                )
                if args.outputfile is None:
                    print(o)
            except ConversionError as err:
                logging.error("{0}".format(err))
                return 1
