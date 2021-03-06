import numpy as np
import networkx as nx
import doctest
from .makeGridGraph import make_grid_graph


def makeImageGraph(morph):
    """
    Construct a graph for an input image.

    Args:
        morph (ND array): The microstructure, an `(n_x, n_y, nz)`
            shaped array where `n_x, n_y and n_z` are the spatial dimensions.

    """
    G = make_grid_graph(morph.shape)
    vertex_colors = morph.flatten()
    mapping = {(i): vertex_colors[i] for i in range(len(vertex_colors))}
    nx.set_node_attributes(G, mapping, name="color")
    return G


def count_of_vertices(G, phase):
    """Count the number of vertices for a given phase.

    Args:
        G: The network representing the input microstructure.
        phase : The identifier of the phase of interest.

    Test to see if the graph is built with the correct number of
    vertices.

    >>> data = np.array([[0,0,0],
    ...                  [1,1,1],
    ...                  [0,0,0]])
    >>> g = makeImageGraph(data)
    >>> assert(count_of_vertices(g, 0) == 6)
    >>> assert(count_of_vertices(g, 1) == 3)

    """
    phases = nx.get_node_attributes(G, "color")
    phase_list = list(phases.values())
    return phase_list.count(phase)


def node_phaseA(n, G):
    nodes = G.nodes
    return nodes[n]["color"] == 0


def node_phaseB(n, G):
    nodes = G.nodes
    return nodes[n]["color"] == 1


def makeInterfaceEdges(G):
    """
    Connect the vertices on the interface through an interface meta-vertex.

    Args:
        G: The network representing the input microstructure.

    Check if the interface is constructed correctly

    >>> data = np.array([[0,0,0],\
                [1,1,1],\
                [0,0,0]])
    >>> g = makeImageGraph(data)
    >>> g = makeInterfaceEdges(g)
    >>> assert(g.number_of_nodes() == 10)

    """
    interface = [
        (n, u)
        for n, u in G.edges()
        if (node_phaseA(n, G) and node_phaseB(u, G))
        or (node_phaseB(n, G) and node_phaseA(u, G))
    ]
    G.remove_edges_from(interface)
    G.add_node(-1, color="green")
    interface = np.unique(np.array(interface))
    interface_edges = [(x, -1) for x in interface]
    G.add_edges_from(interface_edges)
    return G


def makeConnectedComponents(G, phase):
    """Calculate the number of connected components for a phase of the
       microstructure.

    Args:
      G: The network representing the input microstructure.
      phase : The identifier of the phase of interest.

    A subgraph checking the number of connected components.

    >>> data = np.array([[0,0,0],\
                [1,1,1],\
                [0,0,0]])
    >>> g = makeImageGraph(data)
    >>> g = makeInterfaceEdges(g)
    >>> assert(makeConnectedComponents(g, 0) == 2)
    >>> assert(makeConnectedComponents(g, 1) == 1)

    """
    nodes = (node for node, data in G.nodes(data=True) if data.get("color") == phase)
    subgraph = G.subgraph(nodes)
    subgraph.nodes
    return nx.number_connected_components(subgraph)


def interfaceArea(G):
    """
    Calculate the interfacial area of the microstructure.

    Args:
        G: The network representing the input microstructure.

    Check that the interface area is correct

    >>> data = np.array([[0,0,0],\
                [1,1,1],\
                [0,0,0]])
    >>> g = makeImageGraph(data)
    >>> g = makeInterfaceEdges(g)
    >>> assert(interfaceArea(g) == (9, 6, 3))

    """
    nodes_0 = [
        neighbor for neighbor in G.neighbors(-1) if G.nodes[neighbor]["color"] == 0
    ]
    nodes_1 = [
        neighbor for neighbor in G.neighbors(-1) if G.nodes[neighbor]["color"] == 1
    ]
    return G.degree[-1], len(nodes_0), len(nodes_1)


def shortest_distances_all(G):
    """
    Calculate the shortest distances to the meta vertices.

    Args:
        G: The network representing the input microstructure.
       phase : The identifier of the phase of interest.

    Not a good test case.

    >>> data = np.array([[0,0,0],\
                [1,1,1],\
                [0,0,0]])
    >>> g = makeImageGraph(data)
    >>> g = makeInterfaceEdges(g)
    >>> assert(shortest_distances_all(g) == 2.0)

    """
    path = nx.single_source_shortest_path(G, -1)
    del path[-1]
    path_length = [len(p) for p in path.values()]
    # print(path_length)
    return sum(path_length) / len(path_length)


def shortest_distances_phase(G, phase):
    """
    Calculate the shortest distances to the meta vertices.

    Args:
        G: The network representing the input microstructure.
    phase : The identifier of the phase of interest.

    Example
    >>> data = np.array([[0,0,0],\
                [1,1,1],\
                [0,0,0]])
    >>> g = makeImageGraph(data)
    >>> g = makeInterfaceEdges(g)
    >>> assert(shortest_distances_phase(g, 0) == 2.0)
    >>> assert(shortest_distances_phase(g, 1) == 2.0)
    """
    source = [node for node, data in G.nodes(data=True) if data.get("color") == phase]
    path = [
        nx.shortest_path(G, s, target=-1, weight=None, method="dijkstra")
        for s in source
    ]
    path_length = [len(p) for p in path]
    return sum(path_length) / len(path_length)


def shortest_dist_boundary(G, phase):
    path = nx.single_source_shortest_path(g, -1)
    path_length = [len(p) for p in path.values()]
    return sum(path_length) / len(path_length)


def tortuosity(G, phase):
    return None


def interface_boundary(G, phase):
    return None


def getGraspiDescriptors(data):
    """
    Calculate the graph descriptors for a segmented microstructure image.

    Args:
        data (ND array): The microstructure, an `(n_x, n_y, nz)`
            shaped array where `n_x, n_y and n_z` are the spatial dimensions.

    Example
    """
    g = makeImageGraph(data)
    g = makeInterfaceEdges(g)
    [interface_area, phase_0_interface, phase_1_interface] = interfaceArea(g)

    return dict(
        phase_0_count=count_of_vertices(g, 0),
        phase_1_count=count_of_vertices(g, 1),
        phase_0_cc=makeConnectedComponents(g, 0),
        phase_1_cc=makeConnectedComponents(g, 1),
        interfacial_area=interface_area,
        phase_0_interface=phase_0_interface,
        phase_1_interface=phase_1_interface,
        distance_to_interface=shortest_distances_all(g),
        distance_to_interface_0=shortest_distances_phase(g, 0),
        distance_to_interface_1=shortest_distances_phase(g, 1),
    )
