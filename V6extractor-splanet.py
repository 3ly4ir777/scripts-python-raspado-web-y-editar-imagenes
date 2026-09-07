import os
import re
import time
import requests

from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qsl, urlencode, urlunparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

BASE_URL = "https://tienda.splanet.com.mx/store/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
}

# Intentamos aprovechar el máximo que ofrece la tienda.
# Si la web ignora este parámetro y devuelve 12, el script
# seguirá funcionando mediante su paginador real.
ITEMS_POR_PAGINA = 96

# Pausas para no bombardear el servidor.
PAUSA_ENTRE_PRODUCTOS = 0.8
PAUSA_ENTRE_PAGINAS = 1.5
PAUSA_ENTRE_IMAGENES = 0.5

# Tiempo máximo de espera de las peticiones.
TIMEOUT_HTML = 25
TIMEOUT_IMAGEN = 25


# ============================================================
# SESIÓN HTTP ROBUSTA
# ============================================================

def crear_sesion():
    """
    Crea una sesión requests con reintentos automáticos
    para errores temporales del servidor.
    """

    sesion = requests.Session()

    reintentos = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=1.0,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )

    adaptador = HTTPAdapter(max_retries=reintentos)

    sesion.mount("http://", adaptador)
    sesion.mount("https://", adaptador)

    sesion.headers.update(HEADERS)

    return sesion


SESSION = crear_sesion()


# ============================================================
# MAPA MAESTRO DE CATEGORÍAS
# ============================================================
#
# Se utilizan las URLs que ya habíamos confirmado.
#
# La carpeta local es la categoría principal.
# Las URLs incluyen tanto la categoría padre como sus ramas.
#
# ============================================================

URLS_MAESTRAS = {

    "BCAA S": [
        "https://tienda.splanet.com.mx/store/bcaa-s/",
    ],

    "COLAGENO": [
        "https://tienda.splanet.com.mx/store/colageno/",
    ],

    "CREATINA": [
        "https://tienda.splanet.com.mx/store/creatina/",
    ],

    "GANADORES DE MASA MUSCULAR": [
        "https://tienda.splanet.com.mx/store/ganadores-de-masa-muscular/",
    ],

    "POST-ENTRENOS": [
        "https://tienda.splanet.com.mx/store/post-entrenos/",
        "https://tienda.splanet.com.mx/store/post-entrenos/glutamina/",
    ],

    "PRE-ENTRENOS": [
        "https://tienda.splanet.com.mx/store/pre-entrenos/",
        "https://tienda.splanet.com.mx/store/pre-entrenos/oxido-nitrico/",
        "https://tienda.splanet.com.mx/store/pre-entrenos/oxido-nitrico/capsulas/",
        "https://tienda.splanet.com.mx/store/pre-entrenos/oxido-nitrico/concentrados/",
        "https://tienda.splanet.com.mx/store/pre-entrenos/oxido-nitrico/polvos/",
    ],

    "PROMOTORES": [
        "https://tienda.splanet.com.mx/store/promotores/",
        "https://tienda.splanet.com.mx/store/promotores/constructor-muscular/",
        "https://tienda.splanet.com.mx/store/promotores/pro-h-crecimiento/",
        "https://tienda.splanet.com.mx/store/promotores/pro-testoterona/",
    ],

    "PROTEINAS": [
        "https://tienda.splanet.com.mx/store/proteinas/",
        "https://tienda.splanet.com.mx/store/proteinas/bajas-calorias/",
        "https://tienda.splanet.com.mx/store/proteinas/constructor-muscular/",
        "https://tienda.splanet.com.mx/store/proteinas/de-carne/",
        "https://tienda.splanet.com.mx/store/proteinas/formulas-avanzadas-de-suero/",
        "https://tienda.splanet.com.mx/store/proteinas/iso-aislados-de-suero/",
        "https://tienda.splanet.com.mx/store/proteinas/liberacion-sostenida/",
        "https://tienda.splanet.com.mx/store/proteinas/otras-formulas/",
    ],

    "QUEMA GRASAS": [
        "https://tienda.splanet.com.mx/store/quema-grasas/",
        "https://tienda.splanet.com.mx/store/quema-grasas/carnitina/",
        "https://tienda.splanet.com.mx/store/quema-grasas/diureticos/",
        "https://tienda.splanet.com.mx/store/quema-grasas/inhibidores/",
        "https://tienda.splanet.com.mx/store/quema-grasas/termogenicos/",
    ],

    "VARIOS": [
        "https://tienda.splanet.com.mx/store/varios/",
        "https://tienda.splanet.com.mx/store/varios/accesorios/",
        "https://tienda.splanet.com.mx/store/varios/accesorios/para-la-piel/",
        "https://tienda.splanet.com.mx/store/varios/accesorios/shakers/",
        "https://tienda.splanet.com.mx/store/varios/acidos-grasos/",
        "https://tienda.splanet.com.mx/store/varios/acidos-grasos/cla/",
        "https://tienda.splanet.com.mx/store/varios/acidos-grasos/mct/",
        "https://tienda.splanet.com.mx/store/varios/acidos-grasos/omega-3-6-9/",
        "https://tienda.splanet.com.mx/store/varios/alto-rendimiento/",
        "https://tienda.splanet.com.mx/store/varios/alto-rendimiento/intra-entrenamiento/",
        "https://tienda.splanet.com.mx/store/varios/aminoacidos/",
        "https://tienda.splanet.com.mx/store/varios/aminoacidos/amino-especificos/",
        "https://tienda.splanet.com.mx/store/varios/aminoacidos/amino-liquidos/",
        "https://tienda.splanet.com.mx/store/varios/barras/",
        "https://tienda.splanet.com.mx/store/varios/especiales/",
        "https://tienda.splanet.com.mx/store/varios/especiales/ofertas-y-promociones/",
        "https://tienda.splanet.com.mx/store/varios/para-ellas/",
        "https://tienda.splanet.com.mx/store/varios/para-ellas/proteinas/",
        "https://tienda.splanet.com.mx/store/varios/para-ellas/quemadores/",
    ],

    "VITAMINAS Y MINERALES": [
        "https://tienda.splanet.com.mx/store/vitaminas-and-minerales/",
        "https://tienda.splanet.com.mx/store/vitaminas-and-minerales/antioxidantes/",
        "https://tienda.splanet.com.mx/store/vitaminas-and-minerales/salud-articular/",
        "https://tienda.splanet.com.mx/store/vitaminas-and-minerales/varios/",
        "https://tienda.splanet.com.mx/store/vitaminas-and-minerales/vitaminas/",
    ],
}


# ============================================================
# UTILIDADES
# ============================================================

def limpiar_nombre(texto):
    """
    Limpia un nombre para poder utilizarlo como carpeta/archivo
    en Windows.
    """

    if not texto:
        return ""

    texto = texto.strip().upper()

    # Caracteres prohibidos por Windows.
    texto = re.sub(r'[\\/*?:"<>|]', "", texto)

    # Eliminar espacios repetidos.
    texto = " ".join(texto.split())

    # Windows tampoco permite estos nombres especiales.
    nombres_reservados = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    }

    if texto in nombres_reservados:
        texto = f"_{texto}_"

    # Windows no acepta punto o espacio al final.
    texto = texto.rstrip(" .")

    return texto


def normalizar_texto(texto):
    """
    Normaliza texto para comparaciones.
    """

    if not texto:
        return ""

    texto = texto.strip().upper()
    texto = " ".join(texto.split())

    return texto


def es_url_imagen(url):
    """
    Determina si una URL parece apuntar a una imagen.
    """

    if not url:
        return False

    url_limpia = url.lower().split("?")[0]

    extensiones = (
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".gif",
        ".avif",
    )

    return url_limpia.endswith(extensiones)


def obtener_extension(url, content_type=None):
    """
    Determina la extensión de la imagen.
    """

    url_limpia = url.lower().split("?")[0]

    if ".jpeg" in url_limpia:
        return "jpeg"

    if ".jpg" in url_limpia:
        return "jpg"

    if ".png" in url_limpia:
        return "png"

    if ".webp" in url_limpia:
        return "webp"

    if ".gif" in url_limpia:
        return "gif"

    if ".avif" in url_limpia:
        return "avif"

    if content_type:
        content_type = content_type.lower()

        if "jpeg" in content_type:
            return "jpg"

        if "png" in content_type:
            return "png"

        if "webp" in content_type:
            return "webp"

        if "gif" in content_type:
            return "gif"

        if "avif" in content_type:
            return "avif"

    return "jpg"


# ============================================================
# PETICIONES HTML
# ============================================================

def obtener_html(url):
    """
    Descarga una página y devuelve BeautifulSoup.
    """

    try:
        respuesta = SESSION.get(
            url,
            timeout=TIMEOUT_HTML,
            allow_redirects=True,
        )

        if respuesta.status_code == 200:
            return BeautifulSoup(respuesta.text, "html.parser")

        print(
            f"      ⚠️ HTTP {respuesta.status_code}: {url}"
        )

    except requests.RequestException as error:
        print(
            f"      ❌ Error de red en {url}: {error}"
        )

    return None


# ============================================================
# ITEMS POR PÁGINA
# ============================================================

def agregar_items_por_pagina(url, cantidad=96):
    """
    Agrega o reemplaza items_per_page sin destruir el resto
    de los parámetros de la URL.
    """

    partes = urlparse(url)

    parametros = parse_qsl(
        partes.query,
        keep_blank_values=True,
    )

    nuevos = []

    encontrado = False

    for clave, valor in parametros:
        if clave == "items_per_page":
            if not encontrado:
                nuevos.append(
                    ("items_per_page", str(cantidad))
                )
                encontrado = True
        else:
            nuevos.append((clave, valor))

    if not encontrado:
        nuevos.append(
            ("items_per_page", str(cantidad))
        )

    nueva_query = urlencode(nuevos)

    return urlunparse(
        (
            partes.scheme,
            partes.netloc,
            partes.path,
            partes.params,
            nueva_query,
            partes.fragment,
        )
    )


# ============================================================
# TARJETAS DE PRODUCTO
# ============================================================

def obtener_tarjetas_producto(soup):
    """
    Busca las tarjetas de producto utilizando varios selectores
    porque el tema de CS-Cart puede utilizar más de una clase.
    """

    selectores = [
        ".ty-grid-list__item",
        ".grid-list__item",
        ".product-cell",
        "[class*='product-grid']",
        ".ty-column",
    ]

    tarjetas = []

    for selector in selectores:
        encontradas = soup.select(selector)

        if encontradas:
            tarjetas.extend(encontradas)

    # Deduplicar objetos BeautifulSoup.
    resultado = []
    vistos = set()

    for tarjeta in tarjetas:
        identificador = id(tarjeta)

        if identificador not in vistos:
            vistos.add(identificador)
            resultado.append(tarjeta)

    return resultado


# ============================================================
# URL DE PRODUCTO
# ============================================================

def parece_producto_url(url):
    """
    Filtra URLs que claramente no son fichas de producto.
    """

    if not url:
        return False

    url_lower = url.lower()

    if "/store/" not in url_lower:
        return False

    if "/images/" in url_lower:
        return False

    basura = [
        "/cart",
        "/checkout",
        "/wishlist",
        "/compare",
        "/login",
        "/register",
        "/search",
        "/categories",
        "/page-",
    ]

    if any(elemento in url_lower for elemento in basura):
        return False

    return True


def extraer_url_producto(celda, url_base):
    """
    Intenta encontrar la URL real de la ficha del producto.
    """

    # --------------------------------------------------------
    # Método 1:
    # el enlace que contiene directamente la imagen.
    # --------------------------------------------------------

    imagen = celda.find("img")

    if imagen:
        padre = imagen.parent

        if padre and padre.name == "a":
            href = padre.get("href")

            if href:
                url = urljoin(url_base, href)

                if parece_producto_url(url):
                    return url

    # --------------------------------------------------------
    # Método 2:
    # revisar todos los enlaces de la tarjeta.
    # --------------------------------------------------------

    for enlace in celda.find_all("a", href=True):

        href = enlace.get("href")

        if not href:
            continue

        url = urljoin(url_base, href)

        if parece_producto_url(url):
            return url

    return None


# ============================================================
# NOMBRE DEL PRODUCTO
# ============================================================

def extraer_nombre_producto(celda):
    """
    Intenta obtener el nombre del producto de varias maneras.
    """

    imagen = celda.find("img")

    if imagen:

        alt = imagen.get("alt", "").strip()

        if len(alt) >= 3:
            return alt

        title = imagen.get("title", "").strip()

        if len(title) >= 3:
            return title

    # Clases habituales de CS-Cart.
    selectores = [
        ".product-title",
        ".ty-grid-list__item-name",
        ".ty-grid-list__item-name a",
        "[class*='product-title']",
        "[class*='item-name']",
    ]

    for selector in selectores:

        elemento = celda.select_one(selector)

        if elemento:

            texto = elemento.get_text(
                " ",
                strip=True,
            )

            if len(texto) >= 3:
                return texto

    # Último recurso: revisar enlaces.
    for enlace in celda.find_all("a", href=True):

        texto = enlace.get_text(
            " ",
            strip=True,
        )

        if len(texto) >= 3:

            texto_normalizado = normalizar_texto(texto)

            basura = [
                "VISTA RÁPIDA",
                "VISTA RAPIDA",
                "AÑADIR",
                "CARRITO",
                "COMPARAR",
                "WISHLIST",
            ]

            if not any(
                elemento in texto_normalizado
                for elemento in basura
            ):
                return texto

    return ""


# ============================================================
# EXTRAER PRODUCTOS DE UNA PÁGINA
# ============================================================

def extraer_productos_de_pagina(soup, url_base):
    """
    Devuelve:

        [
            {
                "url": "...",
                "nombre": "...",
                "imagen_catalogo": "..."
            }
        ]
    """

    tarjetas = obtener_tarjetas_producto(soup)

    productos = []
    urls_vistas = set()

    for celda in tarjetas:

        url_producto = extraer_url_producto(
            celda,
            url_base,
        )

        if not url_producto:
            continue

        url_producto = url_producto.split("#")[0]

        if url_producto in urls_vistas:
            continue

        nombre = extraer_nombre_producto(celda)

        nombre_limpio = limpiar_nombre(nombre)

        if not nombre_limpio:
            continue

        # Evitar basura del tema.
        basura = [
            "PINTEREST",
            "VISTA RAPIDA",
            "VISTA RÁPIDA",
            "SEGUIMIENTO",
            "CARRITO",
        ]

        if any(
            palabra in nombre_limpio
            for palabra in basura
        ):
            continue

        imagen_catalogo = ""

        imagen = celda.find("img")

        if imagen:
            imagen_catalogo = (
                imagen.get("data-src")
                or imagen.get("data-lazy-src")
                or imagen.get("src")
                or ""
            )

        if imagen_catalogo:
            imagen_catalogo = urljoin(
                url_base,
                imagen_catalogo,
            )

        urls_vistas.add(url_producto)

        productos.append(
            {
                "url": url_producto,
                "nombre": nombre_limpio,
                "imagen_catalogo": imagen_catalogo,
            }
        )

    return productos


# ============================================================
# PAGINACIÓN REAL DE LA TIENDA
# ============================================================

def encontrar_siguiente_url(soup, url_actual):
    """
    Busca el enlace real de "Siguiente" generado por la tienda.

    Esto es deliberadamente preferido a inventar:
        ?page=2
        ?page=3
        etc.

    La tienda actualmente utiliza rutas como:
        /page-2/
        /page-3/
    """

    # --------------------------------------------------------
    # 1. Buscar rel="next"
    # --------------------------------------------------------

    enlace_next = soup.find(
        "a",
        attrs={"rel": True},
    )

    if enlace_next:

        rel = enlace_next.get("rel")

        if isinstance(rel, list):
            rel_texto = " ".join(rel).lower()
        else:
            rel_texto = str(rel).lower()

        if "next" in rel_texto:

            href = enlace_next.get("href")

            if href:
                return urljoin(
                    url_actual,
                    href,
                )

    # --------------------------------------------------------
    # 2. Buscar texto "Siguiente"
    # --------------------------------------------------------

    candidatos = []

    for enlace in soup.find_all("a", href=True):

        texto = normalizar_texto(
            enlace.get_text(
                " ",
                strip=True,
            )
        )

        href = enlace.get("href")

        if not href:
            continue

        if (
            texto == "SIGUIENTE"
            or texto.startswith("SIGUIENTE ")
        ):
            candidatos.append(
                urljoin(url_actual, href)
            )

    if candidatos:

        # Preferir una URL distinta a la actual.
        for candidato in candidatos:

            if candidato.rstrip("/") != url_actual.rstrip("/"):
                return candidato

    # --------------------------------------------------------
    # 3. Fallback: detectar /page-N/
    # --------------------------------------------------------

    match_actual = re.search(
        r"/page-(\d+)/?$",
        urlparse(url_actual).path,
    )

    if match_actual:
        numero_actual = int(
            match_actual.group(1)
        )
    else:
        numero_actual = 1

    numero_siguiente = numero_actual + 1

    patron = re.compile(
        rf"/page-{numero_siguiente}/?$",
        re.IGNORECASE,
    )

    for enlace in soup.find_all(
        "a",
        href=True,
    ):

        href = enlace.get("href")

        if not href:
            continue

        url_candidata = urljoin(
            url_actual,
            href,
        )

        ruta = urlparse(
            url_candidata
        ).path

        if patron.search(ruta):
            return url_candidata

    return None


# ============================================================
# CONVERSIÓN A IMAGEN HD
# ============================================================

def forzar_alta_resolucion(url_img):
    """
    CS-Cart puede entregar algo como:

    /store/images/thumbnails/35/35/detailed/9/foto.jpg

    y la imagen original puede encontrarse como:

    /store/images/detailed/9/foto.jpg

    Eliminamos únicamente el segmento de thumbnails.
    """

    if not url_img:
        return url_img

    return re.sub(
        r"/thumbnails/\d+/\d+/",
        "/",
        url_img,
        flags=re.IGNORECASE,
    )


# ============================================================
# EXTRAER GALERÍA DEL PRODUCTO
# ============================================================

def extraer_imagenes_producto(url_producto):
    """
    Entra a la ficha individual y busca todas las imágenes
    reales de la galería.

    Primero intenta los enlaces <a href="...imagen...">,
    porque suelen apuntar a la imagen grande.

    Después utiliza <img src/data-src> como respaldo.
    """

    soup = obtener_html(url_producto)

    if not soup:
        return []

    imagenes = []

    # --------------------------------------------------------
    # 1. ENLACES DIRECTOS A IMÁGENES
    # --------------------------------------------------------

    for enlace in soup.find_all(
        "a",
        href=True,
    ):

        href = enlace.get("href")

        if not href:
            continue

        url = urljoin(
            url_producto,
            href,
        )

        if not es_url_imagen(url):
            continue

        url_lower = url.lower()

        if any(
            basura in url_lower
            for basura in [
                "logo",
                "banner",
                "favicon",
                "marca",
                "social",
                "facebook",
                "instagram",
                "pinterest",
            ]
        ):
            continue

        imagenes.append(url)

    # --------------------------------------------------------
    # 2. IMÁGENES DEL HTML
    # --------------------------------------------------------

    for imagen in soup.find_all("img"):

        posibles = [
            imagen.get("data-src"),
            imagen.get("data-lazy-src"),
            imagen.get("data-original"),
            imagen.get("src"),
        ]

        for src in posibles:

            if not src:
                continue

            url = urljoin(
                url_producto,
                src,
            )

            if not es_url_imagen(url):
                continue

            url_lower = url.lower()

            if any(
                basura in url_lower
                for basura in [
                    "logo",
                    "banner",
                    "favicon",
                    "marca",
                    "social",
                    "facebook",
                    "instagram",
                    "pinterest",
                ]
            ):
                continue

            imagenes.append(url)

            # Con una fuente válida basta.
            break

    # --------------------------------------------------------
    # 3. DEDUPLICACIÓN INTELIGENTE
    #
    # Dos thumbnails diferentes que apuntan al mismo original
    # no deben convertirse en dos archivos.
    # --------------------------------------------------------

    resultado = []
    claves_vistas = set()

    for url in imagenes:

        url_hd = forzar_alta_resolucion(url)

        clave = url_hd.split("?")[0].lower()

        if clave in claves_vistas:
            continue

        claves_vistas.add(clave)

        resultado.append(url_hd)

    return resultado


# ============================================================
# DESCARGA DE IMAGEN
# ============================================================

def descargar_imagen(url_img, ruta_destino):
    """
    Intenta primero la versión HD.
    Si falla, intenta la URL original.
    """

    urls_intento = []

    url_hd = forzar_alta_resolucion(
        url_img
    )

    urls_intento.append(url_hd)

    if url_img != url_hd:
        urls_intento.append(url_img)

    for url in urls_intento:

        try:

            respuesta = SESSION.get(
                url,
                timeout=TIMEOUT_IMAGEN,
                stream=True,
            )

            if respuesta.status_code != 200:
                continue

            content_type = (
                respuesta.headers.get(
                    "Content-Type",
                    "",
                )
            )

            if not content_type.lower().startswith(
                "image/"
            ):
                continue

            # Crear carpeta por seguridad.
            os.makedirs(
                os.path.dirname(ruta_destino),
                exist_ok=True,
            )

            with open(
                ruta_destino,
                "wb",
            ) as archivo:

                for bloque in respuesta.iter_content(
                    chunk_size=64 * 1024
                ):

                    if bloque:
                        archivo.write(bloque)

            # Comprobar que realmente quedó algo.
            if os.path.exists(ruta_destino):

                tamaño = os.path.getsize(
                    ruta_destino
                )

                if tamaño > 0:
                    return True

                try:
                    os.remove(
                        ruta_destino
                    )
                except OSError:
                    pass

        except requests.RequestException:
            continue

        except OSError:
            continue

    return False


# ============================================================
# RESPALDO DE IMAGEN DE CATÁLOGO
# ============================================================

def obtener_foto_respaldo(producto):
    """
    Si la ficha del producto no entrega galería,
    utiliza la imagen que ya vimos en la tarjeta del catálogo.
    """

    imagen = producto.get(
        "imagen_catalogo",
        "",
    )

    if not imagen:
        return []

    return [imagen]


# ============================================================
# PROCESAR PRODUCTO
# ============================================================

def procesar_producto(
    categoria_local,
    producto,
):
    """
    Crea:

        CATEGORIA/
            PRODUCTO/
                PRODUCTO_1.jpg
                PRODUCTO_2.jpg
                ...

    """

    nombre = producto["nombre"]
    url_producto = producto["url"]

    carpeta_producto = os.path.join(
        categoria_local,
        nombre,
    )

    os.makedirs(
        carpeta_producto,
        exist_ok=True,
    )

    print(
        f"       🔍 Producto: {nombre}"
    )

    print(
        f"          🔗 {url_producto}"
    )

    # --------------------------------------------------------
    # Buscar galería completa.
    # --------------------------------------------------------

    imagenes = extraer_imagenes_producto(
        url_producto
    )

    # --------------------------------------------------------
    # Respaldo.
    # --------------------------------------------------------

    if not imagenes:

        print(
            "          ⚠️ Galería no encontrada. "
            "Usando imagen del catálogo."
        )

        imagenes = obtener_foto_respaldo(
            producto
        )

    if not imagenes:

        print(
            "          ❌ No se encontró ninguna imagen."
        )

        return 0

    print(
        f"          🖼️ Imágenes encontradas: "
        f"{len(imagenes)}"
    )

    guardadas = 0

    # --------------------------------------------------------
    # Descargar todas.
    # --------------------------------------------------------

    for indice, url_imagen in enumerate(
        imagenes,
        start=1,
    ):

        extension = obtener_extension(
            url_imagen
        )

        nombre_archivo = (
            f"{nombre}_{indice}.{extension}"
        )

        ruta_final = os.path.join(
            carpeta_producto,
            nombre_archivo,
        )

        # Ya existe.
        if os.path.exists(ruta_final):

            tamaño = os.path.getsize(
                ruta_final
            )

            if tamaño > 0:

                print(
                    f"          ⏭️ Ya existe: "
                    f"{nombre_archivo}"
                )

                continue

        print(
            f"          ⬇️ {nombre_archivo}"
        )

        if descargar_imagen(
            url_imagen,
            ruta_final,
        ):

            guardadas += 1

            print(
                f"             ✅ Guardada"
            )

        else:

            print(
                f"             ❌ Falló descarga"
            )

        time.sleep(
            PAUSA_ENTRE_IMAGENES
        )

    return guardadas


# ============================================================
# PROCESAR UNA RAMA / CATEGORÍA
# ============================================================

def procesar_rama(
    categoria_local,
    url_inicial,
):
    """
    Recorre una categoría completa mediante el paginador real.

    No asumimos:
        page=1
        page=2
        page=3

    sino que seguimos el enlace real "Siguiente".
    """

    print()
    print(
        f"   🌿 RAMA: {url_inicial}"
    )

    url_actual = agregar_items_por_pagina(
        url_inicial,
        ITEMS_POR_PAGINA,
    )

    paginas_visitadas = set()
    productos_globales_rama = set()

    total_productos = 0
    total_imagenes = 0
    numero_pagina = 1

    while url_actual:

        # ----------------------------------------------------
        # Seguridad contra loops.
        # ----------------------------------------------------

        url_clave = url_actual.rstrip("/")

        if url_clave in paginas_visitadas:

            print(
                "      🛑 Página repetida detectada. "
                "Rama detenida."
            )

            break

        paginas_visitadas.add(
            url_clave
        )

        print()
        print(
            f"      📄 Página {numero_pagina}"
        )

        print(
            f"      🔗 {url_actual}"
        )

        soup = obtener_html(
            url_actual
        )

        if not soup:

            print(
                "      ❌ No se pudo obtener "
                "esta página."
            )

            break

        # ----------------------------------------------------
        # Productos.
        # ----------------------------------------------------

        productos = extraer_productos_de_pagina(
            soup,
            url_actual,
        )

        if not productos:

            print(
                "      ℹ️ No se encontraron productos. "
                "Rama terminada."
            )

            break

        # ----------------------------------------------------
        # Detectar página repetida.
        # ----------------------------------------------------

        urls_pagina = {
            producto["url"]
            for producto in productos
        }

        nuevos_en_pagina = (
            urls_pagina
            - productos_globales_rama
        )

        if not nuevos_en_pagina:

            print(
                "      🛑 Esta página contiene únicamente "
                "productos ya vistos."
            )

            break

        print(
            f"      📦 Productos detectados: "
            f"{len(productos)}"
        )

        print(
            f"      🆕 Productos nuevos: "
            f"{len(nuevos_en_pagina)}"
        )

        # ----------------------------------------------------
        # Procesar productos.
        # ----------------------------------------------------

        for producto in productos:

            url_producto = producto["url"]

            # Producto ya procesado dentro de esta rama.
            if url_producto in productos_globales_rama:

                continue

            productos_globales_rama.add(
                url_producto
            )

            total_productos += 1

            fotos = procesar_producto(
                categoria_local,
                producto,
            )

            total_imagenes += fotos

            time.sleep(
                PAUSA_ENTRE_PRODUCTOS
            )

        # ----------------------------------------------------
        # Buscar siguiente página REAL.
        # ----------------------------------------------------

        siguiente = encontrar_siguiente_url(
            soup,
            url_actual,
        )

        if not siguiente:

            print(
                "      🏁 No existe una página siguiente. "
                "Rama terminada."
            )

            break

        # Mantener el ajuste de 96 productos.
        siguiente = agregar_items_por_pagina(
            siguiente,
            ITEMS_POR_PAGINA,
        )

        if (
            siguiente.rstrip("/")
            == url_actual.rstrip("/")
        ):

            print(
                "      🛑 El siguiente enlace apunta "
                "a la misma página. Deteniendo."
            )

            break

        url_actual = siguiente

        numero_pagina += 1

        time.sleep(
            PAUSA_ENTRE_PAGINAS
        )

    print()
    print(
        f"   ✨ Rama completada."
    )

    print(
        f"      Productos nuevos: {total_productos}"
    )

    print(
        f"      Imágenes guardadas: {total_imagenes}"
    )

    return total_productos, total_imagenes


# ============================================================
# PROCESADOR PRINCIPAL
# ============================================================

def iniciar_extractor():
    print()
    print(
        "============================================================"
    )

    print(
        "🚀 SPLANET EXTRACTOR V6"
    )

    print(
        "🐣🐥🐧 Motor de catálogo + galería completa"
    )

    print(
        "============================================================"
    )

    print()

    print(
        f"📌 Intento de productos por página: "
        f"{ITEMS_POR_PAGINA}"
    )

    print(
        "📌 La paginación se obtiene desde los enlaces "
        "reales de la tienda."
    )

    print(
        "📌 Cada producto tendrá su propia carpeta."
    )

    print(
        "📌 Todas las imágenes serán enumeradas."
    )

    print()

    total_general_productos = 0
    total_general_imagenes = 0

    # ========================================================
    # CATEGORÍAS PRINCIPALES
    # ========================================================

    for categoria_local, lista_urls in URLS_MAESTRAS.items():

        print()
        print(
            "############################################################"
        )

        print(
            f"📁 CATEGORÍA PRINCIPAL: {categoria_local}"
        )

        print(
            "############################################################"
        )

        total_categoria_productos = 0
        total_categoria_imagenes = 0

        # ----------------------------------------------------
        # Cada URL representa una rama del árbol.
        # ----------------------------------------------------

        ramas_procesadas = set()

        for url_rama in lista_urls:

            url_base_rama = url_rama.rstrip("/")

            if url_base_rama in ramas_procesadas:
                continue

            ramas_procesadas.add(
                url_base_rama
            )

            productos, imagenes = procesar_rama(
                categoria_local,
                url_rama,
            )

            total_categoria_productos += productos
            total_categoria_imagenes += imagenes

        print()
        print(
            f"🎉 CATEGORÍA TERMINADA: "
            f"{categoria_local}"
        )

        print(
            f"   📦 Productos: "
            f"{total_categoria_productos}"
        )

        print(
            f"   🖼️ Imágenes nuevas: "
            f"{total_categoria_imagenes}"
        )

        total_general_productos += (
            total_categoria_productos
        )

        total_general_imagenes += (
            total_categoria_imagenes
        )

    # ========================================================
    # FINAL
    # ========================================================

    print()
    print(
        "============================================================"
    )

    print(
        "🎉🎉🎉 EXTRACCIÓN COMPLETADA 🎉🎉🎉"
    )

    print(
        "============================================================"
    )

    print(
        f"📦 Productos procesados: "
        f"{total_general_productos}"
    )

    print(
        f"🖼️ Imágenes nuevas guardadas: "
        f"{total_general_imagenes}"
    )

    print()
    print(
        "🐣🐥🐧 ¡El catálogo debería haber quedado organizado!"
    )

    print()


# ============================================================
# PUNTO DE ENTRADA
# ============================================================

if __name__ == "__main__":
    iniciar_extractor()
