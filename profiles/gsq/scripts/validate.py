"""Example validation script

This Python script receives and input data file in one of the three acceptable formats -
RDF, JSON or Excel - and validates it after conversion to RDF (for JSON & Excel), data
expansion and merging with background vocabularies.

The data file must have the file extension .json, .xsls or one of the standard RDF file
extensions.

If the data file ends with .json, it is validated according to the JSON Schema file
schema.json and then, if it passes validation, it is converted to RDF and then validated
according to the combined-validator.ttl SHACL RDF validator.

If the data file ends with .xlsx, it is converted to RDF using excel_to_rdf.py which also
validates that the Excel template is used correctly. If it passes validation, it is
converted to RDF and then validated according to the combined-validator.ttl SHACL RDF
validator.

If the data file is RDF - ends with a known RDF file format extension - it is parsed and
according to the combined-validator.ttl SHACL RDF validator.

Use:

    ~$ python validate.py {PATH-TO-DATA-FILE}
"""

import sys
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


def make_graph_from_excel(excel_file_path: Path):
    pass


def convert_and_validate(data_file_path):
    profile_home = Path(__file__).parent.parent.resolve()

    # parse or convert then parse data file
    if data_file_path.suffix == ".xlsx":
        raise NotImplementedError("Excel data is not yet handled")
    elif data_file_path.suffix == ".json":
        data = make_graph_from_plain_json(data_file_path)
    else:  # suffix in ["jsonld", "json-ld", "ttl", "nt", "rdf", "xml"]
        data = Graph().parse(data_file_path)

    # combine vocabs & data
    data_combined = data + Graph().parse(profile_home / "vocabs-combined.ttl")

    # validate with expansion rules included
    validator_combined = Graph().parse(profile_home / "validator-combined.ttl")
    return validate(data_combined, shacl_graph=validator_combined, advanced=True)


if __name__ == "__main__":
    print(convert_and_validate(Path(sys.argv[1]))[2])
