from ..convert import *
from ..models import *


GSQ_PROFILE_DIR = Path(__file__).parent.parent.resolve().parent.parent
CONCEPTS_COMBINED_GRAPH = Graph().parse(GSQ_PROFILE_DIR / "vocabs" / "concepts-combined-3.0.ttl")
TESTS_DIR = GSQ_PROFILE_DIR / "scripts" / "geochemxl" / "tests"
TEST_WORKBOOK_30_VALID = GSQ_PROFILE_DIR / "templates" / "GeochemXL-v3.0.xlsx"


# wb = load_workbook(TESTS_DIR.parent.parent.resolve().parent / "templates" / "GeochemXL-v3.0.xlsx")


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


class TestExtractSheetTenement30:
    def test_01_valid(self):
        wb = load_workbook(TESTS_DIR / "data" / "GeochemXL-v3.0-TENEMENT_01_valid.xlsx")
        cc = Graph().parse(TESTS_DIR / "data" / "concepts-combined-3.0.ttl")
        g = extract_sheet_tenement(wb, cc, URIRef("http://test.com"))

        #print(g.serialize(format="longturtle"))
        assert (URIRef("https://linked.data.gov.au/dataset/gsq-tenements/6789"), RDF.type, TENEMENT.Tenement) in g

        assert (URIRef("https://linked.data.gov.au/dataset/gsq-tenements/6789"), TENEMENT.hasProject, Literal("Test Project")) in g

    def test_02_invalid(self):
        wb = load_workbook(TESTS_DIR / "data" / "GeochemXL-v3.0-TENEMENT_02_invalid.xlsx")
        g = Graph().parse(TESTS_DIR / "data" / "concepts-combined-3.0.ttl")
        try:
            extract_sheet_tenement(wb, g)
        except ConversionError as e:
            assert str(e) == "For each tenement in the TENEMENTS worksheet, you must supply a TENEMENT_OPERATOR value"

    def test_03_invalid(self):
        wb = load_workbook(TESTS_DIR / "data" / "GeochemXL-v3.0-TENEMENT_03_invalid.xlsx")
        g = Graph().parse(TESTS_DIR / "data" / "concepts-combined-3.0.ttl")
        try:
            extract_sheet_tenement(wb, g)
        except ConversionError as e:
            assert str(e) == "The value Hello for GEODETIC_DATUM in row 10 on the TENEMENT worksheet is not within " \
                             "the COORD_SYS_ID lookup list"


class TestExtractSheetDrillholeLocation30:
    def test_01_valid(self):
        wb = load_workbook(TESTS_DIR / "data" / "GeochemXL-v3.0-DRILLHOLE_LOCATION_01_valid.xlsx")
        cc = Graph().parse(TESTS_DIR / "data" / "concepts-combined-3.0.ttl")
        g = extract_sheet_drillhole_location(wb, cc)

        assert (
            URIRef("https://linked.data.gov.au/dataset/gsq-bores/DEF123"),
            BORE.hadDrillingMethod,
            URIRef("https://linked.data.gov.au/def/gsq-geochem/drill-type/box-core")
        ) in g

    def test_02_invalid(self):
        wb = load_workbook(TESTS_DIR / "data" / "GeochemXL-v3.0-DRILLHOLE_LOCATION_02_invalid.xlsx")
        cc = Graph().parse(TESTS_DIR / "data" / "concepts-combined-3.0.ttl")
        try:
            extract_sheet_drillhole_location(wb, cc)
        except ConversionError as e:
            assert str(e) == "For each row in the DRILLHOLE_LOCATION worksheet, " \
                             "you must supply a PRE_COLLAR_DEPTH value"


class TestExtractSheetDrillholeSurvey30:
    def test_01_valid(self):
        wb = load_workbook(TESTS_DIR / "data" / "GeochemXL-v3.0-DRILLHOLE_SURVEY_01_valid.xlsx")
        cc = Graph().parse(TESTS_DIR / "data" / "concepts-combined-3.0.ttl")
        g = extract_sheet_drillhole_survey(wb, cc, ["DD1234", "DEF123"])

        # g.serialize(destination="TestExtractSheetDrillholeSurvey30.ttl", format="longturtle")
        assert (
            URIRef("https://linked.data.gov.au/dataset/gsq-bores/DD1234"),
            BORE.hadSurvey,
            None
        ) in g

    def test_02_invalid(self):
        wb = load_workbook(TESTS_DIR / "data" / "GeochemXL-v3.0-DRILLHOLE_SURVEY_02_invalid.xlsx")
        cc = Graph().parse(TESTS_DIR / "data" / "concepts-combined-3.0.ttl")
        try:
            extract_sheet_drillhole_survey(wb, cc, ["DD1234", "DEF123"])
        except ConversionError as e:
            assert str(e) == "The value DD1234x for DRILLHOLE_ID in row 10 of sheet DRILLHOLE_SURVEY is not " \
                             "present on sheet DRILLHOLE_LOCATION, DRILLHOLE_ID, as required"


class TestExtractSheetDrillholeSample30:
    def test_01_valid(self):
        wb = load_workbook(TESTS_DIR / "data" / "GeochemXL-v3.0-DRILLHOLE_SAMPLE_01_valid.xlsx")
        cc = Graph().parse(TESTS_DIR / "data" / "concepts-combined-3.0.ttl")
        g = extract_sheet_drillhole_sample(wb, cc, ["DD1234", "DEF123"])

        # print(g.serialize(format="longturtle"))
        assert (
            URIRef("https://linked.data.gov.au/dataset/gsq-samples/ABC123"),
            SOSA.isSampleOf,
            URIRef("https://linked.data.gov.au/dataset/gsq-bores/DEF123"),
        ) in g

    def test_02_invalid(self):
        wb = load_workbook(TESTS_DIR / "data" / "GeochemXL-v3.0-DRILLHOLE_SAMPLE_02_invalid.xlsx")
        cc = Graph().parse(TESTS_DIR / "data" / "concepts-combined-3.0.ttl")
        try:
            extract_sheet_drillhole_sample(wb, cc, ["DD1234", "DEF123"])
        except ConversionError as e:
            assert str(e) == "For each row in the DRILLHOLE_SAMPLE worksheet, you must supply a TO value"

    def test_03_invalid(self):
        wb = load_workbook(TESTS_DIR / "data" / "GeochemXL-v3.0-DRILLHOLE_SAMPLE_03_invalid.xlsx")
        cc = Graph().parse(TESTS_DIR / "data" / "concepts-combined-3.0.ttl")
        try:
            extract_sheet_drillhole_sample(wb, cc, ["DD1234", "DEF123"])
        except ConversionError as e:
            assert str(e) == "The value 3600 for MAGNETIC_SUSCEPTIBILITY in row 10 of sheet DRILLHOLE_SAMPLE is " \
                             "not negative, as required"


class TestExtractSheetSurfaceSample30:
    def test_01_valid(self):
        wb = load_workbook(TESTS_DIR / "data" / "GeochemXL-v3.0-SURFACE_SAMPLE_01_valid.xlsx")
        cc = Graph().parse(TESTS_DIR / "data" / "concepts-combined-3.0.ttl")
        g = extract_sheet_surface_sample(wb, cc)

        # print(g.serialize(format="longturtle"))
        assert (
            URIRef("https://linked.data.gov.au/dataset/gsq-samples/SSABCD"),
            SDO.material,
            URIRef("https://linked.data.gov.au/def/gsq-geochem/sample-material/sediment"),
        ) in g

    def test_02_invalid(self):
        wb = load_workbook(TESTS_DIR / "data" / "GeochemXL-v3.0-SURFACE_SAMPLE_02_invalid.xlsx")
        cc = Graph().parse(TESTS_DIR / "data" / "concepts-combined-3.0.ttl")
        try:
            extract_sheet_surface_sample(wb, cc)
        except ConversionError as e:
            assert str(e) == "The value hello for DISPATCH_DATE in row 12 of sheet SURFACE_SAMPLE " \
                             "is not a date as required"


class TestIntegration30:
    def test_01_valid(self):
        rdf = excel_to_rdf(TESTS_DIR / "data" / "GeochemXL-v3.0-integration_01.xlsx")
        g = Graph().parse(data=rdf, format="turtle")
        #print(g.serialize(format="longturtle"))

        assert len(g) == 148
