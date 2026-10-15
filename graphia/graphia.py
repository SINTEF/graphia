"""Webapp for viewing and exploring knowledge graphs."""

import re
from pathlib import Path
from typing import Optional, Sequence

import yaml
from tripper import Namespace, Session, Triplestore
from tripper.datadoc import Context


class ConfigError(Exception):
    """Configuration error."""


class Graphia:
    """Main class for the Graphia webapp."""

    def __init__(self) -> None:
        self.ts: Optional[Triplestore] = None

        # Name of currently selected triplestore
        self.triplestore_name: Optional[str] = None

        # Maps prefixes to namespace objects
        # Only required for namespaces that need translations (e.g. emmo)
        self.prefixes: dict[str, Namespace] = {}

        self.context: Optional[Context] = None

        self.datadir = Path(__file__).resolve().parent / "data"

        configfile = self.datadir / "default_session.yaml"
        self.session = Session(configfile)

        settingsfile = self.datadir / "default_settings.yaml"
        with open(settingsfile, encoding="utf-8") as f:
            self.settings = yaml.safe_load(f)

        # We probably don't want to call this in __init__()....
        self.load_triplestore()

    def triplestore_names(self) -> list[str]:
        """Return list with the names of all configured triplestores."""
        return self.session.get_names()

    def load_triplestore(self, name: Optional[str] = None) -> None:
        """Load triplestore with given name.

        This also (re)sets up the context and prefixes.
        """
        if name is None:
            names = self.triplestore_names()
            if not names:
                raise ConfigError("No configured triplestores.")
            name = names[0]

        ts = self.session.get_triplestore(name)

        # Load configurations for selected triplestore
        conf = self.settings.get("triplestores", {}).get(name, {})

        context = Context(theme=None)
        for ctx in conf.get("context", ()):
            context.add_context(ctx)

        prefixes = {}
        for prefix, args in conf.get("translated_namespaces", {}).items():
            prefixes[prefix] = Namespace(**args)

        # No errors has occured, then we update the instance
        self.triplestore_name = name
        self.ts = ts
        self.context = context
        self.prefixes = prefixes

    def update_sparql_query(self, query: str) -> str:
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
            return f"<{self.prefixes[prefix][name]}>"

        for prefix in self.prefixes:
            query = re.sub(rf"(?<=\s)({prefix}):(\S+)", translate, query)

        return query

    def simplify_iris(self, iris: Sequence) -> list:
        """Convert all IRIs in the (possible nested) sequence `iris` to CURIEs.

        For prefixes to namespaces that needs translations, IRIs will be
        translated to simple (formally invalid) human readable CURIEs.
        """
        retval = []
        for iri in iris:
            if isinstance(iri, str):
                for prefix, ns in self.prefixes.items():
                    if iri.startswith(str(ns)):
                        retval.append(f"{prefix}:{ns(iri)}")
                        break
                else:
                    retval.append(self.context.prefixed(iri))  # type: ignore
            elif isinstance(iri, Sequence):
                retval.append(self.simplify_iris(iri))  # type: ignore
            else:
                raise TypeError(
                    "Elements in `iris` must be either strings or sequences. "
                    f"Got: {type(iri)}"
                )
        return retval

    def query(self, query: str) -> list:
        """Execute SPARQL query.

        The query is translated from human readable form and the results to
        human readable form.
        """

        updated = self.update_sparql_query(query)
        result = self.ts.query(updated)  # type: ignore
        return self.simplify_iris(result)
