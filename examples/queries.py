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


# What alloy designations and tempers do we have results from


# List all measurements with Grand ARM
criteria = {
    "rdf:type": "emmo:Measurement", "emmo:hasInterpreter": "nortem:GARM300F2"
}
table = gr.search(criteria=criteria)


# Who have been doint these measurements?
# Visible in the table




# List all registered operators of Grand ARM
q1 = """
SELECT ?m WHERE {
  ?m emmo:hasInterpreter nortem:GARM300F2 .
}
"""
r1 = gr.query(q1)
print()
print("Registered users of Grand ARM:")
for (iri,) in r1:
    print("  -", iri)
