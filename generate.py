import facetontology, os

# load definition
fo = facetontology.FacetOntology()
fo.load_definition("http://iplayer.mspace.fm/data/mspace/mspace.n3#mspace")

# ensure output does not exist already for this demo
output = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exhibit")
if os.path.exists(output):
    raise Exception("Output directory already exists.")

# exhibit generation config
config = {
    "output": output,
}

# generate configured exhibit into output dir
ex = facetontology.Exhibit(config)
ex.generate(fo)

