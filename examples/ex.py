from pathlib import Path

from tripper import DCTERMS, EMMO, RDF, Session
from tripper.datadoc import TableDoc, acquire, get_context, search


# Load the session file. Here we use a file local file.
# The webapp should (by default) probably use the default session file
# See https://emmc-asbl.github.io/tripper/latest/session/
session = Session("session.yaml")

print("Available triplestores:", session.get_names())

# Select triplestore
ts = session.get_triplestore("MemKB")

# Add additional prefixes
PERS = ts.bind("pers", "https://www.ntnu.edu/physmet/people/")


# Load JSON-LD context from PhysMet
branch = "main"  # NB: This will soon change to master!
CONTEXT_URL = (
    "https://raw.githubusercontent.com/SINTEF/"
    f"physmet-data-documentation-templates/refs/heads/{branch}/"
    "context/context.json"
)
context = get_context(CONTEXT_URL, default_theme=None)


# Search for all datasets by Armel
# This is comes from the simple search widget
criteria = {
    RDF.type: EMMO.Dataset,
    DCTERMS.creator: PERS.ArmelPerrotin,
}

# Get a list of all matching IRIs
iris = search(ts, criteria=criteria)

# Get list of dicts describing the IRIs
dicts = [acquire(ts, iri, context=context) for iri in iris]

# Create a table (this should eventually use tabular...)
td = TableDoc.fromdicts(dicts, context=context)


# This should be shown in the table view:

# Result table headers
print("Result table headers:", td.headers)

# Result table data
#print("Result table data:", td.data)
