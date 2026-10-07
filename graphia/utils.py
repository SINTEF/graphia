"""Utility functions for Graphia."""

import re
from typing import Sequence


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

    for prefix, ns in gr.prefixes.items():
        query = re.sub(fr"({prefix}):(\S+)", translate, query)

    return query


def simplify_uris(gr: Graphia, uris: Sequence) -> list:
    """Convert all URIs in the (possible nested) sequence `uris` to CURIEs.

    For prefixes to namespaces that needs translations, URIs will be
    translated to simple (formally invalid) human readable CURIEs.
    """
    retval = []
    for uri in uris:
        if isinstance(uri, str):
            for prefix, ns in gr.prefixes.items():
                if uri.startswith(str(ns)):
                    retval.append(f"{prefix}:{ns(uri)}")
                    break
            else:
                retval.append(gr.context.prefixed(uri))
        elif isinstance(uri, Sequence):
            retval.append(simplify_uris(uri))
        else:
            raise TypeError(
                "Elements in `uris` must be either strings or sequences. "
                f"Got: {type(uri)}"
            )
    return retval
