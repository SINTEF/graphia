"""Demonstrate some queries"""

# pylint: disable=invalid-name

from pathlib import Path

from graphia import Graphia

rootdir = Path(__file__).resolve().parent.parent
kgpath = rootdir / ".." / "PhysMetKnowledgeGraph" / "kg.ttl"


gr = Graphia()
gr.load_triplestore("PhysMetKG")

# FIX PATH
gr.ts.parse(kgpath)  # type: ignore
gr.context.sync_prefixes(gr.ts, update=False)  # type: ignore


# List all registered operators of Grand ARM
q1 = """
SELECT ?m WHERE {
  ?m emmo:hasInterpreter nortem:GARM300F2 .
}
"""

r1 = gr.query(q1)
for (iri,) in r1:
    print(iri)
