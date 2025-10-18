# src/wd_truthy_edges.py
from __future__ import annotations
from kg.wd.utils import run_sparql

def truthy_edges(qid: str) -> list[tuple[str, str]]:
    """
    Devuelve pares (P, Q) de claims truthy donde el objeto es IRI (no literal).
    """
    q = f"""
    SELECT ?p ?o WHERE {{
      VALUES ?s {{ wd:{qid} }}
      ?s ?prop ?o .
      ?prop wikibase:directClaim ?p .
      FILTER(isIRI(?o))
    }}
    """
    res = run_sparql(q)
    edges = []
    for b in res["results"]["bindings"]:
        P = b["p"]["value"].split("/")[-1]
        O = b["o"]["value"].split("/")[-1]
        edges.append((P, O))
    return edges
