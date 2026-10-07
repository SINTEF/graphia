"""Test Graphia"""

from tripper import RDF

from graphia import Graphia


def test_registered_triplestores():
    """Test registered_triplestores() method."""
    gr = Graphia()
    assert gr.triplestore_names() == ["MemKB", "GraphDBTest"]

def test_load_triplestore():
    """ Test load_triplestore() method."""
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
