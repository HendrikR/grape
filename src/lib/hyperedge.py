from lib.config import Config

class Hyperedge(object):
    """ Hyperedge class"""
    def __init__(self, id, adj):
        self.id = id
        self.adj = adj

        config = Config()
        self.title = str(id)
        graph_type = config.get("graph", "type")
        self.directed = graph_type in ['DiGraph', 'MultiDiGraph']
        self.color = config.get("edge", "color")
        self.width = float(config.get("edge", "width"))
        self.selected = False
        self.checked = False

        for vertex in adj:
            vertex.touching_edges.append(self)
            if not vertex.has_edge(self):
                vertex.add_edge(self)

    def __str__(self):
        """Print a formated edge"""
        value = self.title + " " + str(self.start)
        if self.directed:
            value += " -> "
        else:
            value += " -- "
        value += str(self.end)
        return value

    def select(self):
        self.selected = True

    def deselect(self):
        self.selected = False

    def check(self):
        self.checked = True

    def uncheck(self):
        self.checked = False

    def touches(self, vertex):
        for v in adj:
            if v == vertex: return True

    def to_graphml(self): # TODO
        return ('    <edge id="'+ str(self.id) +'" source="'+ str(self.start.id) +'" target="'+ str(self.end.id) +'">\n'
                '      <data key="label">' + self.title + '</data>\n'
                '      <data key="directed">' + str(self.directed) + '</data>\n'
                '      <data key="color">' + self.color + '</data>\n'
                '      <data key="width">' + str(self.width) + '</data>\n'
                '    </node>\n')


    def to_enforce(self): # TODO
        return str(self.id) +':'+ str(self.start.id) +'-'+ self.title +'->'+ str(self.end.id) +'\n'

    def to_dot(self): # TODO
        return '  '+ str(self.start.id) +' -> '+ str(self.end.id) +' [label="'+ self.title + '"]\n'
