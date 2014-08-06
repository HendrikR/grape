from lib.config import Config

class Edge(object):
    """ Edge class"""
    def __init__(self, id, start, end):
        self.id = id
        self.start = start
        self.end = end

        config = Config()
        self.title = str(id)
        graph_type = config.get("graph", "type")
        self.directed = graph_type in ['DiGraph', 'MultiDiGraph']
        self.color = config.get("edge", "color")
        self.width = float(config.get("edge", "width"))

        start.touching_edges.append(self)
        end.touching_edges.append(self)

        self.selected = False
        self.checked = False
        start.add_edge(self)

        if not self.directed:
            end.add_edge(self)

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
        return vertex == self.start or vertex == self.end

    def to_graphml(self):
        return ('    <edge id="'+ str(self.id) +'" source="'+ str(self.start.id) +'" target="'+ str(self.end.id) +'">\n'
                '      <data key="label">' + self.title + '</data>\n'
                '      <data key="directed">' + str(self.directed) + '</data>\n'
                '      <data key="color">' + self.color + '</data>\n'
                '      <data key="width">' + str(self.width) + '</data>\n'
                '    </node>\n')


    def to_enforce(self):
        return str(self.id) +":"+ str(self.start.id) +"-"+ self.title +"->"+ str(self.end.id) +"\n"

    def to_dot(self):
        return "  "+ str(self.start.id) +" -> "+ str(self.end.id) +" [label=\""+ self.title + "\"]\n"
