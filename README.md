# 🧠 Historical Figures Knowledge Graph

**Historical Figures Knowledge Graph** es un proyecto para la construcción automatizada de un **grafo de conocimiento** sobre personajes históricos de distintos países, combinando información estructurada desde **Wikidata** y contenido textual desde **Wikipedia en español**.  

---

## 📁 Estructura del proyecto

```
historical_figures_KG/
├── config/
│   ├── classes.yml          # Definición de clases/ocupaciones por país o categoría
│   ├── property_map.yml     # Mapeo de propiedades Infobox ↔ Wikidata PID
│   └── shapes.ttl           # Esquema SHACL para validar los grafos RDF
│
├── data/
│   ├── cache_wd/            # Caché local de respuestas SPARQL desde Wikidata
│   ├── cache_wiki/          # Caché local de páginas procesadas desde Wikipedia
│   └── subjects.csv         # Lista de sujetos seleccionados (QID, título, clase)
│
├── graphs/                  # Grafos RDF o NetworkX exportados (salida final)
├── logs/                    # Registros de ejecución
│
├── src/
│   ├── 0_setup_project.py   # Inicialización del entorno y validación de configuración
│   ├── 1_sample_subjects.py # Extracción de entidades humanas desde Wikidata
│   └── 2_fetch_wikipedia.py # Descarga de páginas de Wikipedia y parsing de infoboxes
│
├── requirements.txt         # Dependencias del entorno Python
└── README.md                # Este archivo
```

---

## 🚀 Flujo general

El pipeline consta de **tres etapas principales**:

### **1️⃣ Setup del proyecto**
Archivo: [`src/0_setup_project.py`](src/0_setup_project.py)  
Crea las carpetas necesarias (`data/`, `graphs/`, `logs/`, etc.) y valida que existan los archivos de configuración requeridos:
- `config/classes.yml` — define las clases u ocupaciones a consultar.
- `config/property_map.yml` — traduce los campos del infobox de Wikipedia a propiedades Wikidata (PID).  
Además, imprime en consola cuántas clases y mapeos se detectaron.

Ejemplo de ejecución:
```bash
python src/0_setup_project.py
```

---

### **2️⃣ Muestreo de sujetos desde Wikidata**
Archivo: [`src/1_sample_subjects.py`](src/1_sample_subjects.py)  
Usa consultas SPARQL para extraer un subconjunto de personas históricas con:
- Nacionalidad estadounidense (por defecto),
- Ocupaciones definidas en `classes.yml`,
- Y que tengan artículo en Wikipedia en español.  

Cada consulta devuelve un conjunto de QIDs y títulos asociados, que se almacenan en `data/subjects.csv` con las columnas:
```
qid, eswiki_title, clase
```
El script maneja límites de peticiones y espera entre solicitudes (`sleep_s`) para evitar bloqueos del endpoint.

Ejemplo:
```bash
python src/1_sample_subjects.py
```

---

### **3️⃣ Extracción de información desde Wikipedia**
Archivo: [`src/2_fetch_wikipedia.py`](src/2_fetch_wikipedia.py)  
Lee `data/subjects.csv`, itera sobre los sujetos y descarga los metadatos de cada página usando [`wptools`](https://github.com/siznax/wptools): título, resumen, infobox, enlaces, claims, etc.  
Cada sujeto se guarda como archivo JSON en `data/cache_wiki/` con su QID como nombre.

Ejemplo:
```bash
python src/2_fetch_wikipedia.py
```

---

## ⚙️ Archivos de configuración

### `config/classes.yml`
Define las clases o categorías de interés (por ejemplo, científicos, artistas, políticos) y sus QIDs asociados en Wikidata:

```yaml
clases:
  cientificos:
    ocupaciones: [Q901, Q169470, Q121594]
  artistas:
    ocupaciones: [Q483501, Q1028181, Q33999]
```

---

### `config/property_map.yml`
Asocia los campos del *infobox* de Wikipedia con las propiedades equivalentes en Wikidata (PID).  
Esto permite mapear datos estructurados de Wikipedia hacia el grafo RDF.

```yaml
infobox_to_pid:
  nacimiento: P569
  fallecimiento: P570
  ocupacion: P106
  nacionalidad: P27
```

---

### `config/shapes.ttl`
Archivo SHACL para validar que los nodos y relaciones generadas cumplan con las restricciones definidas (por ejemplo, que cada persona tenga una fecha de nacimiento y nacionalidad válidas).  

Ejemplo de forma:
```ttl
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix ex: <http://example.org/schema#> .

ex:PersonShape a sh:NodeShape ;
    sh:targetClass ex:Person ;
    sh:property [
        sh:path ex:birthDate ;
        sh:datatype xsd:dateTime ;
        sh:minCount 1 ;
    ] .
```

---

## 🧩 Dependencias

El proyecto requiere Python ≥ 3.9 y las librerías listadas en `requirements.txt`.  
Ejemplo de instalación:

```bash
pip install -r requirements.txt
```

Principales dependencias:
- `wptools` — extracción de datos de Wikipedia  
- `SPARQLWrapper` — consultas SPARQL a Wikidata  
- `PyYAML`, `tqdm`, `pandas` (opcional), `rdflib` (para grafo RDF)

---

## 📊 Salida esperada

| Etapa | Archivo / Carpeta | Contenido |
|-------|--------------------|------------|
| Muestreo | `data/subjects.csv` | Lista de sujetos con QID, título y clase |
| Wikipedia | `data/cache_wiki/*.json` | Páginas procesadas con infobox y extractos |
| RDF / Grafo | `graphs/` | (Pendiente) Exportaciones `.ttl`, `.nt`, o `.graphml` |
| Logs | `logs/` | Mensajes de ejecución y errores |

---

## 🧠 Próximos pasos

- [ ] Generar grafo RDF combinando claims + infoboxes.  
- [ ] Validar nodos con `shapes.ttl` (SHACL).  
- [ ] Crear visualizaciones interactivas (por ejemplo, con `pyvis` o `networkx`).  
- [ ] Extender a otros países (`P27`) y traducir resultados.

---

## 📜 Licencia

Este proyecto utiliza datos de **Wikidata** y **Wikipedia**, ambos disponibles bajo licencias abiertas:
- [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)
- [GNU Free Documentation License](https://www.gnu.org/licenses/fdl.html)

El código fuente está bajo licencia **MIT**, salvo indicación contraria.

---

## ✨ Autor

Desarrollado por **Diego Larraguibel**  
Pontificia Universidad Católica de Chile  
Contacto: [dlarraguibel@uc.cl](mailto:dlarraguibel@uc.cl)

---

> “Construir un grafo de conocimiento es reconstruir las conexiones invisibles de la historia.”
