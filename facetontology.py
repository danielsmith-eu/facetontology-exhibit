
class FacetOntology:
    """ Parses FacetOntology definitions. """

    def __init__(self):
        self.definition_url = None

    def load_definition(self, url):
        """ Load a definition from a URL. """
        self.definition_url = url
        self.definition = {}


class Exhibit:
    """ Generates Exhibits. """

    def __init__(self, config):
        self.config = config

    def generate(self, facet_ontology):
        """ Generate the Exhibit, using this Facet Ontology definition. """
        self.facet_ontology = facet_ontology




