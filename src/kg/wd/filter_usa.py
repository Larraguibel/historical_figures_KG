from __future__ import annotations
from typing import Iterable
import re
from kg.wd.utils import run_sparql

_QID_RE = re.compile(r"^Q\d+$")

def _only_qids(qids: Iterable[str]) -> list[str]:
    return [q for q in qids if q and _QID_RE.match(q)]

def _values_block(qids: list[str]) -> str:
    return " ".join(f"wd:{q}" for q in qids)

def _select_o(query_core: str) -> set[str]:
    res = run_sparql(query_core)
    out = set()
    for b in res["results"]["bindings"]:
        out.add(b["o"]["value"].split("/")[-1])
    return out

def filter_us(qids: Iterable[str],
              batch_p1: int = 40,   # P27/P17 directos (rápido)
              batch_p2: int = 10,   # P131 a ≤3 saltos (medio)
              batch_p3: int = 8     # P159/P276 (lento)
              ) -> set[str]:
    """
    Devuelve QIDs pertenecientes a EE.UU., en 3 pasadas:
      1) Directo: P27=Q30 o P17=Q30
      2) Vía P131 hasta 3 saltos (sin usar '*')
      3) HQ (P159) o situado en (P276) hacia lugar en EE.UU. (directo o vía hasta 2 saltos)
    """
    qids = list(dict.fromkeys(_only_qids(qids)))
    ok: set[str] = set()

    # PASO 1 — rápido
    for i in range(0, len(qids), batch_p1):
        chunk = qids[i:i+batch_p1]
        vals = _values_block(chunk)
        q1 = f"""
        SELECT DISTINCT ?o WHERE {{
          VALUES ?o {{ {vals} }}
          {{ ?o wdt:P27 wd:Q30 . }} UNION {{ ?o wdt:P17 wd:Q30 . }}
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
        vals = _values_block(chunk)
        q2 = f"""
        SELECT DISTINCT ?o WHERE {{
          VALUES ?o {{ {vals} }}
          {{
            ?o wdt:P131 ?a1 . ?a1 wdt:P17 wd:Q30 .
          }} UNION {{
            ?o wdt:P131 ?a1 . ?a1 wdt:P131 ?a2 . ?a2 wdt:P17 wd:Q30 .
          }} UNION {{
            ?o wdt:P131 ?a1 . ?a1 wdt:P131 ?a2 . ?a2 wdt:P131 ?a3 . ?a3 wdt:P17 wd:Q30 .
          }}
        }}
        """
        ok2 = _select_o(q2)
        ok |= ok2

    rem2 = [q for q in rem1 if q not in ok]
    if not rem2:
        return ok

    # PASO 3 — lento (P159/P276) con lugar en USA directo o vía P131 1–2 saltos
    for i in range(0, len(rem2), batch_p3):
        chunk = rem2[i:i+batch_p3]
        vals = _values_block(chunk)
        q3 = f"""
        SELECT DISTINCT ?o WHERE {{
          VALUES ?o {{ {vals} }}
          {{
            ?o wdt:P159 ?hq .
            {{ ?hq wdt:P17 wd:Q30 . }}
            UNION
            {{ ?hq wdt:P131 ?b1 . ?b1 wdt:P17 wd:Q30 . }}
            UNION
            {{ ?hq wdt:P131 ?b1 . ?b1 wdt:P131 ?b2 . ?b2 wdt:P17 wd:Q30 . }}
          }}
          UNION
          {{
            ?o wdt:P276 ?place .
            {{ ?place wdt:P17 wd:Q30 . }}
            UNION
            {{ ?place wdt:P131 ?c1 . ?c1 wdt:P17 wd:Q30 . }}
            UNION
            {{ ?place wdt:P131 ?c1 . ?c1 wdt:P131 ?c2 . ?c2 wdt:P17 wd:Q30 . }}
          }}
        }}
        """
        ok3 = _select_o(q3)
        ok |= ok3

    return ok
