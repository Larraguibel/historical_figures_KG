import textwrap
import matplotlib.pyplot as plt
import networkx as nx
from rdflib import Graph, URIRef, Namespace, RDFS

WDT = Namespace("http://www.wikidata.org/prop/direct/")

def _qid(uri: str) -> str:
    return uri.rsplit("/", 1)[-1]

def _pid(uri: str) -> str:
    return uri.rsplit("/", 1)[-1]

def plot_graph_degree1_labeled(ttl_path, max_edges=40, figsize=(13, 10), wrap_width=18, fetch_missing_labels=True):
    """
    Dibuja un grafo RDF grado-1 mostrando nombres de entidades y propiedades.
    - Divide etiquetas largas (wrap_width)
    - Desplaza texto de los nodos hacia abajo para mejorar legibilidad.
    """
    g = Graph()
    g.parse(ttl_path, format="turtle")

    # --- Construcción del grafo ---
    G = nx.DiGraph()
    node_labels = {}
    for s, p, o in g.triples((None, None, None)):
        if isinstance(s, URIRef) and isinstance(o, URIRef):
            for n in (s, o):
                lab = g.value(n, RDFS.label)
                if lab:
                    node_labels[str(n)] = str(lab)
            if str(p).startswith(str(WDT)):
                G.add_edge(str(s), str(o), pid=_pid(str(p)))

    if not G.edges:
        raise ValueError("No se encontraron aristas 'wdt:' en el grafo.")

    edges = list(G.edges(data=True))[:max_edges]
    H = nx.DiGraph()
    for u, v, d in edges:
        H.add_edge(u, v, **d)

    # --- Etiquetas ---
    final_node_labels = {
        n: "\n".join(textwrap.wrap(node_labels.get(n, _qid(n)), width=wrap_width))
        for n in H.nodes()
    }

    # Si faltan labels de propiedades
    pids = {d["pid"] for _, _, d in H.edges(data=True)}
    try:
        from SPARQLWrapper import SPARQLWrapper, JSON
        values = " ".join(f"wd:{p}" for p in pids)
        query = f"""
        SELECT ?p ?pLabel WHERE {{
          VALUES ?p {{ {values} }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "es,en". }}
        }}
        """
        sp = SPARQLWrapper("https://query.wikidata.org/sparql")
        sp.setReturnFormat(JSON)
        sp.setQuery(query)
        result = sp.query().convert()
        pid_labels = {
            b["p"]["value"].split("/")[-1]: b["pLabel"]["value"]
            for b in result["results"]["bindings"]
        }
    except Exception:
        pid_labels = {p: p for p in pids}

    edge_labels = {(u, v): pid_labels.get(d["pid"], d["pid"]) for u, v, d in H.edges(data=True)}

    # --- Dibujo ---
    pos = nx.spring_layout(H, k=0.7, seed=42)
    plt.figure(figsize=figsize)
    nx.draw(
        H, pos,
        with_labels=False,
        node_color="#a0cbe2",
        edge_color="#333333",
        node_size=600,
        arrowsize=18,
    )

    # Mover texto un poco hacia abajo (ajuste vertical)
    label_pos = {k: (x, y - 0.05) for k, (x, y) in pos.items()}
    nx.draw_networkx_labels(H, label_pos, final_node_labels, font_size=9)

    nx.draw_networkx_edge_labels(H, pos, edge_labels=edge_labels, font_size=8)
    plt.title(f"Grafo RDF (nodos={H.number_of_nodes()}, aristas={H.number_of_edges()})", fontsize=12)
    plt.axis("off")
    plt.show()
