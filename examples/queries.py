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


# List all measurements with Grand ARM
criteria = {
    "rdf:type": "emmo:Measurement",
    "emmo:hasInterpreter": "nortem:GARM300F2",
}
table1 = gr.search(criteria=criteria)
print()
print("IRI of experiments done with Grand ARM:")
for iri in table1["@id"]:
    print("  -", iri)


# What alloy designations and tempers are these results from?
table2 = gr.query("""
SELECT DISTINCT ?designation ?temper WHERE {
  ?sample micro:alloyDesignation ?designation .
  ?sample micro:temper ?temper .
  ?measurement emmo:hasInput ?sample .
}
""")
print()
print("Alloy designations and tempers we have results for:")
print(table2)


# Who has performed these measurements?
table3 = gr.query("""
SELECT DISTINCT ?designation ?temper ?operator WHERE {
  ?sample micro:alloyDesignation ?designation .
  ?sample micro:temper ?temper .
  ?measurement emmo:hasInput ?sample .
  ?measurement chameo:hasOperator ?b .
  ?b emmo:isTemporalPartOf ?operator .
}
""")
print()
print("Who has performed these experiments:")
print(table3)


# Where can I download the results (limit to .png files)
table4 = gr.query("""
SELECT ?measurement ?designation ?temper ?url
WHERE {
  {
    SELECT ?dataset ?url
    WHERE {
      ?dataset dcat:distribution ?distribution .
      ?distribution dcterms:format "png" ;
                    dcat:downloadURL ?url .
    }
  }

  ?measurement emmo:hasOutput ?dataset ;
               emmo:hasInput ?sample .

  ?sample micro:alloyDesignation ?designation ;
          micro:temper ?temper .
}
""")
print()
print("Measurements on the Grand ARM for which we have png files:")
print(table4)
