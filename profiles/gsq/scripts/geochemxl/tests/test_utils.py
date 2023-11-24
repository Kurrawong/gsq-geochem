from ..utils import *


GSQ_PROFILE_DIR = Path(__file__).parent.parent.resolve().parent.parent
CONCEPTS_COMBINED_GRAPH = Graph().parse(GSQ_PROFILE_DIR / "vocabs" / "concepts-combined.ttl")


def test__get_codelist_id_for_code():
    assert get_codelist_id_for_code("m", CONCEPTS_COMBINED_GRAPH) == "LENGTH"

    assert get_codelist_id_for_code("DGPS", CONCEPTS_COMBINED_GRAPH) == "LOC_SURVEY_TYPE"
