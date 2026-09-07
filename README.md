# 🚀 EXTRACTOR SUITE E-Commerce (v6 & v8)
### 🐣🐥🐧 Motor Avanzado de Catálogo, Galería Completa y Limpieza de Imágenes con IA

Una suite de herramientas robustas en **Python** diseñadas para realizar la extracción masiva de productos (catálogo, metadatos y galerías de imágenes), organización jerárquica y optimización automatizada de assets visuales mediante redes neuronales. 

Originalmente desarrollado para alimentar de forma masiva y limpia aplicaciones web modernas (como plataformas e-commerce construidas en Next.js).

---

## 🗺️ Dirección del Proyecto
* 📖 **[Leer Licencia de Uso](LICENSE)**
* 🚀 **[Ver el Roadmap de Evolución Autónoma](#-roadmap-de-evolución-hacia-un-scraper-universal-y-autónomo)** (Desplegable abajo)

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
git clone https://github.com/3ly4ir777/scripts-python-raspado-web-y-editar-imagenes.git
cd scripts-python-raspado-web-y-editar-imagenes

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

## 🗺️ Roadmap de Evolución: Hacia un Scraper Universal y Autónomo
### 🐣🐥🐧 De un extractor de catálogo manual a un motor con reconocimiento de Stack Tecnológico

<details>
<summary><b>🔍 CLIC AQUÍ PARA DESPLEGAR EL ROADMAP COMPLETO Y FUTURAS FASES</b></summary>

Este bloque detalla la arquitectura planificada para transformar la suite **SPLANET EXTRACTOR** de una herramienta de raspado específica a un motor universal de scraping automatizado.

### 🔐 Fase 1: Desacoplamiento y Configuración Dinámica (`.env`)

Para evitar tener URLs, pausas o configuraciones quemadas directamente en el código (`hardcoded`), el primer paso es implementar un archivo de variables de entorno `.env`. Esto permitirá que cualquier desarrollador configure el comportamiento de la suite sin alterar los scripts principales.

#### Estructura sugerida para el archivo `.env`
Crea un archivo `.env` en la raíz (bloqueado en tu `.gitignore`) con las siguientes variables:

```ini
# Configuración del Objetivo
TARGET_BASE_URL=https://tienda-ejemplo.com
TARGET_PLATFORM=CS-CART # Opciones a futuro: SHOPIFY, WOOCOMMERCE, NEXTJS, CUSTOM

# Tiempos de Espera y Throttling (Anti-Baneos)
DELAY_PRODUCTS=0.8
DELAY_PAGES=1.5
DELAY_IMAGES=0.5
REQUEST_TIMEOUT=25

# Parámetros de Salida (Módulo V8)
OUTPUT_IMAGE_SIZE=1080
IMAGE_SCALE_FACTOR=0.90
```

#### Implementación en los Scripts de Python
Para leer estas variables de forma dinámica en tu código:

```python
import os
from dotenv import load_dotenv

# Cargar configuración global
load_dotenv()

BASE_URL = os.getenv("TARGET_BASE_URL")
PAUSA_ENTRE_PRODUCTOS = float(os.getenv("DELAY_PRODUCTS", 0.8))
TAMAÑO_FINAL = int(os.getenv("OUTPUT_IMAGE_SIZE", 1080))
```

### 🧠 Fase 2: Reconocimiento Autónomo de Stack y Estructura

El objetivo final es crear un script que, al recibir una URL cualquiera, analice la tecnología del sitio objetivo y decida qué estrategia de selectores CSS o endpoints de API utilizar para extraer los productos de forma automática.

#### 1. Motor de Huella Digital Tecnológica (Stack Detector)
Antes de extraer datos, el script analizará las respuestas HTTP y el HTML base buscando patrones clave:
* **Shopify:** Presencia de `/products.json`, objetos `Shopify.shop` en los scripts globales o carpetas `/cdn/shop/`.
* **WooCommerce:** Clases CSS como `product-type-simple`, rutas de archivos `/wp-content/plugins/woocommerce/`.
* **CS-Cart:** Estructura de selectores tradicionales (`.ty-grid-list__item`, `.ty-column`), cookies de sesión específicas o la ruta `/store/`.
* **Next.js / Sitios Modernos:** Etiquetas `<script id="__NEXT_DATA__" type="application/json">` que contienen todos los datos de la página pre-renderizados en texto plano.

#### 2. Pipeline de Detección Automatizada (Prototipo Conceptual)

```python
def detectar_stack_y_extraer(url_objetivo):
    print(f"🕵️ Analizando estructura de: {url_objetivo}")
    
    # Petición inicial para auditar el sitio
    soup, headers = obtener_html_y_headers(url_objetivo)
    
    if os.path.exists(url_join(url_objetivo, "products.json")):
        print("🛍️ Stack Detectado: Shopify. Activando extractor API JSON...")
        return estrategia_shopify_json(url_objetivo)
        
    elif soup.select("script#__NEXT_DATA__"):
        print("🚀 Stack Detectado: Next.js SSR. Extrayendo hydration data directamente...")
        return estrategia_nextjs_data(soup)
        
    elif soup.select("[class*='ty-']") or "/store/" in url_objetivo:
        print("📦 Stack Detectado: CS-Cart / SPlanet Estilo. Activando Extractor V6...")
        return estrategia_cscart_v6(soup)
        
    else:
        print("🔍 Stack Desconocido. Activando algoritmo de selectores heurísticos (AI/Fallback)...")
        return estrategia_heuristica_generica(soup)
```

#### 3. Extracción Avanzada de Hidratación (El "Hackeo" a Next.js)
Si el sitio está hecho con **Next.js**, ¡no hace falta usar BeautifulSoup para buscar etiquetas HTML! Next.js incrusta un JSON gigante en el código fuente con toda la información de la página. El script del futuro simplemente aislará esa etiqueta, convertirá el texto a un diccionario de Python y tendrá los nombres, precios, URLs de imágenes HD y existencias en un solo segundo sin parsear código visual.

---
*Roadmap abierto para Alterar el Status Quo de la extracción de datos. Hecho por y para desarrolladores libres.* 🚀💥🍗

</details>

---
*Desarrollado con el poder de los pingüinos hackers y la bendición del dios Pitón* 🐍 🐣🐥🐧
