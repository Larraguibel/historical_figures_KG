# src/wd_filter_usa.py
from __future__ import annotations
from typing import Iterable
from kg.wd.utils import run_sparql

def filter_us(qids: Iterable[str], batch_size: int = 100) -> set[str]:
    """
    Retorna el subconjunto de qids que cumplen pertenencia a EE.UU., mediante:
      - P27 = Q30 (personas)
      - P17 = Q30
      - P131* dentro de entidad con P17 = Q30
      - P159 (HQ) en lugar con P17 = Q30
      - P276 situado en lugar con P17 = Q30 o P131* -> Q30
    """
    qids = list(dict.fromkeys(qids))
    ok = set()
    for i in range(0, len(qids), batch_size):
        chunk = qids[i:i+batch_size]
        values = " ".join(f"wd:{q}" for q in chunk)
        q = f"""
        SELECT DISTINCT ?o WHERE {{
          VALUES ?o {{ {values} }}

          {{
            ?o wdt:P27 wd:Q30 .           # personas
          }}
          UNION
          {{
            ?o wdt:P17 wd:Q30 .           # país = EE.UU.
          }}
          UNION
          {{
            ?o wdt:P131* ?adm .
            ?adm wdt:P17 wd:Q30 .         # ubicado en admin. de EE.UU.
          }}
          UNION
          {{
            ?o wdt:P159 ?hq .
            ?hq wdt:P17 wd:Q30 .          # HQ en EE.UU.
          }}
          UNION
          {{
            ?o wdt:P276 ?place .
            {{ ?place wdt:P17 wd:Q30 . }}
            UNION
            {{ ?place wdt:P131* ?a . ?a wdt:P17 wd:Q30 . }}
          }}
        }}
        """
        res = run_sparql(q)
        for b in res["results"]["bindings"]:
            ok.add(b["o"]["value"].split("/")[-1])
    return ok
