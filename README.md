# 🧠 Historical Figures Knowledge Graph (KG)

Repositorio para construir **grafos de conocimiento (Knowledge Graphs)** de personajes históricos a partir de **Wikidata**, con soporte para múltiples países e idiomas.

---

## 🏗️ Tecnologías utilizadas

| Tecnología | Uso principal |
|-------------|----------------|
| **Python 3.10+** | Lenguaje base del proyecto |
| **SPARQLWrapper** | Comunicación con el endpoint público de Wikidata |
| **RDFLib** | Lectura y escritura de grafos RDF/Turtle |
| **NetworkX** + **Matplotlib** | Visualización de grafos en entorno local |
| **PyYAML** | Manejo de configuración (`.yml`) |
| **tqdm** | Barras de progreso en consola |
| **pyvis** | Visualización interactiva en HTML |
| **Jupyter Notebook** | Exploración y graficación manual |
| **pyshacl (opcional)** | Validación de grafos con shapes RDF |

---

## 🔄 Pipeline funcional

### 1. **Extracción de sujetos** (por ocupación y país)
Se consultan personajes humanos (`P31=Q5`) que:
- Poseen **una ocupación** listada en `config/classes.yml`.
- Tienen **ciudadanía** (`P27`) asociada al país seleccionado (por nombre, alias o QID).  
- Poseen artículo en Wikidata en el idioma especificado (`--wiki-lang`).

**Salida:**  
`data/subjects_{country}.csv`

---

### 2. **Construcción de grafos desde Wikidata**
Para cada sujeto, se obtienen todas las **relaciones "truthy"** de primer grado desde Wikidata.  
Luego, se filtran las conexiones que pertenecen al mismo país (`filter_country.py`) y se construye un grafo RDF.

**Salida:**  
- `graphs/{country}/full/` → grafos completos  
- `graphs/{country}/sampled/` → versiones reducidas si se usa `config/property_pool.yml`  

---

### 3. **Filtrado geográfico**
El módulo `filter_country.py` verifica si los objetos de un grafo pertenecen al país objetivo, mediante propiedades como:
- `P27` (ciudadanía)  
- `P17` (país)  
- `P131` (división administrativa)  
- `P159` (sede)  
- `P276` (ubicación)  

Esto permite limitar las relaciones solo a entidades del mismo país.

---

### 4. **Construcción y serialización RDF**
`build.py` transforma las aristas filtradas en grafos RDF (de grado 1) y los serializa a formato `.ttl`  
usando `RDFLib`. Los labels se obtienen dinámicamente en español e inglés (`wd/utils.py`).

---

### 5. **Visualización y análisis**
Los grafos pueden visualizarse de dos formas:
- **Interactiva (HTML):** usando `pyvis` o `notebooks/Plot_KG.ipynb`  
- **Local (estática):** con `matplotlib` y `networkx` desde `viz/plot_graph.py`

---

## ⚙️ Ejecución básica

### 1️⃣ Configuración inicial
Edita `config/project.yml` o usa `--country` directamente al ejecutar.

Ejemplo de `config/project.yml`:
```yaml
project:
  country: "United States"
```

Asegúrate de tener las clases y ocupaciones en `config/classes.yml` y los países en `config/countries.yml`:
```yaml
countries:
  Chile: Q298
  United States: Q30
aliases:
  chile: Q298
  usa: Q30
  estados unidos: Q30
default: Q30
```

---

### 2️⃣ Instalar dependencias
```bash
pip install -r requirements.txt
```

---

### 3️⃣ Inicializar el proyecto
```bash
python src/setup_project.py
```
Esto genera la estructura básica de carpetas (`data/`, `graphs/`, etc.)

---

### 4️⃣ Muestrear sujetos (ejemplo: Estados Unidos, Wikidata en español)
```bash
python -m kg.pipeline.sample_subjects --country usa --wiki-lang es --limit-per-class 50
```
Esto generará:  
`data/subjects_usa.csv`

---

### 5️⃣ Construir grafos de conocimiento
```bash
python -m kg.pipeline.run_wd --country usa --label-langs "es,en"
```
Esto descargará los grafos RDF de cada sujeto en:  
`graphs/usa/full/*.ttl`

---

### 6️⃣ Visualizar resultados
Desde Jupyter Notebook:
```bash
jupyter notebook notebooks/Plot_KG.ipynb
```
O desde Python:
```python
from kg.viz.plot_graph import plot_graph_degree1_labeled
plot_graph_degree1_labeled("graphs/usa/full/Q2685.ttl")
```

---

## 📁 Estructura del repositorio

```
historical_figures_KG/
├── config/
│   ├── classes.yml           # Definición de clases y ocupaciones
│   ├── countries.yml         # Mapa de países (QID y alias)
│   ├── project.yml           # País activo del proyecto
│   ├── property_map.yml      # Mapeo opcional de propiedades
│   └── shapes.ttl            # Shape RDF (opcional)
│
├── data/
│   ├── cache_wd/             # Cache de consultas SPARQL
│   └── subjects_usa.csv      # Sujeto muestreado (por país)
│
├── graphs/
│   └── usa/
│       ├── full/             # Grafos completos
│       └── sampled/          # Grafos muestreados
│
├── notebooks/
│   └── Plot_KG.ipynb         # Visualización y exploración
│
├── src/
│   ├── kg/
│   │   ├── pipeline/         # Scripts principales del pipeline
│   │   │   ├── sample_subjects.py
│   │   │   └── run_wd.py
│   │   ├── wd/               # Módulos de interacción con Wikidata
│   │   │   ├── filter_country.py
│   │   │   ├── country.py
│   │   │   ├── truthy.py
│   │   │   ├── utils.py
│   │   │   └── build.py
│   │   ├── viz/              # Visualización local (Python)
│   │   │   └── plot_graph.py
│   │   └── __init__.py
│   └── setup_project.py      # Inicializador del proyecto
│
├── requirements.txt          # Dependencias
└── README.md
```

---

## 🚀 Ejemplo completo de flujo

```bash
# 1. Inicializa la estructura
python src/setup_project.py

# 2. Muestrea personajes históricos
python -m kg.pipeline.sample_subjects --country usa --wiki-lang es --limit-per-class 50

# 3. Construye los grafos RDF
python -m kg.pipeline.run_wd --country usa --label-langs "es,en"

# 4. Visualiza un grafo
python -m notebooks.Plot_KG.ipynb
```

---

## 📦 Salida esperada

```
data/
└── subjects_usa.csv
graphs/
└── usa/
    ├── full/
    │   ├── Q12345.ttl
    │   └── Q67890.ttl
    └── sampled/
        └── Q12345.ttl
```

Cada `.ttl` contiene el grafo RDF de primer grado de un personaje histórico, listo para cargarse en herramientas como **Gephi**, **Neo4j**, o **Protégé**.

---

## 👤 Autor
**Diego Larraguibel**  
Pontificia Universidad Católica de Chile  
Proyecto interdisciplinario de IA y análisis histórico (2025)  
Versión: 2.0 — *Pipeline multi-país y multilingüe*
