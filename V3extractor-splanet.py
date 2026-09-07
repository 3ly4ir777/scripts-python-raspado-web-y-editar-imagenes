import os
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Configuración inicial
BASE_URL = "https://tienda.splanet.com.mx/store/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Categorías mapeadas con tu estructura exacta en mayúsculas
CATEGORIAS_TRADUCCION = {
    "CREATINA": ["CREATINA", "CREATINAS"],
    "GANADORES DE MASA MUSCULAR": ["GANADORES", "MASS", "GAINERS", "GANADORES DE MASA"],
    "POST-ENTRENOS": ["POST-ENTRENO", "POST ENTRENOS", "POST-ENTRENOS", "RECOVERY"],
    "PRE-ENTRENOS": ["PRE-ENTRENO", "PRE ENTRENOS", "PRE-ENTRENOS", "OXIDOS"],
    "PROMOTORES": ["PROMOTORES", "TESTOSTERONA", "PRO HORMONALES"],
    "PROTEINAS": ["PROTEINA", "PROTEINAS", "WHEY"],
    "QUEMA GRASAS": ["QUEMA GRASAS", "QUEMADORES", "LIPO", "SHRED"],
    "VITAMINAS Y MINERALES": ["VITAMINAS", "MINERALES", "VITAMINAS Y MINERALES", "VITAMINAS-AND-MINERALES"]
}

def limpiar_nombre(texto):
    """Limpia cadenas para carpetas en Windows."""
    texto = texto.strip().upper()
    return re.sub(r'[\\/*?:"<>|]', "", texto)

def obtener_html(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code == 200:
            return BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        print(f"❌ Error al conectar a {url}: {e}")
    return None

def transformar_a_alta_resolucion(url_img):
    """
    Convierte una miniatura de CS-Cart en la imagen original de alta resolución.
    Cambia: /images/thumbnails/160/160/detailed/X/foto.jpg 
    A:      /images/detailed/X/foto.jpg
    """
    if "thumbnails" in url_img:
        # Busca el patrón de carpetas de tamaño numérico y lo remueve para ir al directorio original
        url_alta = re.sub(r'thumbnails/\d+/\d+/', '', url_img)
        return url_alta
    return url_img

def descargar_imagen(url_img, ruta_guardado):
    try:
        url_alta = transformar_a_alta_resolucion(url_img)
        res = requests.get(url_alta, headers=HEADERS, timeout=15)
        
        # Si por alguna razón la alta resolución da error, intentamos con la URL original
        if res.status_code != 200:
            res = requests.get(url_img, headers=HEADERS, timeout=15)
            
        if res.status_code == 200:
            with open(ruta_guardado, 'wb') as f:
                f.write(res.content)
            return True
    except Exception as e:
        print(f"  ⚠️ Error al guardar el archivo: {e}")
    return False

def iniciar_asalto_v3():
    print("🚀 Iniciando Motor Extractor SPlanet V3.0 (Especializado en CS-Cart) 🐣🐥🐧")
    
    # 1. Conectar a la tienda principal para extraer el menú dinámico real
    print("🕵️‍♂️ Mapeando los enlaces reales del menú del sitio...")
    soup_raiz = obtener_html(BASE_URL)
    if not soup_raiz:
        print("No se pudo conectar a la tienda base.")
        return
        
    enlaces_menu = soup_raiz.find_all('a', href=True)
    dict_urls_reales = {}
    
    # Asociar dinámicamente los enlaces de la web con tus carpetas locales
    for enlace in enlaces_menu:
        texto_enlace = enlace.text.strip().upper()
        url_enlace = urljoin(BASE_URL, enlace['href'])
        
        for carpeta_local, palabras_clave in CATEGORIAS_TRADUCCION.items():
            if any(id_cat in texto_enlace for id_cat in palabras_clave):
                if "/store/" in url_enlace and url_enlace != BASE_URL:
                    dict_urls_reales[carpeta_local] = url_enlace

    # Si alguna faltó por menú, forzamos las rutas comunes de CS-Cart para asegurar
    for cap in CATEGORIAS_TRADUCCION.keys():
        if cap not in dict_urls_reales:
            slug = cap.lower().replace(" ", "-").replace("inas", "ina")
            dict_urls_reales[cap] = f"https://tienda.splanet.com.mx/store/{slug}/"

    # Corregir manualmente la que descubriste de vitaminas
    dict_urls_reales["VITAMINAS Y MINERALES"] = "https://splanet.com.mx"

    # 2. Empezar el raspado por cada categoría válida
    for carpeta_local, url_objetivo in dict_urls_reales.items():
        print(f"\n📁 Categoría: {carpeta_local}")
        print(f"🔗 URL: {url_objetivo}")
        
        soup_cat = obtener_html(url_objetivo)
        if not soup_cat:
            continue

        # En CS-Cart, las cajas de producto suelen usar clases que contienen 'product-cell' o 'grid-list__item'
        tarjetas = soup_cat.find_all(['div', 'form'], class_=lambda c: c and any(x in c for x in ['product-cell', 'grid-list__item', 'product-grid', 'ty-column']))
        
        # Si el diseño cambia, recolectamos directo desde los enlaces que contienen las imágenes de producto detailed
        if not tarjetas:
            tarjetas = soup_cat.find_all('div', class_=lambda c: c and 'ty-grid-list__item' in c)

        if not tarjetas:
            # Intento de rescate buscando contenedores generales de listas de productos
            tarjetas = soup_cat.select('.ty-grid-list__item, .ty-product-img')

        descargas_exitosas = 0
        productos_vistos = set() # Evitar duplicados en la misma página

        for tarjeta in tarjetas:
            # Encontrar la imagen del producto
            img_tag = tarjeta.find('img')
            if not img_tag:
                continue
                
            # Extraer url de la imagen (soportando src o data-src de CS-Cart)
            url_img_bruta = img_tag.get('data-src') or img_tag.get('src')
            if not url_img_bruta or "logos" in url_img_bruta or "MARCA" in url_img_bruta or "promo" in url_img_bruta:
                continue
                
            url_img = urljoin(BASE_URL, url_img_bruta)

            # Obtener el nombre del producto desde el atributo alt de la foto o enlaces de título
            nombre_producto = img_tag.get('alt', '').strip()
            if not nombre_producto:
                a_tag = tarjeta.find('a', class_=lambda c: c and 'product-title' in c)
                if a_tag:
                    nombre_producto = a_tag.text.strip()
            
            nombre_prod_limpio = limpiar_nombre(nombre_producto)
            
            if not nombre_prod_limpio or len(nombre_prod_limpio) < 4 or nombre_prod_limpio in productos_vistos:
                continue
                
            productos_vistos.add(nombre_prod_limpio)

            # 3. Creación inteligente de carpetas y guardado
            ruta_carpeta_completa = os.path.join(carpeta_local, nombre_prod_limpio)
            os.makedirs(ruta_carpeta_completa, exist_ok=True)

            # Extraer extensión de archivo original (.jpg, .png, etc.)
            ext = "jpg"
            if ".png" in url_img.lower(): ext = "png"
            elif ".webp" in url_img.lower(): ext = "webp"

            archivo_destino = os.path.join(ruta_carpeta_completa, f"{nombre_prod_limpio}.{ext}")

            if not os.path.exists(archivo_destino):
                print(f"   ⬇️ Guardando: {nombre_prod_limpio}")
                if descargar_imagen(url_img, archivo_destino):
                    descargas_exitosas += 1
                    time.sleep(2.0) # El tiempo perfecto de sigilo 🕵️‍♂️
            else:
                print(f"   ⏭️ Saltado (Ya existe): {nombre_prod_limpio}")

        print(f"✨ Concluido {carpeta_local}. Nuevas imágenes: {descargas_exitosas}")

if __name__ == "__main__":
    iniciar_asalto_v3()
