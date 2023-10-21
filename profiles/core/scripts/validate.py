"""Example validation script

This Python script receives an input data file in one of the two acceptable formats -
RDF or JSON and validates it, after conversion to RDF in the case of JSON data. Data
expansion before validation is optional.

The data file to be validated must have the file extension .json or one of the standard
RDF file extensions - see https://rdflib.readthedocs.io/en/stable/intro_to_parsing.html

If the data file ends with .json, it is validated according to the JSON Schema file
schema.json and then, if it passes validation, it is converted to RDF and then validated.

If the data file is RDF - ends with a known RDF file format extension - it is parsed and
then validated.

Use:

    ~$ python validate.py -e {yes|no} {PATH-TO-DATA-FILE}

    -e, --expand:
        whether (yes) or not (no) to expand the data using the Core Profile's
        Expander script before validation. Default is no
"""

import argparse
from pathlib import Path
from rdflib import Graph
import json
from pyshacl import validate
from jsonschema import validate as json_validate


def make_graph_from_plain_json(json_file_path: Path) -> Graph:
    """Makes a plain JSON file into a JSON-LD file by combining it with this Profile's JSON-LD context
    after first validating it with schema.json"""

    schema = json.load(open(Path(__file__).parent.parent / "schema.json"))
    data = json.load(open(json_file_path))

    json_validate(instance=data, schema=schema)

    json_ld = {
        **json.load(open(Path(__file__).parent.parent.resolve() / "context.json")),
        **{
            "@graph": data
        }
    }

    rdf = Graph().parse(data=json.dumps(json_ld), format="json-ld")
    return rdf


def convert_and_validate(data_file_path, expand: bool = False):
    profile_home = Path(__file__).parent.parent.resolve()

    # parse or convert then parse data file
    if data_file_path.suffix == ".json":
        data = make_graph_from_plain_json(data_file_path)
    else:  # suffix in ["jsonld", "json-ld", "ttl", "nt", "rdf", "xml"]
        data = Graph().parse(data_file_path)

    # use the validator or the combined validator and expander
    if expand:
        validator = Graph().parse(profile_home / "validator-combined.ttl")
    else:
        validator = Graph().parse(profile_home / "validator.ttl")

    return validate(data, shacl_graph=validator, advanced=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-e",
        "--expand",
        help="whether (yes) or not (no) to expand the data using the Core Profile's Expander script before validation. "
             "Default is no",
        default="no",
    )

    parser.add_argument(
        "data_file",
        help="Path to the data file to be processed",
    )

    args = parser.parse_args()

    data_file = Path(args.data_file)
    expand = True if args.expand == "yes" else False

    print(convert_and_validate(data_file, expand)[2])
