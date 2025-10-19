# 🧠 historical_figures_KG

Repositorio para la **construcción automatizada de grafos de conocimiento (Knowledge Graphs)** de personajes históricos de Estados Unidos, a partir de datos de **Wikidata**.

---

## 🚀 Objetivo general

Extraer entidades relacionadas con personajes históricos de Estados Unidos y construir, para cada uno, un **grafo de conocimiento individual de grado 1**, garantizando diversidad entre clases (políticos, artistas, científicos, deportistas, etc.) y filtrando las entidades asociadas al contexto estadounidense.

---

## 🧩 Pipeline funcional

1. **Definir clases históricas** → Se especifican 5 categorías de personajes para asegurar diversidad temática.  
2. **Muestrear sujetos** → Se extrae una muestra balanceada de humanos (Q5, P27=Q30) en Wikidata, distribuidos entre las clases.  
3. **Extraer relaciones directas (grado‑1)** → Se obtienen los claims truthy (wdt:Pxx → wd:Qxx) para cada personaje.  
4. **Filtrar por contexto estadounidense** → Se mantienen solo las entidades con vínculos a EE.UU. mediante P27, P17, P131, P159 o P276.  
5. **Asignar etiquetas** → Se consultan las etiquetas en español o inglés de los QIDs involucrados.  
6. **Construir el grafo individual** → Se crea un grafo RDF con el personaje como nodo raíz y sus entidades conectadas.  
7. **Guardar salida** → Se exporta cada grafo en formato `.ttl` (RDF/Turtle) dentro de la carpeta `graphs/`.

---

## 📁 Estructura del repositorio

```
historical_figures_KG/
├── config/                     # Archivos de configuración
│   ├── classes.yml             # Definición de clases históricas y ocupaciones
│   ├── property_map.yml        # Mapeo opcional de propiedades de interés
│   └── shapes.ttl              # Esquemas o validadores SHACL (opcional)
│
├── data/                       # Datos y caché
│   ├── cache_wd/               # Respuestas SPARQL cacheadas
│   └── subjects.csv            # Muestra de personajes a procesar
│
├── graphs/                     # Grafos RDF generados
│   ├── full/                   # Grafos completos (todas las propiedades)
│   └── sampled/                # Grafos reducidos o muestreados
│
├── logs/                       # Logs del proceso
│
├── src/
│   ├── setup_project.py        # Inicializa la estructura del proyecto
│   └── kg/
│       ├── pipeline/           # Scripts de orquestación
│       │   ├── sample_subjects.py  # Extrae la muestra de personajes
│       │   └── run_wd.py           # Ejecuta el pipeline completo
│       │
│       └── wd/                 # Funciones de interacción con Wikidata
│           ├── utils.py        # SPARQL wrapper, caché y etiquetas
│           ├── truthy.py       # Obtención de relaciones truthy (wdt:Pxx)
│           ├── filter_usa.py   # Filtrado de entidades relacionadas con EE.UU.
│           └── build.py        # Construcción y serialización de grafos RDF
│
├── README.md                   # (este archivo)
└── requirements.txt            # Dependencias del proyecto
```

---

## 🧠 Tecnologías principales

- **Python 3.9+**
- **SPARQLWrapper** — consultas a Wikidata
- **rdflib** — creación y exportación de grafos RDF
- **PyYAML** — lectura de archivos de configuración
- **tqdm** — seguimiento visual de progreso

---

## ⚙️ Ejecución básica

1. **Inicializar proyecto**
   ```bash
   python src/setup_project.py
   ```

2. **Muestrear personajes históricos**
   ```bash
   python -m kg.pipeline.sample_subjects
   ```

3. **Construir grafos Wikidata-only**
   ```bash
   python -m kg.pipeline.run_wd
   ```

Los resultados se guardarán en `graphs/full/` como archivos `.ttl`.

---

## 🧭 Estructura del grafo

Cada grafo sigue la forma:

```
:Personaje_Qxxxx a schema:Person ;
    wdt:P27 wd:Q30 ;
    wdt:P106 wd:Q33999 ;
    wdt:P102 wd:Q29468 ;
    ...
```

Solo se incluyen entidades **de grado 1** y filtradas por pertenencia o relación con EE.UU.

---

## 🧾 Créditos

Proyecto desarrollado por **Diego Larraguibel**  
Pontificia Universidad Católica de Chile  
(M3 MacBook Pro · Python 3.9.6 · venv)

---
