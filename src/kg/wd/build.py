# src/build_graph_wd.py
from __future__ import annotations
from pathlib import Path
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, XSD

WD = Namespace("http://www.wikidata.org/entity/")
WDT = Namespace("http://www.wikidata.org/prop/direct/")

def build_degree1_graph(root_qid: str, edges: list[tuple[str,str]], labels: dict[str,str] | None = None) -> Graph:
    """
    Construye un grafo con aristas (root) -[P]-> (Q), grado-1.
    """
    g = Graph()
    g.bind("wd", WD)
    g.bind("wdt", WDT)
    g.bind("rdfs", RDFS)

    s = WD[root_qid]
    # Agrega label opcional al sujeto
    if labels and root_qid in labels:
        g.add((s, RDFS.label, Literal(labels[root_qid], datatype=XSD.string)))

    for P, Q in edges:
        p = WDT[P]       # propiedad truthy directa
        o = WD[Q]
        g.add((s, p, o))
        # labels opcionales para objetos
        if labels and Q in labels:
            g.add((o, RDFS.label, Literal(labels[Q], datatype=XSD.string)))
    return g

def save_ttl(g: Graph, out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    g.serialize(destination=str(out_path), format="turtle")
