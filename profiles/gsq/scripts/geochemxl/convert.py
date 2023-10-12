import argparse
import logging
import sys
from pathlib import Path
from typing import BinaryIO, Literal, Optional

import openpyxl
import rdflib
from pydantic import ValidationError



from geochemxl.models import Dataset
from geochemxl.profiles import PROFILES
from geochemxl.utils import (
    EXCEL_FILE_ENDINGS,
    KNOWN_FILE_ENDINGS,
    KNOWN_TEMPLATE_VERSIONS,
    RDF_FILE_ENDINGS,
    ConversionError,
    get_template_version,
    load_template,
    load_workbook,
    validate_with_profile,
)

TEMPLATE_VERSION = None


def extract_workbook_contents(wb: openpyxl.Workbook, template_version: float) -> rdflib.Graph:
    grf = Dataset().to_graph()

    return grf


def excel_to_rdf(
    file_to_convert_path: Path | BinaryIO,
    output_file_path: Optional[Path] = None,
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

    grf = extract_workbook_contents(wb, template_version)

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
        if not args.file_to_convert.suffix.lower().endswith(tuple(KNOWN_FILE_ENDINGS)):
            print(
                "Files for conversion must either end with .xlsx (Excel) or one of the known RDF file endings, '{}'".format(
                    "', '".join(RDF_FILE_ENDINGS.keys())
                )
            )
            parser.exit()

        print(f"Processing file {args.file_to_convert}")

        # input file looks like an Excel file, so convert Excel -> RDF
        if args.file_to_convert.suffix.lower().endswith(tuple(EXCEL_FILE_ENDINGS)):
            try:
                o = excel_to_rdf(
                    args.file_to_convert,
                    output_file_path=args.outputfile
                )
                if args.outputfile is None:
                    print(o)
            except ConversionError as err:
                logging.error("{0}".format(err))
                return 1

        # RDF file ending, so convert RDF -> Excel
        else:
            try:
                o = rdf_to_excel(
                    args.file_to_convert,
                    profile=args.profile,
                    output_file_path=args.outputfile,
                    template_file_path=args.templatefile,
                    error_level=int(args.errorlevel),
                    message_level=int(args.messagelevel),
                    log_file=args.logfile,
                )
                if args.outputfile is None:
                    print(o)
            except ConversionError as err:
                logging.error(f"{err}")
                return 1



