"""Utility functions for Graphia."""

import re
from typing import Sequence

from graphia import Graphia


def update_sparql_query(gr: Graphia, query: str) -> str:
    """Update SPARQL query `query` by translating all prefixes that needs
    translations.


    Examples:
        A CURIE `emmo:Atom` in `query` will e.g. be replaced with

            <https://w3id.org/emmo#EMMO_eb77076b_a104_42ac_a065_798b2d2809ad>

    Notes:
        This functions assumes that `query` is well-formatted,
        i.e. all CURIEs that should be translated are terminated with
        a blank.

    """

    def translate(m):
        prefix, name = m.groups()
        return gr.prefixes[prefix][name]

    for prefix in gr.prefixes:
        query = re.sub(rf"({prefix}):(\S+)", translate, query)

    return query


def simplify_iris(gr: Graphia, iris: Sequence) -> list:
    """Convert all IRIs in the (possible nested) sequence `iris` to CURIEs.

    For prefixes to namespaces that needs translations, IRIs will be
    translated to simple (formally invalid) human readable CURIEs.
    """
    retval = []
    for iri in iris:
        if isinstance(iri, str):
            for prefix, ns in gr.prefixes.items():
                if iri.startswith(str(ns)):
                    retval.append(f"{prefix}:{ns(iri)}")
                    break
            else:
                retval.append(gr.context.prefixed(iri))  # type: ignore
        elif isinstance(iri, Sequence):
            retval.append(simplify_iris(gr, iri))  # type: ignore[arg-type]
        else:
            raise TypeError(
                "Elements in `iris` must be either strings or sequences. "
                f"Got: {type(iri)}"
            )
    return retval
