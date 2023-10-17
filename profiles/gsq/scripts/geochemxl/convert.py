import argparse
import sys
from typing import BinaryIO, Optional
from uuid import uuid4

import openpyxl
from rdflib.namespace import RDF, SDO, SOSA

from .models import Dataset, Agent, DrillHoleSample, FeatureOfInterest, DrillHole, Geometry
from .utils import *


def extract_dataset(wb: openpyxl.Workbook, template_version: float, external_metadata: str = None) -> Dataset:
    def _extract_external_metadata():
        g = Graph().parse(external_metadata)
        iri = g.value(predicate=RDF.type, object=SDO.Dataset)
        name = g.value(subject=iri, predicate=SDO.name)
        description = g.value(subject=iri, predicate=SDO.description)
        date_created = g.value(subject=iri, predicate=SDO.dateCreated)
        date_modified = g.value(subject=iri, predicate=SDO.dateModified)
        author = None
        for o in g.objects(iri, PROV.qualifiedAttribution):
            for p, o2 in g.predicate_objects(o):
                if o2 == URIRef("http://def.isotc211.org/iso19115/-1/2018/CitationAndResponsiblePartyInformation/code/CI_RoleCode/author"):
                    author = g.value(o, PROV.agent)
        keywords = []
        for o in g.objects(subject=None, predicate=SDO.keywords):
            keywords.append(str(o))

        return Dataset(
            iri=str(iri),
            name=str(name),
            description=str(description),
            date_created=str(date_created),
            date_modified=date_modified.toPython(),
            author=Agent(iri=str(author)),
            keywords=keywords
        )

    if template_version == 2.0:
        # for v2.0, metadata must be supplied externally only
        if not external_metadata:
            raise ConversionError("If you are using an 2.0 version of the Geochem Excel template, you must supply Dataset metadata as external metadata")
        else:
            return _extract_external_metadata()

    elif template_version == 3.0:
        # for v3.0, you need not supply external metadata but, if you do, it will override metadata in the Workbook
        if external_metadata:
            return _extract_external_metadata()
        else:
            sheet = wb["DATASET_METADATA"]

            return Dataset(
                iri=sheet["B3"].value
                if string_is_http_iri(sheet["B3"].value) else "http://example.com/dataset/" + str(uuid4()),
                name=sheet["B4"].value,
                description=sheet["B5"].value,
                date_created=sheet["B6"].value,
                date_modified=sheet["B7"].value,
                author=sheet["B8"].value,
            )


def extract_drillholes(wb: openpyxl.Workbook, template_version: float) -> list[Graph]:
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


def extract_samples(wb: openpyxl.Workbook, template_version: float, known_drillholes: []) -> list[Graph]:
    # only handle v 3.0
    if not template_version == 3.0:
        return []

    sheet = wb["DRILLHOLE_SAMPLE"]

    samples = []

    # only process example row if example data altered
    if sheet["B9"].value != "DD12345":
        row = 9
    else:
        row = 10

    while True:
        if sheet[f"B{row}"].value is not None:
            foi_id = sheet[f"B{row}"].value
            sample_id = sheet[f"C{row}"].value
            if str(FOIS[foi_id]) not in known_drillholes:
                raise ValueError(f"The given Drillhole ID {foi_id} for Sample {sample_id} is unknown. "
                                 f"Must be present in the DRILLHOLE_LOCATION tab. "
                                 f"Known Drillhole IDs are: {', '.join([x.split('/')[-1] for x in known_drillholes])}")

            samples.append(
                DrillHoleSample(
                    is_sample_of=sheet[f"B{row}"].value,
                    iri=SAMPLES[sample_id],
                    sample_type=sheet[f"D{row}"].value,
                    depth_from=sheet[f"E{row}"].value,
                    depth_to=sheet[f"F{row}"].value,
                    collection_date=sheet[f"G{row}"].value,
                    dispatch_date=sheet[f"H{row}"].value,
                    specific_gravity=sheet[f"F{row}"].value,
                    magnetic_susceptibility=sheet[f"F{row}"].value,
                    remarks=str(sheet[f"F{row}"].value)
                )
            )

            row += 1
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


def main(args=None):

    if args is None:  # run via entrypoint
        args = sys.argv[1:]

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
        "-l",
        "--listprofiles",
        help="This flag, if set, must be the only flag supplied. It will cause the program to list all the vocabulary"
        " profiles that this converter, indicating both their URI and their short token for use with the"
        " -p (--profile) flag when converting Excel files",
        action="store_true",
    )

    parser.add_argument(
        "-p",
        "--profile",
        help="A profile - a specified information model - for a vocabulary. This tool understands several profiles and"
        "you can choose which one you want to convert the Excel file according to. The list of profiles - URIs "
        "and their corresponding tokens - supported by VocExcel, can be found by running the program with the "
        "flag -lp or --listprofiles.",
        default="vocpub",
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
        "-g",
        "--logfile",
        help="The file to write logging output to",
        type=Path,
        required=False,
    )

    parser.add_argument(
        "-e",
        "--external_metadata",
        help="Metadata for the Dataset object that is supplied outside the Excel file",
        type=Path,
        required=False,
        default=None
    )

    args = parser.parse_args(args)

    if not args:
        # show help if no args are given
        parser.print_help()
        parser.exit()

    if args.listprofiles:
        s = "Profiles\nToken\tIRI\n-----\t-----\n"
        for k, v in PROFILES.items():
            s += f"{k}\t{v.uri}\n"
        print(s.rstrip())
    elif args.info:
        from .__init__ import __version__

        print(f"geochemxl version: {__version__}")
        from .utils import KNOWN_TEMPLATE_VERSIONS

        print(
            f"Known template versions: {', '.join(sorted(KNOWN_TEMPLATE_VERSIONS, reverse=True))}"
        )
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

