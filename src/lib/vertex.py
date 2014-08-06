from lib.config import Config

class Vertex(object):

    def __init__(self, id, position):
        self.id = id
        self.position = position

        self.edge_list = set()
        self.vertex_list = set()

        config = Config()

        self.title = str(id)
        self.fill_color = config.get("vertex", "fill-color")
        self.border_color = config.get("vertex", "border-color")
        self.border_size = float(config.get("vertex", "border-size"))
        self.size = float(config.get("vertex", "size"))
        self.font_size = float(config.get("vertex", "font-size"))

        self.selected = False
        self.checked = False
        self.touching_edges = []

    def __str__(self):
        return self.title

    def select(self):
        self.selected = True

    def deselect(self):
        self.selected = False

    def check(self):
        self.checked = True

    def uncheck(self):
        self.checked = False
        
    def has_edge(self, edge):
        return edge in self.edge_list

    def touches_edge(self, edge):
        return edge in self.touching_edges

    def add_edge(self, edge):
        self.edge_list.add(edge)
        if edge.start == self:
            self.vertex_list.add(edge.end)
        else:
            self.vertex_list.add(edge.start)

    def remove_edge(self, edge):
        if self.has_edge(edge):
            if edge.start.touches_edge(edge):
                edge.start.touching_edges.remove(edge)
            if edge.end.touches_edge(edge):
                edge.end.touching_edges.remove(edge)
            if edge.start in self.vertex_list:
                self.vertex_list.remove(edge.start)
            if edge.end in self.vertex_list:
                self.vertex_list.remove(edge.end)

            self.edge_list.remove(edge)
            del edge

    def clear_edge_list(self):
        for e in self.edge_list:
            start = e.start
            end = e.end
            if start != self:
                start.remove_edge(e)
            if end != self:
                end.remove_edge(e)

        del self.edge_list[:]

    def nearest_vertices(self, neighbor, axis):
        next_vertex = None

        if len(neighbor) > 0:
            point_max = self.position[axis]
            point_min = self.position[axis]

            while not next_vertex:
                for current in neighbor:
                    if current.position[axis] == point_max:
                        next_vertex = current
                        break
                    elif current.position[axis] == point_min:
                        next_vertex = current
                        break

                point_max = point_max + 1
                point_min = point_min - 1
        return next_vertex

    def to_graphml(self):
        return ('    <node id="' + str(self.id) + '">\n'
                '      <data key="label">' + self.title + '</data>\n'
                '      <data key="fill_color">' + self.fill_color + '</data>\n'
                '      <data key="border_color">' + self.border_color + '</data>\n'
                '      <data key="size">' + str(self.size) + '</data>\n'
                '      <data key="font_size">' + str(self.font_size) + '</data>\n'
                '      <data key="positionx">' + str(self.position[0]) + '</data>\n'
                '      <data key="positiony">' + str(self.position[1]) + '</data>\n'
                '    </node>\n')

    def to_enforce(self):
    	return '(' + str(self.id) + ':' + self.title + ')\n'

    def to_dot(self):
        return ('  '+ str(self.id) +' ['
                'label="' + self.title +'", '
                'color="' + self.fill_color +'"]\n')
