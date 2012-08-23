import urllib2

from rdflib.graph import Graph
from rdflib.term import URIRef, Literal
from cStringIO import StringIO


class FacetOntology:
    """ Parses FacetOntology definitions. """

    ns = "http://danielsmith.eu/resources/facet/#"
    rdf = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    rdfs = "http://www.w3.org/2000/01/rdf-schema#"

    def __init__(self):
        self.definition = None

    def get_and_sanitise_rdf(self, uri):
        """ RDFLib hates weird characters like ^M and stuff, so we workaround that here. Sigh. """
        if uri.startswith("http://") or uri.startswith("https://"):
            # load from internets
            obj = urllib2.urlopen(uri)
            data = "".join(obj.readlines())
            obj.close()
        else:
            # load from file
            fh = open(uri, "r")
            data = "".join(fh.readlines())
            fh.close()

        data = data.replace(chr(13), "\n") # replace ctrl+m with newline
        return data

    def load_definition(self, uri, format="n3", url=None):
        """ Load a definition from a URL. """
        self.data = None
        self.definition = {
            "uri": uri,
            "facets": {},
            "first_order_facet": None,
            "rdfsources": [],
        }

        # optionally specify the url/filename is different to the definition's URI
        if url is None:
            url = uri

        # load the RDF into a graph
        g = Graph()
        g.parse(url, format=format)

        # get the data sources
        for trip in g.triples((URIRef(uri), URIRef(self.ns+"rdfsource"), None)):
            rdfsource = str(trip[2])
            self.definition['rdfsources'].append(rdfsource)

        # TODO support sparql sources

        # load rdf sources
        self.data = Graph()
        for source in self.definition['rdfsources']:
            fmt = "xml"
            if source.endswith("n3"):
                fmt = "n3"
            elif source.endswith("nt"):
                fmt = "nt"
            elif source.endswith("ttl"):
                fmt = "n3" 

            print "Parsing %s as %s" % (source, fmt)
            rdfdata = self.get_and_sanitise_rdf(source)
            self.data.parse(StringIO(rdfdata), format=fmt)

        # parse the slice
        for t in g.triples((URIRef(uri), URIRef(self.ns+"slice"), None)):
            slice = t[2]
            self.definition["slice"] = []

            while slice is not None:
                thisslice = slice
                slice = None
                for t2 in g.triples((thisslice, URIRef(self.ns+"next"), None)):
                    slice = t2[2]

                if slice is not None:
                    for t2 in g.triples((slice, URIRef(self.ns+"faceturi"), None)):
                        faceturi = t2[2]
                    self.definition["slice"].append(str(faceturi))

        # parse the facets
        for t in g.triples((URIRef(uri), URIRef(self.ns+"faceturi"), None)):
            facet = t[2]
            self.definition['facets'][str(facet)] = {"uri": str(facet)};

            # is this the first order facet?
            for trip in g.triples((facet, URIRef(self.rdf+"type"), URIRef(self.ns+"FirstOrderFacet"))):
                self.definition["first_order_facet"] = str(facet)

            # get label
            for trip in g.triples((facet, URIRef(self.rdfs+"label"), None)):
                self.definition['facets'][str(facet)]['label'] = str(trip[2])

            # get class
            for trip in g.triples((facet, URIRef(self.ns+"class"), None)):
                self.definition['facets'][str(facet)]['class'] = str(trip[2])


            if self.definition["first_order_facet"] == str(facet):
                # this is the first order facet
                pass
            else:
                # this facet is a ConnectedFacet
                pass

            


        print str(self.definition)

class Exhibit:
    """ Generates Exhibits. """

    def __init__(self, config):
        self.config = config

    def generate(self, facet_ontology):
        """ Generate the Exhibit, using this Facet Ontology definition. """
        self.facet_ontology = facet_ontology




