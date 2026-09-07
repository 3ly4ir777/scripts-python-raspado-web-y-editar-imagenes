# 🗺️ Roadmap de Evolución: Hacia un Scraper Universal y Autónomo
### 🐣🐥🐧 De un extractor de catálogo manual a un motor con reconocimiento de Stack Tecnológico

Este documento detalla la arquitectura planificada para transformar la suite **SPLANET EXTRACTOR** de una herramienta de raspado específica a un motor universal de scraping automatizado.

---

## 🔐 Fase 1: Desacoplamiento y Configuración Dinámica (`.env`)

Para evitar tener URLs, pausas o configuraciones quemadas directamente en el código (`hardcoded`), el primer paso es implementar un archivo de variables de entorno `.env`. Esto permitirá que cualquier desarrollador configure el comportamiento de la suite sin alterar los scripts principales.

### Estructura sugerida para el archivo `.env`
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

### Implementación en los Scripts de Python
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

---

## 🧠 Fase 2: Reconocimiento Autónomo de Stack y Estructura

El objetivo final es crear un script que, al recibir una URL cualquiera, analice la tecnología del sitio objetivo y decida qué estrategia de selectores CSS o endpoints de API utilizar para extraer los productos de forma automática.

### 1. Motor de Huella Digital Tecnológica (Stack Detector)
Antes de extraer datos, el script analizará las respuestas HTTP y el HTML base buscando patrones clave:
* **Shopify:** Presencia de `/products.json`, objetos `Shopify.shop` en los scripts globales o carpetas `/cdn/shop/`.
* **WooCommerce:** Clases CSS como `product-type-simple`, rutas de archivos `/wp-content/plugins/woocommerce/`.
* **CS-Cart:** Estructura de selectores tradicionales (`.ty-grid-list__item`, `.ty-column`), cookies de sesión específicas o la ruta `/store/`.
* **Next.js / Sitios Modernos:** Etiquetas `<script id="__NEXT_DATA__" type="application/json">` que contienen todos los datos de la página pre-renderizados en texto plano.

### 2. Pipeline de Detección Automatizada (Prototipo Conceptual)

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

### 3. Extracción Avanzada de Hidratación (El "Hackeo" a Next.js)
Si el sitio está hecho con **Next.js**, ¡no hace falta usar BeautifulSoup para buscar etiquetas HTML! Next.js incrusta un JSON gigante en el código fuente con toda la información de la página. El script del futuro simplemente aislará esa etiqueta, convertirá el texto a un diccionario de Python y tendrá los nombres, precios, URLs de imágenes HD y existencias en un solo segundo sin parsear código visual.

---
*Roadmap abierto para Alterar el Status Quo de la extracción de datos. Hecho por y para desarrolladores libres.* 🚀💥🍗
