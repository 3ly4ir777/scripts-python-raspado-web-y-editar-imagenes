# ============================================================
# V7.1 — ORGANIZADOR JERÁRQUICO INTELIGENTE SPLANET
# ============================================================
#
# Entrada:
#     CATALOGO_LIMPIO
#
# Salida:
#     CATALOGO_FINAL
#
# Lógica:
#
#   Categoría sin subcategorías:
#
#       BCAA S/
#           PRODUCTO/
#
#   Categoría con subcategorías:
#
#       POST-ENTRENOS/
#           GLUTAMINA/
#               PRODUCTO/
#
#   Si una categoría padre tiene productos propios que no
#   aparecen en ninguna subcategoría:
#
#       POST-ENTRENOS/
#           INDEX/
#               PRODUCTO/
#           GLUTAMINA/
#               PRODUCTO/
#
# ============================================================

import os
import re
import shutil
import time
import unicodedata

import requests

from bs4 import BeautifulSoup

from urllib.parse import (
    urljoin,
    urlparse,
    parse_qsl,
    urlencode,
    urlunparse,
)

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# ============================================================
# CONFIGURACIÓN
# ============================================================

CARPETA_ENTRADA = "CATALOGO_LIMPIO"

CARPETA_SALIDA = "CATALOGO_FINAL"

ITEMS_POR_PAGINA = 96

PAUSA_ENTRE_PAGINAS = 1.0

INCLUIR_VARIOS = False


BASE_URL = (
    "https://tienda.splanet.com.mx/store/"
)


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": (
        "es-MX,es;q=0.9,en;q=0.8"
    ),
}


# ============================================================
# SESIÓN HTTP
# ============================================================

def crear_sesion():

    sesion = requests.Session()

    reintentos = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=1.0,
        status_forcelist=[
            429,
            500,
            502,
            503,
            504,
        ],
        allowed_methods=[
            "GET"
        ],
    )

    adaptador = HTTPAdapter(
        max_retries=reintentos
    )

    sesion.mount(
        "http://",
        adaptador
    )

    sesion.mount(
        "https://",
        adaptador
    )

    sesion.headers.update(
        HEADERS
    )

    return sesion


SESSION = crear_sesion()


# ============================================================
# ÁRBOL DE CATEGORÍAS
# ============================================================
#
# children = subcategorías directas.
#
# Si children está vacío:
#     los productos van directamente aquí.
#
# Si children tiene elementos:
#     primero se revisan los hijos.
#     solamente los productos exclusivos del padre
#     pueden terminar en INDEX.
#
# ============================================================

ARBOL_CATEGORIAS = {

    "BCAA S": {
        "url": (
            "https://tienda.splanet.com.mx/"
            "store/bcaa-s/"
        ),
        "children": {},
    },

    "COLAGENO": {
        "url": (
            "https://tienda.splanet.com.mx/"
            "store/colageno/"
        ),
        "children": {},
    },

    "CREATINA": {
        "url": (
            "https://tienda.splanet.com.mx/"
            "store/creatina/"
        ),
        "children": {},
    },

    "GANADORES DE MASA MUSCULAR": {
        "url": (
            "https://tienda.splanet.com.mx/"
            "store/ganadores-de-masa-muscular/"
        ),
        "children": {},
    },

    "POST-ENTRENOS": {
        "url": (
            "https://tienda.splanet.com.mx/"
            "store/post-entrenos/"
        ),
        "children": {

            "GLUTAMINA": {
                "url": (
                    "https://tienda.splanet.com.mx/"
                    "store/post-entrenos/glutamina/"
                ),
                "children": {},
            },

        },
    },

    "PRE-ENTRENOS": {
        "url": (
            "https://tienda.splanet.com.mx/"
            "store/pre-entrenos/"
        ),
        "children": {

            "OXIDO NITRICO": {
                "url": (
                    "https://tienda.splanet.com.mx/"
                    "store/pre-entrenos/oxido-nitrico/"
                ),
                "children": {

                    "CAPSULAS": {
                        "url": (
                            "https://tienda.splanet.com.mx/"
                            "store/pre-entrenos/"
                            "oxido-nitrico/capsulas/"
                        ),
                        "children": {},
                    },

                    "CONCENTRADOS": {
                        "url": (
                            "https://tienda.splanet.com.mx/"
                            "store/pre-entrenos/"
                            "oxido-nitrico/concentrados/"
                        ),
                        "children": {},
                    },

                    "POLVOS": {
                        "url": (
                            "https://tienda.splanet.com.mx/"
                            "store/pre-entrenos/"
                            "oxido-nitrico/polvos/"
                        ),
                        "children": {},
                    },

                },
            },

        },
    },

    "PROMOTORES": {
        "url": (
            "https://tienda.splanet.com.mx/"
            "store/promotores/"
        ),
        "children": {

            "CONSTRUCTOR MUSCULAR": {
                "url": (
                    "https://tienda.splanet.com.mx/"
                    "store/promotores/"
                    "constructor-muscular/"
                ),
                "children": {},
            },

            "PRO-H. CRECIMIENTO": {
                "url": (
                    "https://tienda.splanet.com.mx/"
                    "store/promotores/"
                    "pro-h-crecimiento/"
                ),
                "children": {},
            },

            "PRO-TESTOTERONA": {
                "url": (
                    "https://tienda.splanet.com.mx/"
                    "store/promotores/"
                    "pro-testoterona/"
                ),
                "children": {},
            },

        },
    },

    "PROTEINAS": {
        "url": (
            "https://tienda.splanet.com.mx/"
            "store/proteinas/"
        ),
        "children": {

            "BAJAS CALORIAS": {
                "url": (
                    "https://tienda.splanet.com.mx/"
                    "store/proteinas/bajas-calorias/"
                ),
                "children": {},
            },

            "CONSTRUCTOR MUSCULAR": {
                "url": (
                    "https://tienda.splanet.com.mx/"
                    "store/proteinas/"
                    "constructor-muscular/"
                ),
                "children": {},
            },

            "DE CARNE": {
                "url": (
                    "https://tienda.splanet.com.mx/"
                    "store/proteinas/de-carne/"
                ),
                "children": {},
            },

            "FORMULAS AVANZADAS DE SUERO": {
                "url": (
                    "https://tienda.splanet.com.mx/"
                    "store/proteinas/"
                    "formulas-avanzadas-de-suero/"
                ),
                "children": {},
            },

            "ISO AISLADOS DE SUERO": {
                "url": (
                    "https://tienda.splanet.com.mx/"
                    "store/proteinas/"
                    "iso-aislados-de-suero/"
                ),
                "children": {},
            },

            "LIBERACIÓN SOSTENIDA": {
                "url": (
                    "https://tienda.splanet.com.mx/"
                    "store/proteinas/"
                    "liberacion-sostenida/"
                ),
                "children": {},
            },

            "OTRAS FORMULAS": {
                "url": (
                    "https://tienda.splanet.com.mx/"
                    "store/proteinas/"
                    "otras-formulas/"
                ),
                "children": {},
            },

        },
    },

    "QUEMA GRASAS": {
        "url": (
            "https://tienda.splanet.com.mx/"
            "store/quema-grasas/"
        ),
        "children": {

            "CARNITINA": {
                "url": (
                    "https://tienda.splanet.com.mx/"
                    "store/quema-grasas/carnitina/"
                ),
                "children": {},
            },

            "DIURETICOS": {
                "url": (
                    "https://tienda.splanet.com.mx/"
                    "store/quema-grasas/diureticos/"
                ),
                "children": {},
            },

            "INHIBIDORES": {
                "url": (
                    "https://tienda.splanet.com.mx/"
                    "store/quema-grasas/inhibidores/"
                ),
                "children": {},
            },

            "TERMOGENICOS": {
                "url": (
                    "https://tienda.splanet.com.mx/"
                    "store/quema-grasas/termogenicos/"
                ),
                "children": {},
            },

        },
    },

    "VITAMINAS & MINERALES": {
        "url": (
            "https://tienda.splanet.com.mx/"
            "store/vitaminas-and-minerales/"
        ),
        "children": {

            "ANTIOXIDANTES": {
                "url": (
                    "https://tienda.splanet.com.mx/"
                    "store/vitaminas-and-minerales/"
                    "antioxidantes/"
                ),
                "children": {},
            },

            "SALUD ARTICULAR": {
                "url": (
                    "https://tienda.splanet.com.mx/"
                    "store/vitaminas-and-minerales/"
                    "salud-articular/"
                ),
                "children": {},
            },

            "VARIOS": {
                "url": (
                    "https://tienda.splanet.com.mx/"
                    "store/vitaminas-and-minerales/"
                    "varios/"
                ),
                "children": {},
            },

            "VITAMINAS": {
                "url": (
                    "https://tienda.splanet.com.mx/"
                    "store/vitaminas-and-minerales/"
                    "vitaminas/"
                ),
                "children": {},
            },

        },
    },

}


# ============================================================
# VARIOS
# ============================================================
#
# Lo dejamos separado porque tú decidiste no procesarlo.
#
# Si algún día quieres incluirlo:
#
#     INCLUIR_VARIOS = True
#
# ============================================================

ARBOL_VARIOS = {

    "url": (
        "https://tienda.splanet.com.mx/"
        "store/varios/"
    ),

    "children": {

        "ACCESORIOS": {
            "url": (
                "https://tienda.splanet.com.mx/"
                "store/varios/accesorios/"
            ),
            "children": {

                "PARA LA PIEL": {
                    "url": (
                        "https://tienda.splanet.com.mx/"
                        "store/varios/accesorios/"
                        "para-la-piel/"
                    ),
                    "children": {},
                },

                "SHAKERS": {
                    "url": (
                        "https://tienda.splanet.com.mx/"
                        "store/varios/accesorios/"
                        "shakers/"
                    ),
                    "children": {},
                },

            },
        },

        "ACIDOS GRASOS": {
            "url": (
                "https://tienda.splanet.com.mx/"
                "store/varios/acidos-grasos/"
            ),
            "children": {

                "CLA": {
                    "url": (
                        "https://tienda.splanet.com.mx/"
                        "store/varios/acidos-grasos/"
                        "cla/"
                    ),
                    "children": {},
                },

                "MCT": {
                    "url": (
                        "https://tienda.splanet.com.mx/"
                        "store/varios/acidos-grasos/"
                        "mct/"
                    ),
                    "children": {},
                },

                "OMEGA 3-6-9": {
                    "url": (
                        "https://tienda.splanet.com.mx/"
                        "store/varios/acidos-grasos/"
                        "omega-3-6-9/"
                    ),
                    "children": {},
                },

            },
        },

        "ALTO RENDIMIENTO": {
            "url": (
                "https://tienda.splanet.com.mx/"
                "store/varios/alto-rendimiento/"
            ),
            "children": {

                "INTRA-ENTRENAMIENTO": {
                    "url": (
                        "https://tienda.splanet.com.mx/"
                        "store/varios/"
                        "alto-rendimiento/"
                        "intra-entrenamiento/"
                    ),
                    "children": {},
                },

            },
        },

        "AMINOÁCIDOS": {
            "url": (
                "https://tienda.splanet.com.mx/"
                "store/varios/aminoacidos/"
            ),
            "children": {

                "AMINO ESPECIFICOS": {
                    "url": (
                        "https://tienda.splanet.com.mx/"
                        "store/varios/aminoacidos/"
                        "amino-especificos/"
                    ),
                    "children": {},
                },

                "AMINO LIQUIDOS": {
                    "url": (
                        "https://tienda.splanet.com.mx/"
                        "store/varios/aminoacidos/"
                        "amino-liquidos/"
                    ),
                    "children": {},
                },

            },
        },

        "BARRAS": {
            "url": (
                "https://tienda.splanet.com.mx/"
                "store/varios/barras/"
            ),
            "children": {},
        },

        "ESPECIALES": {
            "url": (
                "https://tienda.splanet.com.mx/"
                "store/varios/especiales/"
            ),
            "children": {

                "OFERTAS Y PROMOCIONES": {
                    "url": (
                        "https://tienda.splanet.com.mx/"
                        "store/varios/especiales/"
                        "ofertas-y-promociones/"
                    ),
                    "children": {},
                },

            },
        },

        "PARA ELLAS": {
            "url": (
                "https://tienda.splanet.com.mx/"
                "store/varios/para-ellas/"
            ),
            "children": {

                "PROTEÍNAS": {
                    "url": (
                        "https://tienda.splanet.com.mx/"
                        "store/varios/para-ellas/"
                        "proteinas/"
                    ),
                    "children": {},
                },

                "QUEMADORES": {
                    "url": (
                        "https://tienda.splanet.com.mx/"
                        "store/varios/para-ellas/"
                        "quemadores/"
                    ),
                    "children": {},
                },

            },
        },

    },
}


# ============================================================
# UTILIDADES DE TEXTO
# ============================================================

def normalizar_nombre(texto):
    """
    Convierte nombres para poder comparar:

        Proteína X
        PROTEINA X
        proteína x

    como la misma cosa.
    """

    if not texto:
        return ""

    texto = str(texto)

    texto = unicodedata.normalize(
        "NFKD",
        texto
    )

    texto = "".join(
        caracter
        for caracter in texto
        if not unicodedata.combining(
            caracter
        )
    )

    texto = texto.upper()

    # Ampersand y variantes.
    texto = texto.replace(
        "&",
        "Y"
    )

    # Guiones / underscores.
    texto = texto.replace(
        "_",
        " "
    )

    texto = texto.replace(
        "-",
        " "
    )

    # Todo lo que no sea alfanumérico
    # se convierte en espacio.
    texto = re.sub(
        r"[^A-Z0-9]+",
        " ",
        texto
    )

    texto = " ".join(
        texto.split()
    )

    return texto


def limpiar_nombre_carpeta(texto):
    """
    Limpia nombres para Windows.
    """

    if not texto:
        return ""

    texto = str(texto).strip()

    texto = re.sub(
        r'[\\/*?:"<>|]',
        "",
        texto
    )

    texto = texto.rstrip(
        " ."
    )

    return texto


# ============================================================
# ITEMS POR PÁGINA
# ============================================================

def agregar_items_por_pagina(
    url,
    cantidad=96
):

    partes = urlparse(
        url
    )

    parametros = parse_qsl(
        partes.query,
        keep_blank_values=True
    )

    nuevos = []

    encontrado = False

    for clave, valor in parametros:

        if clave == "items_per_page":

            if not encontrado:

                nuevos.append(
                    (
                        "items_per_page",
                        str(cantidad)
                    )
                )

                encontrado = True

        else:

            nuevos.append(
                (
                    clave,
                    valor
                )
            )

    if not encontrado:

        nuevos.append(
            (
                "items_per_page",
                str(cantidad)
            )
        )

    nueva_query = urlencode(
        nuevos
    )

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
# OBTENER HTML
# ============================================================

def obtener_html(url):

    try:

        respuesta = SESSION.get(
            url,
            timeout=25
        )

        if respuesta.status_code == 200:

            return BeautifulSoup(
                respuesta.text,
                "html.parser"
            )

        print(
            f"      ⚠️ HTTP "
            f"{respuesta.status_code}"
        )

    except requests.RequestException as error:

        print(
            f"      ❌ Error: {error}"
        )

    return None


# ============================================================
# DETECTAR TARJETAS
# ============================================================

def obtener_tarjetas_producto(
    soup
):

    selectores = [

        ".ty-grid-list__item",

        ".grid-list__item",

        ".product-cell",

        "[class*='product-grid']",

        ".ty-column",

    ]

    tarjetas = []

    for selector in selectores:

        encontradas = soup.select(
            selector
        )

        tarjetas.extend(
            encontradas
        )

    resultado = []

    vistos = set()

    for tarjeta in tarjetas:

        identificador = id(
            tarjeta
        )

        if identificador not in vistos:

            vistos.add(
                identificador
            )

            resultado.append(
                tarjeta
            )

    return resultado


# ============================================================
# URL DE PRODUCTO
# ============================================================

def parece_producto_url(
    url
):

    if not url:
        return False

    url_lower = url.lower()

    if "/store/" not in url_lower:
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

    for elemento in basura:

        if elemento in url_lower:

            return False

    return True


def extraer_url_producto(
    tarjeta,
    url_base
):

    imagen = tarjeta.find(
        "img"
    )

    if imagen:

        padre = imagen.parent

        if (
            padre
            and padre.name == "a"
        ):

            href = padre.get(
                "href"
            )

            if href:

                url = urljoin(
                    url_base,
                    href
                )

                if parece_producto_url(
                    url
                ):

                    return url

    for enlace in tarjeta.find_all(
        "a",
        href=True
    ):

        href = enlace.get(
            "href"
        )

        url = urljoin(
            url_base,
            href
        )

        if parece_producto_url(
            url
        ):

            return url

    return None


# ============================================================
# NOMBRE DE PRODUCTO
# ============================================================

def extraer_nombre_producto(
    tarjeta
):

    imagen = tarjeta.find(
        "img"
    )

    if imagen:

        alt = imagen.get(
            "alt",
            ""
        ).strip()

        if len(alt) >= 3:

            return alt

        title = imagen.get(
            "title",
            ""
        ).strip()

        if len(title) >= 3:

            return title

    selectores = [

        ".product-title",

        ".ty-grid-list__item-name",

        ".ty-grid-list__item-name a",

        "[class*='product-title']",

        "[class*='item-name']",

    ]

    for selector in selectores:

        elemento = tarjeta.select_one(
            selector
        )

        if elemento:

            texto = elemento.get_text(
                " ",
                strip=True
            )

            if len(texto) >= 3:

                return texto

    for enlace in tarjeta.find_all(
        "a",
        href=True
    ):

        texto = enlace.get_text(
            " ",
            strip=True
        )

        if len(texto) >= 3:

            return texto

    return ""


# ============================================================
# PRODUCTOS DE UNA PÁGINA
# ============================================================

def extraer_productos_pagina(
    soup,
    url_base
):

    tarjetas = obtener_tarjetas_producto(
        soup
    )

    productos = []

    urls_vistas = set()

    for tarjeta in tarjetas:

        url_producto = (
            extraer_url_producto(
                tarjeta,
                url_base
            )
        )

        if not url_producto:
            continue

        url_producto = (
            url_producto
            .split("#")[0]
        )

        if url_producto in urls_vistas:
            continue

        nombre = (
            extraer_nombre_producto(
                tarjeta
            )
        )

        nombre = nombre.strip()

        if not nombre:
            continue

        clave = normalizar_nombre(
            nombre
        )

        if not clave:
            continue

        urls_vistas.add(
            url_producto
        )

        productos.append(
            {
                "nombre": nombre,
                "clave": clave,
                "url": url_producto,
            }
        )

    return productos


# ============================================================
# SIGUIENTE PÁGINA
# ============================================================

def encontrar_siguiente(
    soup,
    url_actual
):

    # rel="next"
    for enlace in soup.find_all(
        "a",
        href=True
    ):

        rel = enlace.get(
            "rel"
        )

        if rel:

            if isinstance(
                rel,
                list
            ):

                rel_texto = (
                    " ".join(rel)
                    .lower()
                )

            else:

                rel_texto = str(
                    rel
                ).lower()

            if "next" in rel_texto:

                return urljoin(
                    url_actual,
                    enlace["href"]
                )

    # Texto "Siguiente"
    for enlace in soup.find_all(
        "a",
        href=True
    ):

        texto = normalizar_nombre(
            enlace.get_text(
                " ",
                strip=True
            )
        )

        if texto == "SIGUIENTE":

            return urljoin(
                url_actual,
                enlace["href"]
            )

    # Fallback page-N
    match = re.search(
        r"/page-(\d+)/?$",
        urlparse(
            url_actual
        ).path
    )

    if match:

        numero = int(
            match.group(1)
        )

    else:

        numero = 1

    siguiente_numero = (
        numero + 1
    )

    patron = re.compile(
        rf"/page-{siguiente_numero}/?$",
        re.IGNORECASE
    )

    for enlace in soup.find_all(
        "a",
        href=True
    ):

        candidata = urljoin(
            url_actual,
            enlace["href"]
        )

        ruta = urlparse(
            candidata
        ).path

        if patron.search(
            ruta
        ):

            return candidata

    return None


# ============================================================
# OBTENER TODOS LOS PRODUCTOS DE UNA CATEGORÍA
# ============================================================

def obtener_productos_categoria(
    url_inicial
):

    todos = {}

    url_actual = agregar_items_por_pagina(
        url_inicial,
        ITEMS_POR_PAGINA
    )

    paginas_vistas = set()

    numero_pagina = 1

    while url_actual:

        clave_url = (
            url_actual.rstrip("/")
        )

        if clave_url in paginas_vistas:

            print(
                "      🛑 Página repetida."
            )

            break

        paginas_vistas.add(
            clave_url
        )

        print(
            f"      📄 Página "
            f"{numero_pagina}: "
            f"{url_actual}"
        )

        soup = obtener_html(
            url_actual
        )

        if not soup:

            break

        productos = (
            extraer_productos_pagina(
                soup,
                url_actual
            )
        )

        nuevos = 0

        for producto in productos:

            clave = producto[
                "clave"
            ]

            if clave not in todos:

                todos[clave] = (
                    producto
                )

                nuevos += 1

        print(
            f"         📦 "
            f"{len(productos)} encontrados"
        )

        print(
            f"         🆕 "
            f"{nuevos} nuevos"
        )

        siguiente = (
            encontrar_siguiente(
                soup,
                url_actual
            )
        )

        if not siguiente:

            break

        siguiente = (
            agregar_items_por_pagina(
                siguiente,
                ITEMS_POR_PAGINA
            )
        )

        if (
            siguiente.rstrip("/")
            == url_actual.rstrip("/")
        ):

            break

        url_actual = siguiente

        numero_pagina += 1

        time.sleep(
            PAUSA_ENTRE_PAGINAS
        )

    return todos


# ============================================================
# ESCANEAR PRODUCTOS LOCALES
# ============================================================

def carpeta_contiene_imagenes(
    carpeta
):

    extensiones = (
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
        ".bmp",
        ".tif",
        ".tiff",
    )

    try:

        for elemento in os.listdir(
            carpeta
        ):

            ruta = os.path.join(
                carpeta,
                elemento
            )

            if os.path.isfile(
                ruta
            ):

                if elemento.lower().endswith(
                    extensiones
                ):

                    return True

    except OSError:

        pass

    return False


def obtener_productos_locales(
    carpeta
):

    productos = {}

    if not os.path.isdir(
        carpeta
    ):

        return productos

    for raiz, directorios, archivos in os.walk(
        carpeta
    ):

        # ----------------------------------------------------
        # Solo consideramos carpetas que contienen imágenes.
        # ----------------------------------------------------

        tiene_imagen = any(
            archivo.lower().endswith(
                (
                    ".png",
                    ".jpg",
                    ".jpeg",
                    ".webp",
                    ".bmp",
                    ".tif",
                    ".tiff",
                )
            )
            for archivo in archivos
        )

        if not tiene_imagen:

            continue

        nombre = os.path.basename(
            raiz
        )

        # Ignorar carpetas especiales.
        if nombre.startswith(
            "_"
        ):

            continue

        clave = normalizar_nombre(
            nombre
        )

        if not clave:

            continue

        if clave in productos:

            print()
            print(
                "⚠️ PRODUCTO LOCAL DUPLICADO:"
            )

            print(
                f"   {nombre}"
            )

            print(
                f"   {raiz}"
            )

            continue

        productos[clave] = (
            nombre,
            raiz
        )

    return productos


# ============================================================
# COPIAR PRODUCTO
# ============================================================

def copiar_producto(
    origen,
    destino
):

    os.makedirs(
        destino,
        exist_ok=True
    )

    copiados = 0

    for elemento in os.listdir(
        origen
    ):

        origen_elemento = os.path.join(
            origen,
            elemento
        )

        destino_elemento = os.path.join(
            destino,
            elemento
        )

        if os.path.isdir(
            origen_elemento
        ):

            copiar_producto(
                origen_elemento,
                destino_elemento
            )

            continue

        if os.path.isfile(
            origen_elemento
        ):

            # ------------------------------------------------
            # Si ya existe, no lo reemplazamos.
            # ------------------------------------------------

            if os.path.exists(
                destino_elemento
            ):

                continue

            shutil.copy2(
                origen_elemento,
                destino_elemento
            )

            copiados += 1

    return copiados


# ============================================================
# CONSTRUIR ÍNDICE DEL ÁRBOL
# ============================================================

def construir_indice_nodo(
    nombre,
    nodo,
    cache
):

    url = nodo["url"]

    hijos = nodo.get(
        "children",
        {}
    )

    print()
    print(
        "🌿 " + nombre
    )

    print(
        f"   🔎 {url}"
    )

    # --------------------------------------------------------
    # Obtener productos del nodo.
    # --------------------------------------------------------

    productos_padre = (
        obtener_productos_categoria(
            url
        )
    )

    # --------------------------------------------------------
    # Procesar hijos.
    # --------------------------------------------------------

    resultados_hijos = {}

    productos_de_hijos = set()

    for nombre_hijo, nodo_hijo in hijos.items():

        resultado_hijo = (
            construir_indice_nodo(
                nombre_hijo,
                nodo_hijo,
                cache
            )
        )

        resultados_hijos[
            nombre_hijo
        ] = resultado_hijo

        productos_de_hijos.update(
            resultado_hijo[
                "todos_los_productos"
            ]
        )

    # --------------------------------------------------------
    # Productos exclusivos del padre.
    #
    # Si el padre muestra todo lo que tienen sus hijos,
    # esta diferencia será vacía.
    # --------------------------------------------------------

    exclusivos = (
        set(productos_padre.keys())
        - productos_de_hijos
    )

    # --------------------------------------------------------
    # Si NO tiene hijos:
    #
    # Todos sus productos son propios.
    # --------------------------------------------------------

    if not hijos:

        exclusivos = set(
            productos_padre.keys()
        )

    print(
        f"   📦 Total en categoría: "
        f"{len(productos_padre)}"
    )

    if hijos:

        print(
            f"   🌱 Productos de hijos: "
            f"{len(productos_de_hijos)}"
        )

        print(
            f"   📌 Exclusivos del padre: "
            f"{len(exclusivos)}"
        )

    return {
        "nombre": nombre,
        "url": url,
        "productos": productos_padre,
        "hijos": resultados_hijos,
        "exclusivos": exclusivos,
        "todos_los_productos": (
            set(productos_padre.keys())
            | productos_de_hijos
        ),
    }


# ============================================================
# COPIAR ÁRBOL
# ============================================================

def copiar_arbol(
    nombre,
    resultado,
    ruta_padre,
    locales,
    estadisticas,
    es_categoria_raiz=False
):

    ruta_actual = os.path.join(
        ruta_padre,
        limpiar_nombre_carpeta(
            nombre
        )
    )

    os.makedirs(
        ruta_actual,
        exist_ok=True
    )

    hijos = resultado[
        "hijos"
    ]

    exclusivos = resultado[
        "exclusivos"
    ]

    # ========================================================
    # CASO 1:
    # NODO SIN HIJOS
    # ========================================================

    if not hijos:

        for clave in sorted(
            exclusivos
        ):

            if clave not in locales:

                estadisticas[
                    "sin_coincidencia"
                ].add(
                    clave
                )

                continue

            nombre_local, ruta_local = (
                locales[clave]
            )

            destino = os.path.join(
                ruta_actual,
                limpiar_nombre_carpeta(
                    nombre_local
                )
            )

            print(
                f"   📦 {nombre}/"
                f"{nombre_local}"
            )

            cantidad = copiar_producto(
                ruta_local,
                destino
            )

            estadisticas[
                "productos"
            ] += 1

            estadisticas[
                "archivos"
            ] += cantidad

            estadisticas[
                "encontrados"
            ].add(
                clave
            )

        return

    # ========================================================
    # CASO 2:
    # NODO CON HIJOS
    # ========================================================

    # --------------------------------------------------------
    # Productos exclusivos del padre.
    #
    # SOLO aquí creamos INDEX.
    #
    # --------------------------------------------------------

    if exclusivos:

        ruta_index = os.path.join(
            ruta_actual,
            "INDEX"
        )

        os.makedirs(
            ruta_index,
            exist_ok=True
        )

        print()
        print(
            f"   📌 {nombre}/INDEX"
        )

        for clave in sorted(
            exclusivos
        ):

            if clave not in locales:

                estadisticas[
                    "sin_coincidencia"
                ].add(
                    clave
                )

                continue

            nombre_local, ruta_local = (
                locales[clave]
            )

            destino = os.path.join(
                ruta_index,
                limpiar_nombre_carpeta(
                    nombre_local
                )
            )

            print(
                f"      📦 "
                f"{nombre_local}"
            )

            cantidad = copiar_producto(
                ruta_local,
                destino
            )

            estadisticas[
                "productos"
            ] += 1

            estadisticas[
                "archivos"
            ] += cantidad

            estadisticas[
                "encontrados"
            ].add(
                clave
            )

    # --------------------------------------------------------
    # Hijos.
    # --------------------------------------------------------

    for nombre_hijo, resultado_hijo in (
        hijos.items()
    ):

        copiar_arbol(
            nombre_hijo,
            resultado_hijo,
            ruta_actual,
            locales,
            estadisticas,
            False
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print(
        "=" * 70
    )

    print(
        "🐣 SPLANET V7.1 — "
        "ORGANIZADOR JERÁRQUICO"
    )

    print(
        "=" * 70
    )

    print()

    print(
        f"📂 Entrada: "
        f"{CARPETA_ENTRADA}"
    )

    print(
        f"📁 Salida: "
        f"{CARPETA_SALIDA}"
    )

    print(
        f"📌 Productos por página: "
        f"{ITEMS_POR_PAGINA}"
    )

    print()

    # ========================================================
    # COMPROBAR ENTRADA
    # ========================================================

    if not os.path.isdir(
        CARPETA_ENTRADA
    ):

        print(
            f"❌ No existe: "
            f"{CARPETA_ENTRADA}"
        )

        print()

        print(
            "Asegúrate de que V8 ya creó "
            "CATALOGO_LIMPIO."
        )

        return

    # ========================================================
    # ESCANEAR LOCALES
    # ========================================================

    print(
        "📂 Escaneando imágenes limpiadas..."
    )

    locales = (
        obtener_productos_locales(
            CARPETA_ENTRADA
        )
    )

    print(
        f"📦 Productos locales encontrados: "
        f"{len(locales)}"
    )

    # ========================================================
    # SALIDA
    # ========================================================

    os.makedirs(
        CARPETA_SALIDA,
        exist_ok=True
    )

    # ========================================================
    # CONSTRUIR ÍNDICE
    # ========================================================

    print()
    print(
        "=" * 70
    )

    print(
        "🌐 CONSULTANDO CATEGORÍAS"
    )

    print(
        "=" * 70
    )

    indice_general = {}

    for nombre, nodo in (
        ARBOL_CATEGORIAS.items()
    ):

        indice_general[
            nombre
        ] = construir_indice_nodo(
            nombre,
            nodo,
            {}
        )

    # ========================================================
    # VARIOS
    # ========================================================

    if INCLUIR_VARIOS:

        print()
        print(
            "🌿 VARIOS"
        )

        indice_general[
            "VARIOS"
        ] = construir_indice_nodo(
            "VARIOS",
            ARBOL_VARIOS,
            {}
        )

    else:

        print()
        print(
            "⏭️ VARIOS omitido "
            "(INCLUIR_VARIOS = False)"
        )

    # ========================================================
    # COPIAR
    # ========================================================

    print()
    print(
        "=" * 70
    )

    print(
        "📁 ORGANIZANDO CATÁLOGO"
    )

    print(
        "=" * 70
    )

    estadisticas = {

        "productos": 0,

        "archivos": 0,

        "encontrados": set(),

        "sin_coincidencia": set(),

    }

    for nombre, resultado in (
        indice_general.items()
    ):

        print()
        print(
            f"📁 {nombre}"
        )

        copiar_arbol(
            nombre,
            resultado,
            CARPETA_SALIDA,
            locales,
            estadisticas,
            True
        )

    # ========================================================
    # PRODUCTOS LOCALES QUE NO APARECIERON
    # ========================================================

    no_encontrados = (
        set(locales.keys())
        - estadisticas[
            "encontrados"
        ]
    )

    # ========================================================
    # REPORTE
    # ========================================================

    print()
    print(
        "=" * 70
    )

    print(
        "📊 RESUMEN"
    )

    print(
        "=" * 70
    )

    print(
        f"📦 Productos organizados: "
        f"{estadisticas['productos']}"
    )

    print(
        f"🖼️ Archivos copiados: "
        f"{estadisticas['archivos']}"
    )

    print(
        f"⚠️ Productos sin coincidencia: "
        f"{len(no_encontrados)}"
    )

    if no_encontrados:

        print()

        print(
            "⚠️ Productos que no se pudieron "
            "ubicar:"
        )

        for clave in sorted(
            no_encontrados
        ):

            nombre_local, ruta_local = (
                locales[clave]
            )

            print(
                f"   ⚠️ {nombre_local}"
            )

            print(
                f"      {ruta_local}"
            )

        # ----------------------------------------------------
        # Copiar los no encontrados a revisión.
        # ----------------------------------------------------

        carpeta_revision = os.path.join(
            CARPETA_SALIDA,
            "_REVISION_V7"
        )

        os.makedirs(
            carpeta_revision,
            exist_ok=True
        )

        print()

        print(
            "📋 Copiando no encontrados "
            "a _REVISION_V7..."
        )

        for clave in sorted(
            no_encontrados
        ):

            nombre_local, ruta_local = (
                locales[clave]
            )

            destino = os.path.join(
                carpeta_revision,
                limpiar_nombre_carpeta(
                    nombre_local
                )
            )

            copiar_producto(
                ruta_local,
                destino
            )

    else:

        print()
        print(
            "🎉 ¡Todos los productos "
            "tuvieron coincidencia!"
        )

    # ========================================================
    # FINAL
    # ========================================================

    print()
    print(
        "=" * 70
    )

    print(
        "🎉 V7.1 TERMINADO"
    )

    print(
        "=" * 70
    )

    print()
    print(
        f"📁 Resultado: "
        f"{CARPETA_SALIDA}"
    )

    print()
    print(
        "👉 Los originales de CATALOGO_LIMPIO "
        "siguen intactos."
    )

    print()
    print(
        "🐣🐥🐧 ¡Organizador terminado!"
    )


# ============================================================
# PUNTO DE ENTRADA
# ============================================================

if __name__ == "__main__":

    main()