import facetontology, os

fo = facetontology.FacetOntology()
fo.load_definition("http://iplayer.mspace.fm/data/mspace/mspace.n3#mspace")

output = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exhibit")
if os.path.exists(output):
    raise Exception("Output directory already exists.")

config = {
    "output": output,
}

ex = facetontology.Exhibit(config)
ex.generate(fo)

