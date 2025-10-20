# src/kg/wd/country.py
from pathlib import Path
import yaml
import re
import unicodedata

# ------------------------------
# Descubrir la raíz del proyecto
# ------------------------------
def _find_project_root(start: Path) -> Path:
    """
    Sube directorios hasta encontrar 'config/countries.yml' o 'config/classes.yml'.
    """
    cur = start
    for _ in range(8):
        if (cur / "config" / "countries.yml").exists() or (cur / "config" / "classes.yml").exists():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    # Último fallback: 3 niveles arriba (típico src/kg/wd/ → repo root)
    return start.parents[3] if len(start.parents) >= 3 else start

HERE = Path(__file__).resolve()
PROJECT_ROOT = _find_project_root(HERE)
CFG_COUNTRIES = PROJECT_ROOT / "config" / "countries.yml"
CFG_PROJECT   = PROJECT_ROOT / "config" / "project.yml"

_QID_RE = re.compile(r"^Q\d+$")

# ------------------------------
# Utilidades internas
# ------------------------------
def _load_yaml(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el archivo {path}")
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def _normalize_name(name: str) -> str:
    """Quita tildes, pasa a minúsculas y reemplaza espacios por guiones."""
    return (
        unicodedata.normalize("NFD", name)
        .encode("ascii", "ignore")
        .decode("utf-8")
        .lower()
        .replace(" ", "-")
    )

# ------------------------------
# API pública
# ------------------------------
def load_country_cfg() -> dict:
    """Carga config/countries.yml"""
    return _load_yaml(CFG_COUNTRIES)

def load_project_cfg() -> dict:
    """Carga config/project.yml"""
    return _load_yaml(CFG_PROJECT)

def get_country_from_project() -> tuple[str, str]:
    """
    Devuelve (country_name, country_qid) según config/project.yml y countries.yml.
    """
    countries = load_country_cfg().get("countries", {})
    project = load_project_cfg().get("project", {})

    country_name = project.get("country", None)
    country_qid = None

    if country_name:
        # Si lo ponen como QID directo en project.yml
        if _QID_RE.match(country_name):
            country_qid = country_name
        elif country_name in countries:
            country_qid = countries[country_name]
        else:
            # probar aliases en minúscula
            aliases = load_country_cfg().get("aliases", {})
            country_qid = aliases.get(country_name.lower())
    else:
        # si no hay project.yml o no tiene 'country'
        default_qid = load_country_cfg().get("default", "Q30")
        country_name = "Default"
        country_qid = default_qid

    if not country_qid:
        raise ValueError(f"No se pudo resolver QID para el país '{country_name}'. Revisa config/countries.yml y config/project.yml")
    return country_name, country_qid

def get_country_qid() -> str:
    """Devuelve solo el QID del país activo (p.ej., 'Q30')."""
    _, qid = get_country_from_project()
    return qid

def get_country_name_slug() -> str:
    """Devuelve el nombre del país en formato slug (p.ej., 'united-states')."""
    name, _ = get_country_from_project()
    return _normalize_name(name)

def resolve_country_id(user_arg: str | None) -> str:
    r"""
    Resuelve el país a un QID de Wikidata.
    - Si user_arg es None/'' -> usa el país de config/project.yml (si existe) o 'default' en countries.yml.
    - Acepta QIDs directos (Q\d+).
    - Intenta machar contra 'countries' (nombres exactos) y 'aliases' (en minúsculas) de countries.yml.
    """
    cfg = load_country_cfg()

    # 1) si no se pasó argumento, usa project.yml o default
    if not user_arg:
        try:
            return get_country_qid()
        except Exception:
            return cfg.get("default", "Q30")

    arg = user_arg.strip()

    # 2) QID directo
    if _QID_RE.match(arg):
        return arg

    # 3) nombres exactos en 'countries'
    countries = cfg.get("countries", {})
    if arg in countries:
        return countries[arg]

    # 4) alias en minúsculas
    aliases = cfg.get("aliases", {})
    qid = aliases.get(arg.lower())
    if qid:
        return qid

    # 5) no encontrado
    raise ValueError(
        f"No se pudo resolver el país '{user_arg}'. Añádelo a config/countries.yml (sección 'countries' o 'aliases')."
    )
