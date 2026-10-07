"""Webapp for viewing and exploring knowledge graphs."""

import contextlib
from pathlib import Path
from typing import Optional

import yaml

from tripper import Namespace, Session, Triplestore
from tripper.datadoc import Context, TableDoc, acquire, search


class ConfigError(Exception):
    """Configuration error."""


class Graphia:
    """
    """

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
