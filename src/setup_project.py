# src/setup_project.py
from pathlib import Path
import yaml

# Raíz del proyecto = carpeta padre de /src
PROJECT_ROOT = Path(__file__).resolve().parents[1]

DIRS = [
    PROJECT_ROOT / "config",
    PROJECT_ROOT / "data" / "cache_wiki",
    PROJECT_ROOT / "data" / "cache_wd",
    PROJECT_ROOT / "graphs",
    PROJECT_ROOT / "logs",
    PROJECT_ROOT / "config" / "countries.yml",
]

def ensure_dirs():
    for d in DIRS:
        d.mkdir(parents=True, exist_ok=True)

def load_configs():
    classes_path = PROJECT_ROOT / "config" / "classes.yml"
    props_path   = PROJECT_ROOT / "config" / "property_map.yml"

    if not classes_path.exists():
        raise FileNotFoundError(f"No encuentro {classes_path}. ¿Está en 'config/classes.yml'?")
    if not props_path.exists():
        raise FileNotFoundError(f"No encuentro {props_path}. ¿Está en 'config/property_map.yml'?")

    with classes_path.open("r", encoding="utf-8") as f:
        classes = yaml.safe_load(f)
    with props_path.open("r", encoding="utf-8") as f:
        props = yaml.safe_load(f)

    print("Configuración cargada:")
    print(f"- Clases definidas: {len(classes.get('clases', {}))}")
    print(f"- Mapeos infobox -> PID: {len(props.get('infobox_to_pid', {}))}")

if __name__ == "__main__":
    print(f"Proyecto en: {PROJECT_ROOT}")
    ensure_dirs()
    load_configs()
    print("Proyecto inicializado. Listo para el paso 1.")
