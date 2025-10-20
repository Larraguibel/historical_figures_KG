# src/kg/pipeline/run_wd.py
from __future__ import annotations
from pathlib import Path
import csv
import random
import yaml
import argparse
from tqdm import tqdm
import re
import unicodedata

from kg.wd.truthy import truthy_edges
from kg.wd.filter_country import filter_by_country
from kg.wd.build import build_degree1_graph, save_ttl
from kg.wd.utils import labels
from kg.wd.country import resolve_country_id, get_country_from_project

# --------------------------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------------------------
def _slugify(s: str) -> str:
    return (
        unicodedata.normalize("NFD", s)
        .encode("ascii", "ignore")
        .decode("utf-8")
        .lower()
        .replace(" ", "-")
    )

def find_project_root(start: Path) -> Path:
    cur = start
    for _ in range(6):
        if (cur / "config" / "classes.yml").exists():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return start

HERE = Path(__file__).resolve()
PROJECT_ROOT = find_project_root(HERE.parents[3] if "kg" in str(HERE) else HERE.parents[1])

# Archivos opcionales
POOL_YML = PROJECT_ROOT / "config" / "property_pool.yml"  # variabilidad por clase (opcional)

# --------------------------------------------------------------------------------------
# Carga de entradas
# --------------------------------------------------------------------------------------
def load_subjects(csv_path: Path) -> list[dict]:
    if not csv_path.exists():
        raise FileNotFoundError(f"No se encontró el CSV de sujetos: {csv_path}")
    with csv_path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def maybe_load_pool():
    if POOL_YML.exists():
        return yaml.safe_load(POOL_YML.read_text(encoding="utf-8"))
    return None

def sample_props(edges: list[tuple[str,str]], clase: str, pool_cfg: dict | None) -> list[tuple[str,str]]:
    """Muestreo ponderado de propiedades por clase (opcional)."""
    if not pool_cfg or clase not in pool_cfg:
        return edges  # sin variabilidad
    cfg = pool_cfg[clase]
    max_props = int(cfg.get("max_props", len(edges)))
    weights = cfg.get("props", {})  # {"P39":0.9,"P69":0.6,...}

    # agrupar edges por P
    byP: dict[str, list[tuple[str,str]]] = {}
    for P, Q in edges:
        byP.setdefault(P, []).append((P, Q))

    # ordenar P por peso descendente (default=0.5)
    candidates = list(byP.keys())
    candidates.sort(key=lambda P: float(weights.get(P, 0.5)), reverse=True)

    picked: list[tuple[str,str]] = []
    for P in candidates:
        # probabilidad de incluir esta propiedad
        if random.random() <= float(weights.get(P, 0.5)):
            picked.extend(byP[P])
        # límite por número de propiedades distintas
        if len({p for p, _ in picked}) >= max_props:
            break
    return picked or edges[:max_props]

# --------------------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Construcción de grafos de conocimiento desde Wikidata.")
    ap.add_argument("--country", help="QID, ISO-2/3 o nombre del país (según config/countries.yml). Ej: Q183, de, germany, alemania.")
    ap.add_argument("--label-langs", default="es,en", help='Idiomas de etiquetas (prioridad), ej: "es,en" o "fr,en".')
    ap.add_argument("--subjects-csv", help="Ruta al CSV de sujetos. Por defecto usa data/subjects_{country}.csv o data/subjects.csv.")
    ap.add_argument("--out-dir", help="Directorio base de salida. Por defecto graphs/{country_slug}/")
    args = ap.parse_args()

    # 1) Resolver país: CLI > project.yml
    if args.country:
        try:
            country_qid = resolve_country_id(args.country)
        except Exception as e:
            raise SystemExit(f"[error] No fue posible resolver el país '{args.country}': {e}")
        country_slug = _slugify(args.country) if not args.country.upper().startswith("Q") else country_qid.lower()
        country_label_for_print = args.country
    else:
        try:
            country_name, country_qid = get_country_from_project()
        except Exception as e:
            raise SystemExit(f"[error] No fue posible leer el país desde config/project.yml: {e}")
        country_slug = _slugify(country_name)
        country_label_for_print = country_name

    print(f"País objetivo: {country_label_for_print} ({country_qid})")

    # 2) Elegir CSV de sujetos
    if args.subjects_csv:
        subjects_csv = Path(args.subjects_csv)
    else:
        # preferimos data/subjects_{country}.csv; si no existe, usamos data/subjects.csv
        preferred = PROJECT_ROOT / "data" / f"subjects_{country_slug}.csv"
        fallback = PROJECT_ROOT / "data" / "subjects.csv"
        subjects_csv = preferred if preferred.exists() else fallback
    print(f"CSV de sujetos: {subjects_csv}")

    subs = load_subjects(subjects_csv)
    if not subs:
        raise SystemExit("[error] El CSV de sujetos está vacío.")

    # 3) Directorios de salida
    if args.out_dir:
        out_base = Path(args.out_dir)
    else:
        out_base = PROJECT_ROOT / "graphs" / country_slug
    out_full = out_base / "full"
    out_sampled = out_base / "sampled"
    out_full.mkdir(parents=True, exist_ok=True)
    out_sampled.mkdir(parents=True, exist_ok=True)

    # 4) Config de variabilidad (opcional)
    pool = maybe_load_pool()

    # 5) Procesamiento
    _P_RE = re.compile(r"^P\d+$")

    for row in tqdm(subs, desc="Wikidata pipeline"):
        root = row["qid"]
        clase = row.get("clase", "default")

        # 5.1 truthy edges
        edges = truthy_edges(root)
        edges = [(P, Q) for (P, Q) in edges if _P_RE.match(P) and Q.startswith("Q")]
        if not edges:
            continue

        # 5.2 filtro por país (sobre objetos)
        objs = [q for _, q in edges]
        try:
            ok_objs = filter_by_country(objs, country_qid=country_qid)
        except Exception as e:
            print(f"[warn] filtro por país falló para {root}: {e}")
            continue
        edges_country = [(P, Q) for (P, Q) in edges if Q in ok_objs]
        if not edges_country:
            continue

        # 5.3 variabilidad opcional
        edges_final = sample_props(edges_country, clase, pool) if pool else edges_country

        # 5.4 etiquetas (parametrizable por idioma)
        qids_for_labels = [root] + list({q for _, q in edges_final})
        lbl = labels(qids_for_labels, langs=args.label_langs)

        # 5.5 construir y serializar
        g = build_degree1_graph(root, edges_final, labels=lbl)
        save_ttl(g, out_full / f"{root}.ttl")

        # 5.6 si hay muestreo, guarda también sampled
        if pool:
            save_ttl(g, out_sampled / f"{root}.ttl")

    print(f"\n✅ Salida full:    {out_full}")
    if pool:
        print(f"✅ Salida sampled: {out_sampled}")

if __name__ == "__main__":
    main()
