from __future__ import annotations
from pathlib import Path
import os
from SPARQLWrapper import SPARQLWrapper, JSON
import hashlib, json, time, random

ENDPOINT = "https://query.wikidata.org/sparql"
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_ROOT = Path(os.getenv("HFKG_DATA_DIR", PROJECT_ROOT / "data"))

CACHE_DIR = DATA_ROOT / "cache_wd"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def _cache_path(query: str) -> Path:
    h = hashlib.sha1(query.encode("utf-8")).hexdigest()
    return CACHE_DIR / f"{h}.json"


def run_sparql(query: str, use_cache: bool = True, sleep_s: float = 0.12, retries: int = 7):
    """Ejecuta una consulta SPARQL con caché, reintentos y backoff exponencial."""
    p = _cache_path(query)
    if use_cache and p.exists():
        return json.loads(p.read_text(encoding="utf-8"))

    backoff = 0.8
    last_err = None
    for attempt in range(retries):
        try:
            sp = SPARQLWrapper(ENDPOINT, agent="kg-country-agnostic/0.1 (mailto:example@example.com)")
            sp.setReturnFormat(JSON)
            sp.setQuery(query)
            sp.setTimeout(120)  # 2 minutos
            res = sp.query().convert()
            if sleep_s:
                time.sleep(sleep_s)  # cortesía con el endpoint
            if use_cache:
                p.write_text(json.dumps(res), encoding="utf-8")
            return res
        except Exception as e:
            last_err = e
            # backoff exponencial + jitter
            time.sleep(backoff + random.uniform(0, 0.6))
            backoff = min(backoff * 1.9, 10.0)
    raise last_err


def labels(qids: list[str], langs: str = "es,en") -> dict[str, str]:
    """
    Devuelve etiquetas de Wikidata en los idiomas especificados (por defecto 'es,en').

    Parameters
    ----------
    qids : list[str]
        Lista de QIDs (ej. ["Q30", "Q183", ...])
    langs : str
        Lenguajes preferidos separados por coma, en orden de prioridad (ej. "es,en" o "fr,en").

    Returns
    -------
    dict[str, str]
        Diccionario QID → etiqueta.
    """
    if not qids:
        return {}
    # dedup + filtro
    qids = list(dict.fromkeys([q for q in qids if q and q.startswith("Q")]))
    if not qids:
        return {}

    values = " ".join(f"wd:{q}" for q in qids)
    q = f"""
    SELECT ?x ?xLabel WHERE {{
      VALUES ?x {{ {values} }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "{langs}". }}
    }}
    """

    res = run_sparql(q)
    out = {}
    for b in res["results"]["bindings"]:
        qid = b["x"]["value"].split("/")[-1]
        out[qid] = b.get("xLabel", {}).get("value", qid)
    return out
