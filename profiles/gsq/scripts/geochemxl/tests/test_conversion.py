from ..convert import *
from ..models import *


GSQ_PROFILE_DIR = Path(__file__).parent.parent.resolve().parent.parent
CONCEPTS_COMBINED_GRAPH = Graph().parse(GSQ_PROFILE_DIR / "vocabs" / "concepts-combined-3.0.ttl")
TESTS_DIR = GSQ_PROFILE_DIR / "scripts" / "geochemxl" / "tests"
TEST_WORKBOOK_30_VALID = GSQ_PROFILE_DIR / "templates" / "GeochemXL-v3.0.xlsx"


class TestExtractSheetDatasetMetadata30:
    def test_extract_sheet_dataset_metadata(self):
        wb = load_workbook(TEST_WORKBOOK_30_VALID)
        d1 = extract_sheet_dataset_metadata(wb, Graph().parse(TESTS_DIR / "data" / "concepts-combined-3.0.ttl"))
        assert type(d1) == Dataset

        assert d1.date_modified == datetime.date(2023, 11, 15)

        assert d1.author.iri == "https://linked.data.gov.au/def/gsq-geochem/agent/kurrawongai"


class TestValidateSheetValidationDictionary30:
    def test_01_invalid(self):
        wb = load_workbook(TESTS_DIR / "data" / "GeochemXL-v3.0-VALIDATION_DICTIONARY_01_invalid.xlsx")
        try:
            validate_sheet_validation_dictionary(wb, Graph().parse(TESTS_DIR / "data" / "concepts-combined-3.0.ttl"))
        except ConversionError as e:
            assert str(e) == "Code xx in codelist LOC_SURVEY_TYPE on worksheet VALIDATION_DICTIONARY is not known"

    def test_02_valid(self):
        # code xx is defined by user
        wb = load_workbook(TESTS_DIR / "data" / "GeochemXL-v3.0-VALIDATION_DICTIONARY_02_valid.xlsx")
        validate_sheet_validation_dictionary(wb, Graph().parse(TESTS_DIR / "data" / "concepts-combined-3.0.ttl"))

    def test_03_invalid(self):
        # code xx is incorrectly defined as xy by user
        wb = load_workbook(TESTS_DIR / "data" / "GeochemXL-v3.0-VALIDATION_DICTIONARY_03_invalid.xlsx")
        try:
            validate_sheet_validation_dictionary(wb, Graph().parse(TESTS_DIR / "data" / "concepts-combined-3.0.ttl"))
        except ConversionError as e:
            assert str(e) == "Code xx in codelist LOC_SURVEY_TYPE on worksheet VALIDATION_DICTIONARY is not known"


class TestExtractSheetUserDictionary30:
    def test_01_valid(self):
        wb = load_workbook(TESTS_DIR / "data" / "GeochemXL-v3.0-USER_DICTIONARY_01_valid.xlsx")
        g = Graph()
        extract_sheet_user_dictionary(wb, g)

        concepts_count = 0
        notations = []
        for c in g.subjects(RDF.type, SKOS.Concept):
            concepts_count += 1
            notations.append(str(g.value(subject=c, predicate=SKOS.notation)))
        assert concepts_count == 2

        assert "TESTER" in notations

    def test_02_invalid(self):
        wb = load_workbook(TESTS_DIR / "data" / "GeochemXL-v3.0-USER_DICTIONARY_02_invalid.xlsx")
        try:
            extract_sheet_user_dictionary(wb, Graph())
        except ConversionError as e:
            assert str(e) == "You must supply a DESCRIPTION value for each code you define in the USER_DICTIONARY sheet"


class TestExtractSheetUom30:
    def test_01_valid(self):
        wb = load_workbook(TESTS_DIR / "data" / "GeochemXL-v3.0-UNITS_OF_MEASURE_01_valid.xlsx")
        validate_sheet_uom(wb, Graph().parse(TESTS_DIR / "data" / "concepts-combined-3.0.ttl"))

    def test_02_valid(self):
        # code 'ROUNDS' defined by user should be 'rounds'
        wb = load_workbook(TESTS_DIR / "data" / "GeochemXL-v3.0-UNITS_OF_MEASURE_02_invalid.xlsx")
        try:
            validate_sheet_uom(wb, Graph().parse(TESTS_DIR / "data" / "concepts-combined-3.0.ttl"))
        except ConversionError as e:
            assert str(e) == "Code rounds in codelist ROTATION on worksheet UNITS_OF_MEASURE is not known"


class TestExtractSheetUserUom30:
    def test_01_valid(self):
        wb = load_workbook(TESTS_DIR / "data" / "GeochemXL-v3.0-USER_UNITS_OF_MEASURE_01_valid.xlsx")
        g = Graph().parse(TESTS_DIR / "data" / "concepts-combined-3.0.ttl")
        extract_sheet_user_uom(wb, g)

        concepts_count = 0
        notations = []
        for c in g.subjects(RDF.type, SKOS.Concept):
            for _ in g.triples((c, SKOS.inScheme, URIRef("http://example.com/user-defined-uom"))):
                concepts_count += 1
                notations.append(str(g.value(subject=c, predicate=SKOS.notation)))
        assert concepts_count == 2

        assert "BPC" in notations

    def test_02_invalid(self):
        wb = load_workbook(TESTS_DIR / "data" / "GeochemXL-v3.0-USER_UNITS_OF_MEASURE_01_valid.xlsx")
        try:
            extract_sheet_user_uom(wb, Graph().parse(TESTS_DIR / "data" / "concepts-combined-3.0.ttl"))
        except ConversionError as e:
            assert str(e) == "You must supply a DESCRIPTION value for each code you define in the USER_UNITS_OF_MEASURE sheet"
