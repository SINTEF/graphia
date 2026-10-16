"""Test Graphia"""

# pylint: disable=invalid-name

from tripper import DCTERMS, EMMO, RDF

from graphia import Graphia


def test_registered_triplestores():
    """Test registered_triplestores() method."""
    gr = Graphia()
    assert gr.triplestore_names() == ["MemKB", "PhysMetKG", "GraphDBTest"]


def test_load_triplestore():
    """Test load_triplestore() method."""
    gr = Graphia()
    gr.load_triplestore()

    # Test that context attribute is set
    prefixes = gr.context.get_prefixes()
    assert len(prefixes) > 10
    assert prefixes["dcterms"] == "http://purl.org/dc/terms/"

    # Test that prefixes attribute is set
    EMMO = gr.prefixes["emmo"]
    assert str(EMMO) == "https://w3id.org/emmo#"
    assert EMMO.Atom == (
        "https://w3id.org/emmo#EMMO_eb77076b_a104_42ac_a065_798b2d2809ad"
    )

    # Test that the default triplestore is loaded
    triples = list(gr.ts.triples(predicate=RDF.type, object=EMMO.Dataset))
    assert len(triples) == 70


def test_all_iris():
    """Test all_iris() method."""
    gr = Graphia()
    subj, pred = gr.all_iris()
    assert subj["http://www.w3.org/ns/org#NFR"] == "org:NFR"
    assert pred[
        "https://w3id.org/emmo#EMMO_c4bace1d_4db0_4cd3_87e9_18122bae2840"
    ] == "emmo:hasOutput"


def test_update_sparql_query():
    """Test update_sparql_query()."""
    query = "SELECT ?s WHERE { ?s a emmo:Dataset }"
    gr = Graphia()
    new = gr.update_sparql_query(query)
    assert new == (
        "SELECT ?s WHERE { ?s a "
        "<https://w3id.org/emmo#EMMO_194e367c_9783_4bf5_96d0_9ad597d48d9a>"
        " }"
    )


def test_simplify_iris():
    """Test simplify_iris()."""
    gr = Graphia()
    iris = [DCTERMS.creator, EMMO.Dataset]
    assert gr.simplify_iris(iris) == ["dcterms:creator", "emmo:Dataset"]


def test_query():
    """Test query() method."""
    gr = Graphia()
    query = "SELECT ?s WHERE { ?s a emmo:Dataset }"
    result = gr.query(query)
    assert ["arp:data-EDS-ARP003"] in result


def test_search():
    """Test search() method."""
    gr = Graphia()
    table = gr.search(
        type="emmo:Dataset", criteria={"dcterms:creator": "pers:ArmelPerrotin"}
    )
    assert len(table.headers) == 13
    assert len(table.rows) == 31
