import matplotlib.pyplot as plt
import networkx as nx
from rdflib import Graph, URIRef, Namespace

WDT = Namespace("http://www.wikidata.org/prop/direct/")

def plot_graph(ttl_path, root_qid=None, max_edges=30, figsize=(12, 9)):
    """
    Dibuja un grafo RDF grado-1 (formato .ttl) usando networkx y matplotlib.

    Parameters
    ----------
    ttl_path : str
        Ruta al archivo .ttl del grafo.
    root_qid : str, optional
        Si se pasa, se centra el dibujo en este nodo (ej. 'Q2685').
    max_edges : int
        Número máximo de aristas a visualizar (para no saturar el gráfico).
    figsize : tuple
        Tamaño del gráfico en pulgadas.

    Returns
    -------
    None
    """
    g = Graph()
    g.parse(ttl_path, format="turtle")

    # Crear grafo NetworkX
    G = nx.DiGraph()

    for s, p, o in g.triples((None, None, None)):
        if isinstance(s, URIRef) and isinstance(o, URIRef):
            if str(p).startswith(str(WDT)):
                G.add_edge(str(s), str(o), label=str(p))

    if len(G.edges) == 0:
        raise ValueError("No se encontraron aristas wdt: en el grafo.")

    # limitar cantidad
    edges = list(G.edges)[:max_edges]
    H = G.edge_subgraph(edges).copy()

    # Layout
    pos = nx.spring_layout(H, k=0.6, seed=42)
    plt.figure(figsize=figsize)
    nx.draw(
        H, pos,
        with_labels=False,
        node_color="#a0cbe2",
        edge_color="#333333",
        node_size=400,
        arrowsize=15,
    )

    # Etiquetas simples
    node_labels = {n: n.split("/")[-1] for n in H.nodes()}
    nx.draw_networkx_labels(H, pos, node_labels, font_size=9)

    plt.title(f"Grafo RDF ({len(H.nodes())} nodos, {len(H.edges())} aristas)")
    plt.axis("off")
    plt.show()
