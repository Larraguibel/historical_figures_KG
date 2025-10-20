from pathlib import Path
import yaml
import re
import unicodedata

# --------------------------------------------------
# CONFIGURACIÓN
# --------------------------------------------------

CFG_COUNTRIES = Path(__file__).resolve().parents[2] / "config" / "countries.yml"
CFG_PROJECT   = Path(__file__).resolve().parents[2] / "config" / "project.yml"
_QID_RE = re.compile(r"^Q\d+$")

# --------------------------------------------------
# FUNCIONES INTERNAS
# --------------------------------------------------

def _load_yaml(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el archivo {path}")
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def _normalize_name(name: str) -> str:
    """Quita tildes, pasa a minúsculas y reemplaza espacios por guiones."""
    return (
        unicodedata.normalize("NFD", name)
        .encode("ascii", "ignore")
        .decode("utf-8")
        .lower()
        .replace(" ", "-")
    )

# --------------------------------------------------
# FUNCIONES PÚBLICAS
# --------------------------------------------------

def load_country_cfg() -> dict:
    """Carga el archivo config/countries.yml"""
    return _load_yaml(CFG_COUNTRIES)

def load_project_cfg() -> dict:
    """Carga el archivo config/project.yml"""
    return _load_yaml(CFG_PROJECT)

def get_country_from_project() -> tuple[str, str]:
    """
    Devuelve (country_name, country_qid) según config/project.yml.
    Usa countries.yml como mapa auxiliar.
    """
    countries = load_country_cfg().get("countries", {})
    project = load_project_cfg().get("project", {})

    country_name = project.get("country", "USA")
    country_qid = None

    # Intentar encontrar el QID correspondiente
    if country_name in countries:
        country_qid = countries[country_name]
    elif _QID_RE.match(country_name):
        country_qid = country_name
    else:
        # Intentar alias (sin mayúsculas)
        aliases = load_country_cfg().get("aliases", {})
        country_qid = aliases.get(country_name.lower())

    if not country_qid:
        raise ValueError(f"No se pudo resolver QID para el país '{country_name}'.")

    return country_name, country_qid

def get_country_qid() -> str:
    """Devuelve solo el QID del país actual (ej. 'Q30')."""
    _, qid = get_country_from_project()
    return qid

def get_country_name_slug() -> str:
    """Devuelve el nombre del país en formato simple (para nombrar archivos)."""
    name, _ = get_country_from_project()
    return _normalize_name(name)
