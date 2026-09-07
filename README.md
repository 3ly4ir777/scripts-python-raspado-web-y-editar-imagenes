# 🚀 SPLANET EXTRACTOR SUITE (v6 & v8)
### 🐣🐥🐧 Motor Avanzado de Catálogo, Galería Completa y Limpieza de Imágenes con IA

Una suite de herramientas robustas en **Python** diseñadas para realizar la extracción masiva de productos (catálogo, metadatos y galerías de imágenes), organización jerárquica y optimización automatizada de assets visuales mediante redes neuronales. 

Originalmente desarrollado para alimentar de forma masiva y limpia aplicaciones web modernas (como plataformas e-commerce construidas en Next.js).

---

## 🛠️ Arquitectura de la Suite

El proyecto se divide en módulos especializados para garantizar un procesamiento eficiente, reanudable y tolerante a fallas en entornos **GNU/Linux**:

### 1. 📑 Extractor de Catálogo (`v6_extractor.py`)
El núcleo del scraping. Diseñado específicamente para plataformas basadas en CS-Cart.
* **Sesión HTTP Robusta:** Implementa `HTTPAdapter` y políticas de reintento (`Retry`) automáticas para manejar códigos de error temporales (429, 500, 502, 503, 504) sin romper la ejecución.
* **Paginación Real:** Descubre de manera dinámica los enlaces "Siguiente" generados por el servidor en lugar de adivinar parámetros URL secuenciales.
* **Estructuración Nativa:** Organiza las descargas creando de forma automática directorios limpios por categorías principales y nombres de producto válidos para sistemas operativos.

### 2. 🗂️ Organizador Jerárquico (`v7_1_organizer.py`)
Módulo encargado de mapear la arquitectura interna de la tienda web y replicarla localmente.
* Separa de forma inteligente los productos pertenecientes a subcategorías directas de aquellos exclusivos de la categoría raíz, enviando estos últimos a directorios `INDEX` para evitar duplicación de archivos.
* Implementa normalización de texto por compatibilidad de codificación de caracteres.

### 3. 🧼 Limpiador de Imágenes con IA (`v8_cleaner.py`)
El optimizador masivo de assets visuales. Transforma gigabytes de imágenes crudas en componentes listos para producción.
* **Remoción de Fondo automatizada:** Integra la librería `rembg` (basada en modelos de segmentación de IA) para recortar fondos y aplicar transparencias reales en canal Alfa (RGBA).
* **Lienzo E-Commerce Estándar:** Redimensiona el producto manteniendo su proporción original mediante filtros `LANCZOS`, centrándolo de forma exacta en un lienzo transparente cuadrado de **1080x1080 píxeles**.
* **Motor Reanudable e Inteligente:** Cuenta con persistencia de progreso guardando un reporte en tiempo real (`reporte_v8.csv`). Si el proceso se detiene, valida la integridad de los archivos PNG existentes (`image.verify()`) y solo procesa imágenes nuevas o modificadas. ¡Ideal para trabajar con volúmenes de datos masivos (+2 GB)!

---

## 🚀 Requisitos e Instalación

Para ejecutar este proyecto en tu entorno local (altamente recomendado en distribuciones GNU/Linux con Python 3 integrado de forma nativa), clona el repositorio e instala las dependencias necesarias:

```bash
# Clonar el proyecto
git clone https://github.com
cd splanet-extractor

# Instalar las librerías necesarias
pip install pillow rembg requests beautifulsoup4 urllib3
```

---

## 💻 Flujo de Uso

El pipeline de procesamiento se ejecuta en el siguiente orden secuencial:

1. **Fase de Extracción (`v6`):** Corre el extractor para conectarse a la tienda, leer el árbol de categorías, extraer las galerías HD y guardar todo en el almacenamiento local.
2. **Fase de Optimización Visual (`v8`):** Procesa la carpeta de imágenes recolectada. El script removerá los fondos, centrará los productos y generará los PNG finales listos para ser consumidos por tu base de datos o API.

```bash
python v6_extractor.py
python v8_cleaner.py
```

---

## 🛡️ Notas de Desarrollo (Y por qué es mejor que JavaScript)
* **Baterías Incluidas:** Aprovecha módulos nativos del sistema como `os`, `re`, `time` y `json` sin necesidad de inflar el proyecto con un directorio `node_modules` del tamaño de un agujero negro.
* **Hecho para Datos Reales:** Resuelve problemas del mundo real estructurando información pesada de forma ágil, mientras otros siguen configurando entornos y frameworks para una sola SPA.

---
*Desarrollado con el poder de los pingüinos hackers y la bendición del dios Pitón* 🐍 🐣🐥🐧
