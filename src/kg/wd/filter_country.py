from __future__ import annotations
from typing import Iterable, Set
import re
from kg.wd.utils import run_sparql

_QID_RE = re.compile(r"^Q\d+$")

def _only_qids(qids: Iterable[str]) -> list[str]:
    return [q for q in qids if q and _QID_RE.match(q)]

def _values_block(qids: list[str]) -> str:
    return " ".join(f"wd:{q}" for q in qids)

def _select_o(query_core: str) -> Set[str]:
    res = run_sparql(query_core)
    out: Set[str] = set()
    for b in res["results"]["bindings"]:
        out.add(b["o"]["value"].split("/")[-1])
    return out

def filter_by_country(qids: Iterable[str],
                      country_qid: str,
                      batch_p1: int = 40,   # P27/P17 directos (rápido)
                      batch_p2: int = 10,   # P131 a ≤3 saltos (medio)
                      batch_p3: int = 8     # P159/P276 (lento)
                      ) -> Set[str]:
    """
    Devuelve los QIDs del conjunto de entrada que están relacionados con el país dado,
    en 3 pasadas:
      1) Directo: P27 = country_qid  (nacionalidad)  o  P17 = country_qid  (país)
      2) Vía P131 hasta 3 saltos (sin usar '*')
      3) P159 (HQ) o P276 (situado en) con lugar en el país (directo o vía P131 1-2 saltos)

    Parámetros:
      - qids: iterable de QIDs candidatos (solo se consideran Q\\d+)
      - country_qid: QID del país objetivo (ej. 'Q30' EE. UU., 'Q183' Alemania)
      - batch_p1/p2/p3: tamaños de lote por pasada para evitar timeouts en WDQS
    """
    if not _QID_RE.match(country_qid):
        raise ValueError(f"country_qid inválido: {country_qid!r} (se espera 'Q\\d+')")

    qids = list(dict.fromkeys(_only_qids(qids)))
    ok: Set[str] = set()

    # PASO 1 — rápido (P27/P17)
    for i in range(0, len(qids), batch_p1):
        chunk = qids[i:i+batch_p1]
        if not chunk:
            continue
        vals = _values_block(chunk)
        q1 = f"""
        SELECT DISTINCT ?o WHERE {{
          VALUES ?o {{ {vals} }}
          {{ ?o wdt:P27 wd:{country_qid} . }} UNION {{ ?o wdt:P17 wd:{country_qid} . }}
        }}
        """
        ok1 = _select_o(q1)
        ok |= ok1

    rem1 = [q for q in qids if q not in ok]
    if not rem1:
        return ok

    # PASO 2 — medio (P131 sin '*', hasta 3 saltos)
    for i in range(0, len(rem1), batch_p2):
        chunk = rem1[i:i+batch_p2]
        if not chunk:
            continue
        vals = _values_block(chunk)
        q2 = f"""
        SELECT DISTINCT ?o WHERE {{
          VALUES ?o {{ {vals} }}
          {{
            ?o wdt:P131 ?a1 . ?a1 wdt:P17 wd:{country_qid} .
          }} UNION {{
            ?o wdt:P131 ?a1 . ?a1 wdt:P131 ?a2 . ?a2 wdt:P17 wd:{country_qid} .
          }} UNION {{
            ?o wdt:P131 ?a1 . ?a1 wdt:P131 ?a2 . ?a2 wdt:P131 ?a3 . ?a3 wdt:P17 wd:{country_qid} .
          }}
        }}
        """
        ok2 = _select_o(q2)
        ok |= ok2

    rem2 = [q for q in rem1 if q not in ok]
    if not rem2:
        return ok

    # PASO 3 — lento (P159/P276) con lugar en el país directo o vía P131 1–2 saltos
    for i in range(0, len(rem2), batch_p3):
        chunk = rem2[i:i+batch_p3]
        if not chunk:
            continue
        vals = _values_block(chunk)
        q3 = f"""
        SELECT DISTINCT ?o WHERE {{
          VALUES ?o {{ {vals} }}
          {{
            ?o wdt:P159 ?hq .
            {{ ?hq wdt:P17 wd:{country_qid} . }}
            UNION
            {{ ?hq wdt:P131 ?b1 . ?b1 wdt:P17 wd:{country_qid} . }}
            UNION
            {{ ?hq wdt:P131 ?b1 . ?b1 wdt:P131 ?b2 . ?b2 wdt:P17 wd:{country_qid} . }}
          }}
          UNION
          {{
            ?o wdt:P276 ?place .
            {{ ?place wdt:P17 wd:{country_qid} . }}
            UNION
            {{ ?place wdt:P131 ?c1 . ?c1 wdt:P17 wd:{country_qid} . }}
            UNION
            {{ ?place wdt:P131 ?c1 . ?c1 wdt:P131 ?c2 . ?c2 wdt:P17 wd:{country_qid} . }}
          }}
        }}
        """
        ok3 = _select_o(q3)
        ok |= ok3

    return ok
