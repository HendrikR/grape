import gzip
import base64
import pickle
import os

from lib.config import Config
from lib.vertex import Vertex
from lib.edge import Edge
from lib.hyperedge import Hyperedge

import re
import random
import math

class Graph(object):
    def __init__(self, title=""):
#       Cant stay here, cause splode stack in pickle dump
#        self.config = Config()

        self.vertex_id = 0
        self.edge_id = 0
        self.hyperedge_id = 0
        self.vertices = []
        self.edges = []
        self.hyperedges = []
        self.title = title
        self.selected_vertices_cache = None
        self.path = None

        config = Config()
        if not title:
            self.title = config.get("graph", "title")
        self.type = config.get("graph", "type")

        self.directed = self.type in ['DiGraph', 'MultiDiGraph' ]
        self.multiple = self.type in ['MultiGraph', 'MultiDiGraph']

        self.background_color = config.get("graph", "background-color")

    def __str__(self):
        """Prints all verticies and your adjacncies lists"""
        value = ""
        for v in self.vertices:
            value += str(v) + ": "
            for n in v.vertex_list:
                value += str(n) + " "
            value += "\n"
        return value

    def find_in_area(self, x, y, w, h):
        vertices = []
        for v in self.vertices:
            vx = v.position[0]
            vy = v.position[1]
            def in_range(position, p, r):
                if r > 0:
                    return (position >= p and position <= (p + r))
                else:
                    return (position <= p and position >= (p + r))
            in_x = in_range(vx, x, w)
            in_y = in_range(vy, y, h)
            if in_x and in_y:
                vertices.append(v)
        return vertices

    def find_by_position(self, position):
        current_x = position[0]
        current_y = position[1]
        for v in self.vertices:
            r = v.size / 2
            x = v.position[0]
            y = v.position[1]
            if (x - r) <= current_x and (x + r) >= current_x:
                if (y - r) <= current_y and (y + r) >= current_y:
                    return v
        return None

    def find(self, id, what="vertex"):
        array = None
        
        if what == "vertex":
            array = self.vertices
        elif what == "edge":
            array = self.edges
        elif what == "hyperedge":
            array = self.hyperedges
        else:
            return None

        lo = 0
        hi = len(array)
        while lo < hi:
            mid = (lo + hi) // 2
            midval = array[mid].id

            if midval < id:
                lo = mid + 1
            elif midval > id:
                hi = mid
            else:
                return array[mid]
        return None

    def find_edge(self, start, end):
        edges = []
        for e in self.edges:
            if e.start == start and e.end == end:
                edges.append(e)
            elif not e.directed and e.start == end and e.end == start:
                edges.append(e)
        return edges

    def find_edge_from_vertex(self, vertex, id):
        for edge in vertex.edge_list:
            if int(id) == edge.id:
                return edge
        return None

    def selected_vertices(self):
        if self.selected_vertices_cache:
            return self.selected_vertices_cache
        selected = []
        for v in self.vertices:
            if v.selected:
                selected.append(v)
        return selected

    def has_edge(self, edge):
        return edge in self.edges

    def has_hyperedge(self, hyperedge):
        return hyperedge in self.hyperedges

    # TODO - Header

    def open(self, name):
        graph = None
        if   name.lower().endswith('.cgf'):
            graph = self.open_native(name)
        elif name.lower().endswith('.jsg'):
            graph = self.open_jsg(name)
        else:
            print("nooope, can't open that.")
        if graph != None:
            graph.path = name
            self.init_layout()
        return graph

        
    def open_native(self, name):
        f = open(name, 'rb')
        encoded = f.read()
        compressed = base64.b64decode(encoded)
        data = gzip.zlib.decompress(compressed)
        graph = pickle.loads(data)
        f.close()
        return graph


    def typecolor(self, nodetype):
        val = hash(nodetype)
        r = "%02x" % ((val >>  8) & 0xFF)
        g = "%02x" % ((val >> 16) & 0xFF)
        b = "%02x" % ((val >> 24) & 0xFF)
        return "#" + r + g + b

    def open_jsg(self, name):
        print("opening " + name)
        self.title="jsg"
        f = open(name, 'r')
        fline = 0
        all_edges = {}
        for line in f.readlines():
            fline += 1
            if (fline == 1): # ignore that first line with the typing for now
                continue
            m = re.match('^\["([^"]*)",([0-9]*),\[(|\[.*\])\],\[(|\[.*\])\]\]$', line.rstrip('\n'))
            nodetype  = m.group(1)
            nodeid    = int(m.group(2))
            nodeprops = m.group(3)
            nodeedges = m.group(4)
            nodeprops = re.findall('\["([^"]*)",([^[\]]*)\]', nodeprops)
            
            vertex = Vertex(nodeid, [0,0])
            self.vertices.append(vertex)
            setattr(vertex, "user_nodetype", nodetype)
            for (key,val) in nodeprops:
                setattr(vertex, "user_" + key.lower(), val)
            vertex.border_color = self.typecolor(nodetype)
            vertex.title = str(nodeid) +":"+ nodetype

            all_edges[nodeid] = re.findall('\["([^\"]*)",([0-9, ]*)\]', nodeedges)
        # the vertices have to be sorted by id to find them
        self.vertices.sort(key=lambda v : v.id)
        self.vertex_id = self.vertices[-1].id+1

        for src_id,edgetypes in all_edges.iteritems():
            for (etype,edges) in edgetypes:
                for tgt_id in edges.split(','):
                    src_v = self.find(int(src_id))
                    tgt_v = self.find(int(tgt_id))
                    self.add_edge(src_v, tgt_v)
        
        self.init_layout()
        return self

    def save(self, name):
        if not name.endswith('.cgf'):
            name += '.cgf'
        self.path = name
        self.title = os.path.basename(name)
        f = open(name, 'wb')
        data = pickle.dumps(self)
        compress = gzip.zlib.compress(data)
        encoded = base64.b64encode(compress)
        f.write(encoded)
        f.close()

    def layout_graph(self, steps):
        for i in xrange(0, steps):
            self.calc_layout()
        #self.scale_to_region()

    def init_layout(self):
        self.layout_step = 0
        self.layout_X0    = 20
        self.layout_Y0    = 20
        self.layout_WIDTH = 800
        self.layout_HEIGHT= 400
        for v in self.vertices:
            v.position = [random.randrange(20,self.layout_WIDTH -20),
                          random.randrange(20,self.layout_HEIGHT-20)]
            v.velocity = (0,0)

    def calc_layout(self):
        # init constants
        k = min(self.layout_WIDTH, self.layout_HEIGHT) / 3 * 2
        C = math.log(self.layout_step + 2) * 100

        # calculate repelling force between nodes:
        for v1 in self.vertices:
            v1.velocity = (0,0)
            for v2 in self.vertices:
                dx = v1.position[0] - v2.position[0]
                dy = v1.position[1] - v2.position[1]
                #dist = math.pow(dx*dx + dy*dy, 0.5) # Euclidian distance
                dist = abs(dx)+abs(dy) # Manhattan distance
                if (dist < 0.0001):
                    continue
                mul = (k*k) / (dist*dist*C)
                v1.position[0] += dx * mul
                v1.position[1] += dy * mul
                
        # calculate attracting forces along edges:
        for e in self.edges:
            psrc = e.start.position
            ptgt = e.end.position
            dx = psrc[0] - ptgt[0]
            dy = psrc[1] - ptgt[1]
            #dist = math.pow(dx*dx + dy*dy, 0.5) # Euclidian distance
            dist = abs(dx)+abs(dy) # Manhattan distance
            if (dist < 0.0001):
                continue
            mul = (dist*dist) / (k*k*C)
            v1.position[0] += dx * mul
            v1.position[1] += dy * mul
                
    def scale_to_region(self):
        minx = self.layout_X0 + self.layout_WIDTH
        miny = self.layout_Y0 + self.layout_HEIGHT
        maxx = self.layout_X0
        maxy = self.layout_Y0
        for v in self.vertices:
            nodex = v.position[0]
            nodey = v.position[1]
            minx = nodex if nodex < minx else minx
            miny = nodey if nodey < miny else miny
            maxx = nodex if nodex > maxx else maxx
            maxy = nodey if nodey > maxy else maxy
        print("scaling from (" + str(minx) +","+str(miny)+") , ("+str(maxx)+","+str(maxy)+")")
        xscale = self.layout_WIDTH  / (maxx - minx)
        yscale = self.layout_HEIGHT / (maxy - miny)
        xshift = self.layout_X0
        yshift = self.layout_Y0
        print("scaling by *(" + str(xscale) +","+str(yscale)+") +("+str(xshift)+","+str(yshift)+")")
        for v in self.vertices:
            v.position[0] = xshift + xscale*(nodex-minx)
            v.position[1] = yshift + yscale*(nodey-miny)

    def add_vertex(self, position):
        vertex = Vertex(self.vertex_id, position)
        self.vertices.append(vertex)
        self.vertex_id += 1

        return vertex

    def remove_vertex(self, vertex):
        if vertex:
            to_be_removed = list(vertex.touching_edges)
            list(map(lambda e: self.remove_edge(e), to_be_removed))
            self.vertices.remove(vertex)

    def add_edge(self, start, end):
        digraph = self.directed and not end in start.vertex_list
        graph = not self.directed and not end in start.vertex_list and not start in end.vertex_list

        edge = None
        if (self.multiple) or digraph or graph:
            edge = Edge(self.edge_id, start, end)
            self.edges.append(edge)
            self.edge_id += 1

        return edge

    def remove_edge(self, edge):
        if not self.has_edge(edge):
            return
        # TODO - Figure out how to handle multiple edges
        edge.start.remove_edge(edge)
        if not edge.directed:
            edge.end.remove_edge(edge)
        self.edges.remove(edge)

    def toggle_vertex_selection(self, vertex):
        self.selected_vertices_cache = None

        if vertex.selected:
            vertex.deselect()
        else:
            vertex.select()

    def select_all(self):
        self.selected_vertices_cache = None
        for vertex in self.vertices:
            vertex.select()

    def deselect_all(self):
        if len(self.selected_vertices()) > 0:
            selected_vertices = self.selected_vertices()
            for vertex in selected_vertices:
                self.deselect_vertex(vertex)

    def select_vertex(self, vertex):
        self.selected_vertices_cache = None
        vertex.select()

    def deselect_vertex(self, vertex):
        self.selected_vertices_cache = None
        vertex.deselect()

    def move_selection(self, direction):
        selected = self.selected_vertices()

        if len(selected) == 1:
            if direction == 'up':
                sort_index = 1
                slice = lambda arr, index: arr[:index - 1]
            elif direction == 'down':
                sort_index = 1
                slice = lambda arr, index: arr[index + 1:]
            elif direction == 'left':
                sort_index = 0
                slice = lambda arr, index: arr[:index - 1]
            elif direction == 'right':
                sort_index = 0
                slice = lambda arr, index: arr[index + 1:]
            else:
                return None

            ordered = sorted(self.vertices, key=lambda vertex: vertex.position[sort_index])
            index = ordered.index(selected[0])
            ordered = slice(ordered, index)

            vertex = selected[0].nearest_vertices(ordered, int(not sort_index))

            if vertex:
                self.deselect_vertex(selected[0])
                self.select_vertex(vertex)

    def graph_to_networkx(self):
        g = None

        print(self.type)
        if self.type == 'Graph':
            g = nx.Graph(title=self.title)
        elif self.type == 'DiGraph':
            g = nx.DiGraph(title=self.title)
        elif self.type == 'MultiGraph':
            g = nx.MultiGraph(title=self.title)
        elif self.type == 'MultiDiGraph':
            g = nx.MultiDiGraph(title=self.title)

        if g == None:
            return

        for v in self.vertices:
            g.add_node(v.id, id=v.id)

            for attr in v.__dict__:
                if attr.startswith("user_"):
                    t_identifier = attr[5:]
                    t_value = getattr(self.vertex, attr)
                    self.liststore_properties.append([t_identifier, t_value])
                    g.node[v.id][t_identifier] = t_value

        for e in self.edges:
            g.add_edge(e.start.id, e.end.id, id=e.id)
            for attr in e.__dict__:
                if attr.startswith("user_"):
                    t_identifier = attr[5:]
                    t_value = getattr(self.vertex, attr)
                    self.liststore_properties.append([t_identifier, t_value])
                    for s in g[e.start.id][e.end.id]:
                        if g[e.start.id][e.end.id][s]['id'] == e.id:
                            g[e.start.id][e.end.id][s][t_identifier] = t_value

        print(g.nodes(data=True))
        print(g.edges(data=True))
        return g

    def to_graphml(self):
        str = '<graph id="'+ self.title +'" edgedefault="directed">'
        for v in self.vertices:
            str += v.to_graphml()
        for v in self.edges:
            str += v.to_graphml()
        str += '</graph>\n'
        return str

    def to_enforce(self):
        str = ''
        for v in self.vertices:
            str += v.to_enforce()
        for v in self.edges:
            str += v.to_enforce()
        return str
    
    def to_dot(self):
        str = 'digraph '+ self.title +' {\n'
        for v in self.vertices:
            str += v.to_dot()
        for v in self.edges:
            str += v.to_dot()
        str += '}\n'
        return str
        
    def to_jsg(self):
        # TODO: Property types?
        str = '# {"name":"GRAPE_EXPORT","indexed":1,"undirected":0,"node_types":["T"],"edge_types":["E"],"property_types":[],"gravity_version":46}\n'
        for v in self.vertices:
            str += v.to_jsg()
        # Edges are handeled by the nodes
        return str
    
