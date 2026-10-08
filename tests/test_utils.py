"""Test Graphia utility functions."""

from tripper import DCTERMS, EMMO

from graphia import Graphia
from graphia.utils import simplify_iris, update_sparql_query


def test_update_sparql_query():
    """Test update_sparql_query()."""
    query = "SELECT ?s WHERE { ?s a emmo:Dataset }"
    gr = Graphia()
    new = update_sparql_query(gr, query)
    assert new == (
        "SELECT ?s WHERE { ?s a "
        "https://w3id.org/emmo#EMMO_194e367c_9783_4bf5_96d0_9ad597d48d9a"
        " }"
    )


def test_simplify_iris():
    """Test simplify_iris()."""
    gr = Graphia()
    iris = [DCTERMS.creator, EMMO.Dataset]
    assert simplify_iris(gr, iris) == ["dcterms:creator", "emmo:Dataset"]
