"""Webapp for viewing and exploring knowledge graphs."""

import os
import re
from pathlib import Path
from typing import Iterable, Mapping, Optional, Sequence

import yaml
from tabular import Table
from tripper import Namespace, Session, Triplestore
from tripper.datadoc import Context, TableDoc, acquire
from tripper.datadoc.dataset import make_query

PathType = str | Path


class ConfigError(Exception):
    """Configuration error."""


class Graphia:
    """Main class for the Graphia webapp.

    Configurations are loaded the files

      - default_session.yaml
      - default_settings.yaml

    in `confdir`.

    If `confdir` is None, the environment variable GRAPHIA_CONFDIR is
    checked. If that is not set, `confdir` defaults to ~/.config/graphia/.

    """

    def __init__(self, confdir: Optional[PathType] = None) -> None:
        self.ts: Triplestore = None

        # Name of currently selected triplestore
        self.triplestore_name: Optional[str] = None

        # Maps prefixes to namespace objects
        # Only required for namespaces that need translations (e.g. emmo)
        self.prefixes: dict[str, Namespace] = {}

        self.context: Context = None

        if not confdir:
            confdir = os.environ.get("GRAPHIA_CONFDIR")
        if not confdir:
            confdir = Path.home() / ".config" / "graphia"
        if not Path(confdir).exists():
            confdir = Path(__file__).resolve().parent / "data"

        self.confdir = Path(confdir)

        configfile = self.confdir / "default_session.yaml"
        self.session = Session(configfile)

        settingsfile = self.confdir / "default_settings.yaml"
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
        context.sync_prefixes(ts, update=False)

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
        namespaces = {str(ns): ns for ns in self.prefixes.values()}

        def translate(m):
            prefix, name = m.groups()
            return f"<{self.prefixes[prefix][name]}>"

        def translate2(m):
            ns, name = m.groups()
            return f"<{namespaces[ns][name]}>"

        for prefix, ns in self.prefixes.items():
            query = re.sub(rf"(?<=\s)({prefix}):(\S+)", translate, query)
            query = re.sub(rf"<({ns})([^>]*)>", translate2, query)

        return query

    def all_iris(self) -> tuple[dict, dict]:
        """Return two dicts.

        The first maps entity (subject and object) IRIs to human CURIEs.
        The second maps predicate IRIs to human CURIEs.
        """
        # pylint: disable=too-many-branches
        irinames: dict[str, str] = {}  # maps IRIs to names
        for prefix, ns in self.prefixes.items():
            if isinstance(ns, Namespace):
                # pylint: disable=protected-access
                ns._update_iris(
                    triplestore=ns._triplestore,
                    reload=ns._reload,
                    format=ns._format,
                )
                for name, iri in ns._iris.items():
                    irinames.setdefault(iri, f"{prefix}:{name}")

        def get_curie(iri: str) -> str:
            """Helper to resolve an IRI using caches, prefixes, or namespaces."""
            if iri in irinames:
                return irinames[iri]

            for prefix, ns in self.prefixes.items():
                if iri.startswith(str(ns)):
                    try:
                        return f"{prefix}:{ns(iri)}"
                    except Exception:
                        pass

            for prefix, ns in self.ts.namespaces.items():
                if iri.startswith(str(ns)):
                    return f"{prefix}:{iri[len(ns):]}"

            return iri
            
        subj, pred = {}, {}

        for s, p, o in self.ts.triples():
            if isinstance(s, str) and not s.startswith("_:"):
                subj[s] = get_curie(s)

            if isinstance(p, str):
                pred[p] = get_curie(p)

            if isinstance(o, str) and not o.startswith("_:") and o.startswith("http"):
                subj[o] = get_curie(o)

        return subj, pred

    def simplify_iris(self, iris: Iterable) -> list:
        """Convert all IRIs in the (possible nested) sequence `iris` to CURIEs.

        For prefixes to namespaces that needs translations, IRIs will be
        translated to simple (formally invalid) human readable CURIEs.
        """
        retval: list = []
        for iri in iris:
            if iri is None:
                retval.append(iri)
            elif isinstance(iri, str):
                if iri.startswith("_:") or iri.startswith("@"):
                    retval.append(iri)  # don't try to simplify blank nodes
                else:
                    for prefix, ns in self.prefixes.items():
                        if iri.startswith(str(ns)):
                            retval.append(f"{prefix}:{ns(iri)}")
                            break
                    else:
                        retval.append(self.context.prefixed(iri, strict=False))
            elif isinstance(iri, Sequence):
                retval.append(self.simplify_iris(iri))
            elif isinstance(iri, Mapping):
                keys = self.simplify_iris(iri.keys())
                values = self.simplify_iris(iri.values())
                retval.append(dict(zip(keys, values)))
            else:
                raise TypeError(
                    "Elements in `iris` must be either strings or sequences. "
                    f"Got: {type(iri)}"
                )
        return retval

    def query(self, query: str) -> Table:
        """Execute SPARQL query.

        The query is translated from human readable form and the results to
        human readable form.
        """
        updated = self.update_sparql_query(query)
        result = self.ts.query(updated)
        headers: list[str] = []
        if result:
            if m := re.search(r"\s*SELECT (DISTINCT)?(.*?)WHERE\s+{", updated, re.IGNORECASE | re.DOTALL):
                headers = m.groups()[1].strip().split()
            if len(headers) != len(result[0]):
                headers = [f"h{i}" for i in range(len(result[0]))]
        return Table(headers=headers, rows=self.simplify_iris(result))

    def search(
        self,
        type: Optional[str] = None,
        criteria: Optional[dict] = None,
        regex: Optional[dict] = None,
        flags: Optional[str] = None,
        skipblanks: bool = True,
    ) -> Table:
        # pylint: disable=line-too-long
        """Return a list of IRIs for all matching resources.

        Arguments:
            type: Either a [resource type] (ex: "Dataset", "Distribution", ...)
                or the IRI of a class to limit the search to.
            criteria: Exact match criteria. A dict of IRI, value pairs, where
                the IRIs refer to data properties on the resource
                match. The IRIs may use any prefix defined in
                `ts`. E.g. if the prefix `dcterms` is in `ts`, it is
                expanded and the match criteria `dcterms:title` is
                correctly parsed.
            regex: Like `criteria` but the values in the provided dict
                are regular expressions used for the matching.
            flags: Flags passed to regular expressions.
                - `s`: Dot-all mode. The . matches any character.  The default
                  doesn't match newline or carriage return.
                - `m`: Multi-line mode. The ^ and $ characters matches
                  beginning or end of line instead of beginning or end of
                  string.
                - `i`: Case-insensitive mode.
                - `q`: Special characters representing themselves.
            skipblanks: Whether to skip blank nodes.

        Returns:
            tabular.Table of matched resources.

        Examples:
            List all data resources:

                gr.search()

            List all resources with John Doe as `contactPoint`:

                gr.search(criteria={"contactPoint.hasName": "John Doe"})

            List all samples:

                gr.search(type=CHAMEO.Sample)

            List all datasets with John Doe as `contactPoint` AND are
            measured on a given sample:

                gr.search(
                    type=DCAT.Dataset,
                    criteria={
                        "contactPoint.hasName": "John Doe",
                        "fromSample": SAMPLE.batch2/sample3,
                    },
                )

            List all datasets who's title matches the regular expression
            "[Mm]agnesium":

                gr.search(
                    type=DCAT.Dataset, regex={"title": "[Mm]agnesium"},
                )

        SeeAlso:
            [resource type]: https://emmc-asbl.github.io/tripper/latest/datadoc/introduction/#resource-types

        """
        query = make_query(
            ts=self.ts,
            type=type,
            criteria=criteria,
            regex=regex,
            flags=flags,
            query_type="SELECT DISTINCT",
        )
        updated = self.update_sparql_query(query)
        iris = [iri[0] for iri in self.ts.query(updated)]

        if skipblanks:
            iris = [iri for iri in iris if not iri.startswith("_:")]

        dicts = [acquire(self.ts, iri, context=self.context) for iri in iris]
        td = TableDoc.fromdicts(dicts, context=self.context)
        simplified = self.simplify_iris(td.data)
        return Table(headers=td.headers, rows=simplified)
