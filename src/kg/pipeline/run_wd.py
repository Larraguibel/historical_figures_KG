# src/run_wd_pipeline.py
# Contiene las herramientas básicas para comunicarse con Wikidata vía SPARQL.

from __future__ import annotations
from pathlib import Path
import csv, random, yaml
from tqdm import tqdm
import re

from kg.wd.truthy import truthy_edges
from kg.wd.filter_usa import filter_us
from kg.wd.utils import labels_es
from kg.wd.build import build_degree1_graph, save_ttl

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SUBJECTS_CSV = PROJECT_ROOT / "data" / "subjects.csv"
OUT_FULL     = PROJECT_ROOT / "graphs" / "full"
OUT_SAMPLED  = PROJECT_ROOT / "graphs" / "sampled"
POOL_YML     = PROJECT_ROOT / "config" / "property_pool.yml"  # opcional

def load_subjects():
    with SUBJECTS_CSV.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def maybe_load_pool():
    if POOL_YML.exists():
        return yaml.safe_load(POOL_YML.read_text(encoding="utf-8"))
    return None

def sample_props(edges: list[tuple[str,str]], clase: str, pool_cfg: dict) -> list[tuple[str,str]]:
    """Muestreo ponderado de propiedades por clase (opcional)."""
    if not pool_cfg or clase not in pool_cfg:
        return edges  # sin variabilidad
    cfg = pool_cfg[clase]
    max_props = int(cfg.get("max_props", len(edges)))
    weights = cfg.get("props", {})  # {"P39":0.9,"P69":0.6,...}

    # agrupar edges por P
    byP = {}
    for P,Q in edges:
        byP.setdefault(P, []).append((P,Q))

    # ordenar P por peso descendente (default=0.5)
    candidates = list(byP.keys())
    candidates.sort(key=lambda P: weights.get(P, 0.5), reverse=True)

    picked = []
    for P in candidates:
        # probabilidad de incluir esta propiedad
        if random.random() <= float(weights.get(P, 0.5)):
            picked.extend(byP[P])
        if len({p for p,_ in picked}) >= max_props:
            break
    return picked or edges[:max_props]

if __name__ == "__main__":
    subs = load_subjects()
    pool = maybe_load_pool()

    for row in tqdm(subs, desc="Wikidata pipeline"):
        root = row["qid"]
        clase = row.get("clase", "default")

        # 1) truthy edges
        edges = truthy_edges(root)
        _P_RE = re.compile(r"^P\d+$")
        edges = [(P, Q) for (P, Q) in edges if _P_RE.match(P) and Q.startswith("Q")]
        if not edges:
            continue

        # 2) filtro USA (sobre objetos)
        objs = [q for _, q in edges]
        try:
            ok_objs = filter_us(objs)   # puede tardar; ahora está más robusto
        except Exception as e:
            print(f"[warn] filtro USA falló para {root}: {e}")
            continue
        edges_us = [(P,Q) for (P,Q) in edges if Q in ok_objs]
        if not edges_us:
            continue

        # 3) variabilidad opcional
        edges_final = sample_props(edges_us, clase, pool) if pool else edges_us

        # 4) labels en ES (opcional pero útil)
        lbl = labels_es([root] + list({q for _,q in edges_final}))

        # 5) construir y serializar
        g = build_degree1_graph(root, edges_final, labels=lbl)
        save_ttl(g, OUT_FULL / f"{root}.ttl")

        # 6) si hay muestreo, guarda también sampled
        if pool:
            save_ttl(g, OUT_SAMPLED / f"{root}.ttl")
