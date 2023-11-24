import argparse
import sys
from typing import BinaryIO, Optional
from uuid import uuid4

from rdflib.namespace import SDO, SOSA

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


def extract_sheet_tenement(wb: openpyxl.Workbook):
    check_template_version_supported(wb)

    sheet = wb["TENEMENT"]


def extract_sheet_drillhole_location(wb: openpyxl.Workbook):
    check_template_version_supported(wb)

    sheet = wb["DRILLHOLE_LOCATION"]


def extract_sheet_drillhole_survey(wb: openpyxl.Workbook):
    check_template_version_supported(wb)

    sheet = wb["DRILLHOLE_SURVEY"]


def extract_sheet_drillhole_sample(wb: openpyxl.Workbook):
    check_template_version_supported(wb)

    sheet = wb["DRILLHOLE_SAMPLE"]


def extract_sheet_surface_sample(wb: openpyxl.Workbook):
    check_template_version_supported(wb)

    sheet = wb["SURFACE_SAMPLE"]


def extract_sheet_sample_preparation(wb: openpyxl.Workbook):
    check_template_version_supported(wb)

    sheet = wb["SAMPLE_PREPARATION"]


def extract_sheet_geochemistry_meta(wb: openpyxl.Workbook):
    check_template_version_supported(wb)

    sheet = wb["GEOCHEMISTRY_META"]


def extract_sheet_sample_geochemistry(wb: openpyxl.Workbook):
    check_template_version_supported(wb)

    sheet = wb["SAMPLE_GEOCHEMISTRY"]


def extract_sheet_qaqc_meta(wb: openpyxl.Workbook):
    check_template_version_supported(wb)

    sheet = wb["QAQC_META"]


def extract_sheet_qaqc_geochemistry(wb: openpyxl.Workbook):
    check_template_version_supported(wb)

    sheet = wb["QAQC_GEOCHEMISTRY"]


def extract_sheet_sample_pxrf(wb: openpyxl.Workbook):
    check_template_version_supported(wb)

    sheet = wb["SAMPLE_PXRF"]


def extract_sheet_drillhole_lithology(wb: openpyxl.Workbook):
    check_template_version_supported(wb)

    sheet = wb["DRILLHOLE_LITHOLOGY"]


def extract_sheet_drillhole_structure(wb: openpyxl.Workbook):
    check_template_version_supported(wb)

    sheet = wb["DRILLHOLE_STRUCTURE"]


def extract_sheet_surface_lithology(wb: openpyxl.Workbook):
    check_template_version_supported(wb)

    sheet = wb["SURFACE_LITHOLOGY"]


def extract_sheet_surface_structure(wb: openpyxl.Workbook):
    check_template_version_supported(wb)

    sheet = wb["SURFACE_STRUCTURE"]


def extract_sheet_lith_dictionary(wb: openpyxl.Workbook):
    check_template_version_supported(wb)

    sheet = wb["LITH_DICTIONARY"]


def extract_sheet_min_dictionary(wb: openpyxl.Workbook):
    check_template_version_supported(wb)

    sheet = wb["MIN_DICTIONARY"]


def extract_sheet_reserves_resources(wb: openpyxl.Workbook):
    check_template_version_supported(wb)

    sheet = wb["RESERVES_RESOURCES"]




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
