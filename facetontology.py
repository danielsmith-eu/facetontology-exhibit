import urllib2, json, os, pystache

from rdflib.graph import Graph
from rdflib.term import URIRef, Literal
from cStringIO import StringIO

import rdflib
from rdflib import plugin
plugin.register(
    'sparql', rdflib.query.Processor,
    'rdfextras.sparql.processor', 'Processor')
plugin.register(
    'sparql', rdflib.query.Result,
    'rdfextras.sparql.query', 'SPARQLQueryResult')

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
            # TODO check that multiple sources are not overridden
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
            self.definition['facets'][str(facet)] = {"uri": str(facet), "properties": []};

            # is this the first order facet?
            for trip in g.triples((facet, URIRef(self.rdf+"type"), URIRef(self.ns+"FirstOrderFacet"))):
                self.definition["first_order_facet"] = str(facet)

            # get label
            for trip in g.triples((facet, URIRef(self.rdfs+"label"), None)):
                self.definition['facets'][str(facet)]['label'] = str(trip[2])

            # get class
            for trip in g.triples((facet, URIRef(self.ns+"class"), None)):
                self.definition['facets'][str(facet)]['class'] = str(trip[2])

            # get type (optional!)
            self.definition['facets'][str(facet)]['type'] = self.ns+"TypeAlpha"
            for trip in g.triples((facet, URIRef(self.ns+"type"), None)):
                self.definition['facets'][str(facet)]['type'] = str(trip[2])

            # set the label uri to rdfs:label, or one that is set (if type is TypeLiteral)
            self.definition['facets'][str(facet)]['labeluri'] = self.rdfs+"label"
            if str(self.definition["facets"][str(facet)]['type']) == self.ns+"TypeLiteral":
                #TypeLiteral
                for trip in g.triples((facet, URIRef(self.ns+"labeluri"), None)):
                    self.definition['facets'][str(facet)]['labeluri'] = str(trip[2])
            else:
                # TypeAlpha
                pass

            # query for the properties
            current = facet
            while True:
                found_predicate = False
                for trip in g.triples((current, URIRef(self.ns+"nextpredicate"), None)):
                    current = trip[2]
                    found_predicate = True

                if found_predicate:
                    predicate = {"uri": None, "reverse": False}
                    for trip in g.triples((current, URIRef(self.ns+"predicateuri"), None)):
                        predicate["uri"] = str(trip[2])
                    for trip in g.triples((current, URIRef(self.ns+"reverse"), None)):
                        reverse = str(trip[2])
                        if reverse is True or reverse.lower() == "true":
                            predicate['reverse'] = True
                    
                    self.definition['facets'][str(facet)]['properties'].append(predicate) 

                else:
                    break

    def get_data(self):
        """ Get the data graph source. """
        # FIXME support sparql data
        return self.data

    def get_definition(self):
        """ Get the definition data structure. """
        return self.definition


class Exhibit:
    """ Generates Exhibits. """

    ns = "http://danielsmith.eu/resources/facet/#"
    rdf = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    rdfs = "http://www.w3.org/2000/01/rdf-schema#"

    def __init__(self, config):
        self.config = config

    def generate(self, facet_ontology):
        """ Generate the Exhibit, using this Facet Ontology definition. """
        self.facet_ontology = facet_ontology

        if not os.path.exists(self.config['output']):
            os.mkdir(self.config['output'])

        self.definition = facet_ontology.get_definition()
        self.data = facet_ontology.get_data()

        self.exhibit_data = {}

        # grab data for each facet
        num_facets = len(self.definition['facets'])
        count = 0

        facet_to_uri = {}
        for facetURI in self.definition['facets']:
            count += 1

            label = self.definition['facets'][facetURI]['label']
            facet = label 
            facet.replace(" ","")

            facet_to_uri[facet] = facetURI

            #TODO support sparql endpoints

            # rdfsources have already been read into the self.data graph
            selects = ["first", "label"]

            current = "first"

            patterns = ["?first <"+self.rdf+"type> <"+self.definition['facets'][ self.definition['first_order_facet'] ]['class']+">"]

            if self.definition["first_order_facet"] == str(facet):
                # this is the first order facet
                patterns.append("?first <"+self.definition['facets'][facetURI]["labeluri"]+"> ?label")
            else:
                # this facet is a ConnectedFacet


                # TODO support properties

#                selects.append("item")
                patterns.append("?"+current+" <"+self.rdf+"type> <"+self.definition['facets'][facetURI]['class']+">")
                patterns.append("?"+current+" <"+self.definition['facets'][facetURI]["labeluri"]+"> ?label")

            query = "SELECT DISTINCT "
            for select in selects:
                query += "?"+select+" "

            query += "WHERE {"
            query += " . ".join(patterns)
            query += "}"
           
            print "Querying facet "+str(count)+"/"+str(num_facets)
            print "Query: "+query

            for binding in self.data.query(query):
                first = binding[0]
                label = binding[1]

#                if self.definition["first_order_facet"] != str(facet):
#                    # FIXME? not used for anything, only the label is used
#                    item = binding[2]

                if not(first in self.exhibit_data):
                    self.exhibit_data[first] = {}

                if not(facet in self.exhibit_data[first]):
                    self.exhibit_data[first][facet] = {}

                if self.definition["first_order_facet"] == str(facetURI):
                    if not("label" in self.exhibit_data[first]):
                        self.exhibit_data[first]["label"] = {}
                    self.exhibit_data[first]["label"][label] = True # set "label" to this if this is the first order facet

                if not("id" in self.exhibit_data[first]):
                    self.exhibit_data[first]["id"] = {}

                self.exhibit_data[first]["id"][first] = True # set "id" the item's URI

                self.exhibit_data[first][facet][label] = True

        # transform exhibit data
        self.exhibit_data_transformed = []
        facets_dict = {} # facets_dict.keys() => distinct list of facets for the index.html
        for uri in self.exhibit_data:
            out_row = {}
            row = self.exhibit_data[uri]
            for facet in row:
                facets_dict[facet] = True
                value_dict = row[facet]
                out_row[facet] = value_dict.keys()
            self.exhibit_data_transformed.append(out_row)

        # output data to data.js
        out_data = os.path.join(self.config['output'], "data.js")
        out_data_f = open(out_data, "w")
        json.dump({"items": self.exhibit_data_transformed}, out_data_f, indent=2)
        out_data_f.close()

        # set up the context for the index.html template
        context = {"title": "Faceted Browser", "facets": []}
        for facet in facets_dict.keys():
            if facet != "label" and facet != "id":
                facet_entry = {
                    "label": self.definition['facets'][facet_to_uri[facet]]['label'],
                    "expression": facet,
                }
                context['facets'].append(facet_entry)

        # read in template
        index_templ = open(os.path.join("exhibit_template","index.html"), "r")
        index_src = "".join(index_templ.readlines())
        index_templ.close()

        # write out template
        index_out = open(os.path.join(self.config['output'], "index.html"), "w")
        index_out.write(pystache.render(index_src, context))
        index_out.close()

