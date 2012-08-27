import facetontology, os

# load definition
fo = facetontology.FacetOntology()
fo.load_definition("http://iplayer.mspace.fm/data/mspace/mspace.n3#mspace")
#fo.load_definition("http://cpiexplorer.danielsmith.eu/mspace.n3#mspace")

# output is ./exhibit
output = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exhibit")

# exhibit generation config
config = {
    "output": output,
}

# generate configured exhibit into output dir
ex = facetontology.Exhibit(config)
ex.generate(fo)

