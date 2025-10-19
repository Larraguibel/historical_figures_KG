# src/kg/wd/truthy.py
from __future__ import annotations
from kg.wd.utils import run_sparql

def truthy_edges(qid: str) -> list[tuple[str, str]]:
    """
    Devuelve pares (P, Q) de claims truthy donde el objeto es una ENTIDAD de Wikidata (Q...),
    no archivos/URLs/literales.
    P es el predicado directo wdt:Pxx, Q es el QID objeto.
    """
    q = f"""
    SELECT ?p ?o WHERE {{
      VALUES ?s {{ wd:{qid} }}
      ?s ?p ?o .
      ?prop wikibase:directClaim ?p .

      # Solo objetos IRI en el namespace de entidades Q de Wikidata
      FILTER(isIRI(?o))
      FILTER(STRSTARTS(STR(?o), "http://www.wikidata.org/entity/Q") ||
             STRSTARTS(STR(?o), "https://www.wikidata.org/entity/Q"))
    }}
    """
    res = run_sparql(q)
    edges = []
    for b in res["results"]["bindings"]:
        P = b["p"]["value"].split("/")[-1]   # wdt:Pxx -> "Pxx"
        O = b["o"]["value"].split("/")[-1]   # .../entity/Qxxxx -> "Qxxxx"
        edges.append((P, O))
    return edges
