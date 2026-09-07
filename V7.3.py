# ============================================================
# V7.3 — ORGANIZADOR JERÁRQUICO SIN DUPLICADOS SPLANET
# ============================================================
#
# ENTRADA:
#     CATALOGO_LIMPIO
#
# SALIDA:
#     CATALOGO_FINAL_V73
#
# OBJETIVO PRINCIPAL:
#
#     CADA PRODUCTO LOCAL SE COPIA UNA SOLA VEZ.
#
# Estrategia:
#
# 1. Lee el árbol real de categorías.
# 2. Consulta las categorías y subcategorías.
# 3. Las hojas son las ubicaciones canónicas.
# 4. Los padres solamente conservan productos exclusivos.
# 5. Los productos exclusivos del padre van a INDEX.
# 6. Usa la misma limpieza de nombres compatible con V6.
# 7. Usa coincidencia flexible como segundo intento.
# 8. Detecta duplicados locales.
# 9. Detecta un producto apareciendo en varias categorías.
# 10. Un producto jamás se copia dos veces.
# 11. Crea MANIFEST_V73.csv.
# 12. Crea _REVISION_V73 para los no encontrados.
#
# CATALOGO_LIMPIO permanece intacto.
#
# ============================================================

import os
import re
import csv
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

# IMPORTANTE:
# No usamos CATALOGO_FINAL para evitar mezclar V7.2 con V7.3.
CARPETA_SALIDA = "CATALOGO_FINAL_V73"

CARPETA_REVISION = "_REVISION_V73"

MANIFEST = "MANIFEST_V73.csv"

ITEMS_POR_PAGINA = 96

PAUSA_ENTRE_PAGINAS = 1.0

# VARIOS permanece fuera.
INCLUIR_VARIOS = False


# ============================================================
# HEADERS
# ============================================================

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
# ÁRBOL DE CATEGORÍAS
# ============================================================

ARBOL_CATEGORIAS = {

    "BCAA S": {
        "url": "https://tienda.splanet.com.mx/store/bcaa-s/",
        "children": {},
    },

    "COLAGENO": {
        "url": "https://tienda.splanet.com.mx/store/colageno/",
        "children": {},
    },

    "CREATINA": {
        "url": "https://tienda.splanet.com.mx/store/creatina/",
        "children": {},
    },

    "GANADORES DE MASA MUSCULAR": {
        "url": (
            "https://tienda.splanet.com.mx/store/"
            "ganadores-de-masa-muscular/"
        ),
        "children": {},
    },

    "POST-ENTRENOS": {
        "url": (
            "https://tienda.splanet.com.mx/store/"
            "post-entrenos/"
        ),
        "children": {

            "GLUTAMINA": {
                "url": (
                    "https://tienda.splanet.com.mx/store/"
                    "post-entrenos/glutamina/"
                ),
                "children": {},
            },

        },
    },

    "PRE-ENTRENOS": {
        "url": (
            "https://tienda.splanet.com.mx/store/"
            "pre-entrenos/"
        ),
        "children": {

            "OXIDO NITRICO": {
                "url": (
                    "https://tienda.splanet.com.mx/store/"
                    "pre-entrenos/oxido-nitrico/"
                ),
                "children": {

                    "CAPSULAS": {
                        "url": (
                            "https://tienda.splanet.com.mx/store/"
                            "pre-entrenos/oxido-nitrico/"
                            "capsulas/"
                        ),
                        "children": {},
                    },

                    "CONCENTRADOS": {
                        "url": (
                            "https://tienda.splanet.com.mx/store/"
                            "pre-entrenos/oxido-nitrico/"
                            "concentrados/"
                        ),
                        "children": {},
                    },

                    "POLVOS": {
                        "url": (
                            "https://tienda.splanet.com.mx/store/"
                            "pre-entrenos/oxido-nitrico/"
                            "polvos/"
                        ),
                        "children": {},
                    },

                },
            },

        },
    },

    "PROMOTORES": {
        "url": (
            "https://tienda.splanet.com.mx/store/"
            "promotores/"
        ),
        "children": {

            "CONSTRUCTOR MUSCULAR": {
                "url": (
                    "https://tienda.splanet.com.mx/store/"
                    "promotores/constructor-muscular/"
                ),
                "children": {},
            },

            "PRO-H. CRECIMIENTO": {
                "url": (
                    "https://tienda.splanet.com.mx/store/"
                    "promotores/pro-h-crecimiento/"
                ),
                "children": {},
            },

            "PRO-TESTOTERONA": {
                "url": (
                    "https://tienda.splanet.com.mx/store/"
                    "promotores/pro-testoterona/"
                ),
                "children": {},
            },

        },
    },

    "PROTEINAS": {
        "url": (
            "https://tienda.splanet.com.mx/store/"
            "proteinas/"
        ),
        "children": {

            "BAJAS CALORIAS": {
                "url": (
                    "https://tienda.splanet.com.mx/store/"
                    "proteinas/bajas-calorias/"
                ),
                "children": {},
            },

            "CONSTRUCTOR MUSCULAR": {
                "url": (
                    "https://tienda.splanet.com.mx/store/"
                    "proteinas/constructor-muscular/"
                ),
                "children": {},
            },

            "DE CARNE": {
                "url": (
                    "https://tienda.splanet.com.mx/store/"
                    "proteinas/de-carne/"
                ),
                "children": {},
            },

            "FORMULAS AVANZADAS DE SUERO": {
                "url": (
                    "https://tienda.splanet.com.mx/store/"
                    "proteinas/"
                    "formulas-avanzadas-de-suero/"
                ),
                "children": {},
            },

            "ISO AISLADOS DE SUERO": {
                "url": (
                    "https://tienda.splanet.com.mx/store/"
                    "proteinas/"
                    "iso-aislados-de-suero/"
                ),
                "children": {},
            },

            "LIBERACIÓN SOSTENIDA": {
                "url": (
                    "https://tienda.splanet.com.mx/store/"
                    "proteinas/"
                    "liberacion-sostenida/"
                ),
                "children": {},
            },

            "OTRAS FORMULAS": {
                "url": (
                    "https://tienda.splanet.com.mx/store/"
                    "proteinas/"
                    "otras-formulas/"
                ),
                "children": {},
            },

        },
    },

    "QUEMA GRASAS": {
        "url": (
            "https://tienda.splanet.com.mx/store/"
            "quema-grasas/"
        ),
        "children": {

            "CARNITINA": {
                "url": (
                    "https://tienda.splanet.com.mx/store/"
                    "quema-grasas/carnitina/"
                ),
                "children": {},
            },

            "DIURETICOS": {
                "url": (
                    "https://tienda.splanet.com.mx/store/"
                    "quema-grasas/diureticos/"
                ),
                "children": {},
            },

            "INHIBIDORES": {
                "url": (
                    "https://tienda.splanet.com.mx/store/"
                    "quema-grasas/inhibidores/"
                ),
                "children": {},
            },

            "TERMOGENICOS": {
                "url": (
                    "https://tienda.splanet.com.mx/store/"
                    "quema-grasas/termogenicos/"
                ),
                "children": {},
            },

        },
    },

    "VITAMINAS & MINERALES": {
        "url": (
            "https://tienda.splanet.com.mx/store/"
            "vitaminas-and-minerales/"
        ),
        "children": {

            "ANTIOXIDANTES": {
                "url": (
                    "https://tienda.splanet.com.mx/store/"
                    "vitaminas-and-minerales/"
                    "antioxidantes/"
                ),
                "children": {},
            },

            "SALUD ARTICULAR": {
                "url": (
                    "https://tienda.splanet.com.mx/store/"
                    "vitaminas-and-minerales/"
                    "salud-articular/"
                ),
                "children": {},
            },

            "VARIOS": {
                "url": (
                    "https://tienda.splanet.com.mx/store/"
                    "vitaminas-and-minerales/"
                    "varios/"
                ),
                "children": {},
            },

            "VITAMINAS": {
                "url": (
                    "https://tienda.splanet.com.mx/store/"
                    "vitaminas-and-minerales/"
                    "vitaminas/"
                ),
                "children": {},
            },

        },
    },

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
            "GET",
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
# LIMPIEZA COMPATIBLE CON V6
# ============================================================

def limpiar_nombre_v6(texto):
    """
    Misma filosofía usada por V6 para los nombres locales.

    - strip
    - MAYÚSCULAS
    - elimina caracteres inválidos de Windows
    - compacta espacios
    - protege nombres reservados
    - elimina puntos/espacios finales
    """

    if not texto:
        return ""

    texto = str(texto).strip()

    texto = texto.upper()

    texto = re.sub(
        r'[\\/*?:"<>|]',
        "",
        texto
    )

    texto = " ".join(
        texto.split()
    )

    reservados = {
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

    texto = texto.rstrip(
        " ."
    )

    if texto in reservados:
        texto = f"_{texto}_"

    return texto


# ============================================================
# CLAVE FLEXIBLE
# ============================================================

def normalizar_nombre_flexible(texto):
    """
    Segunda capa de comparación.

    Permite considerar equivalentes cosas como:

        PROTEÍNA X
        PROTEINA X
        proteina-x
        PROTEINA_X
        PROTEINA / X
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
        if not unicodedata.combining(caracter)
    )

    texto = texto.upper()

    texto = texto.replace(
        "&",
        " Y "
    )

    texto = texto.replace(
        "_",
        " "
    )

    texto = texto.replace(
        "-",
        " "
    )

    texto = re.sub(
        r"[^A-Z0-9]+",
        " ",
        texto
    )

    return " ".join(
        texto.split()
    ).strip()


# ============================================================
# ITEMS POR PÁGINA
# ============================================================

def agregar_items_por_pagina(
    url,
    cantidad=96,
):

    partes = urlparse(
        url
    )

    parametros = parse_qsl(
        partes.query,
        keep_blank_values=True,
    )

    resultado = []

    encontrado = False

    for clave, valor in parametros:

        if clave == "items_per_page":

            if not encontrado:

                resultado.append(
                    (
                        "items_per_page",
                        str(cantidad),
                    )
                )

                encontrado = True

        else:

            resultado.append(
                (
                    clave,
                    valor,
                )
            )

    if not encontrado:

        resultado.append(
            (
                "items_per_page",
                str(cantidad),
            )
        )

    return urlunparse(
        (
            partes.scheme,
            partes.netloc,
            partes.path,
            partes.params,
            urlencode(resultado),
            partes.fragment,
        )
    )


# ============================================================
# HTML
# ============================================================

def obtener_html(url):

    try:

        respuesta = SESSION.get(
            url,
            timeout=25,
        )

        if respuesta.status_code == 200:

            return BeautifulSoup(
                respuesta.text,
                "html.parser",
            )

        print(
            f"      ⚠️ HTTP "
            f"{respuesta.status_code}: "
            f"{url}"
        )

    except requests.RequestException as error:

        print(
            f"      ❌ Error HTTP: "
            f"{error}"
        )

    return None


# ============================================================
# SIGUIENTE PÁGINA
# ============================================================

def siguiente_pagina(
    soup,
    url_actual,
):

    # --------------------------------------------------------
    # rel="next"
    # --------------------------------------------------------

    for enlace in soup.find_all(
        "a",
        href=True,
    ):

        rel = enlace.get(
            "rel",
            [],
        )

        if isinstance(
            rel,
            list,
        ):

            rel = " ".join(
                rel
            )

        if "next" in str(
            rel
        ).lower():

            return urljoin(
                url_actual,
                enlace["href"],
            )

    # --------------------------------------------------------
    # Texto SIGUIENTE
    # --------------------------------------------------------

    for enlace in soup.find_all(
        "a",
        href=True,
    ):

        texto = normalizar_nombre_flexible(
            enlace.get_text(
                " ",
                strip=True,
            )
        )

        if texto == "SIGUIENTE":

            return urljoin(
                url_actual,
                enlace["href"],
            )

    # --------------------------------------------------------
    # Fallback /page-N/
    # --------------------------------------------------------

    match = re.search(
        r"/page-(\d+)/?$",
        urlparse(
            url_actual
        ).path,
    )

    if match:

        siguiente = (
            int(
                match.group(1)
            )
            + 1
        )

    else:

        siguiente = 2

    patron = re.compile(
        rf"/page-{siguiente}/?$",
        re.IGNORECASE,
    )

    for enlace in soup.find_all(
        "a",
        href=True,
    ):

        candidato = urljoin(
            url_actual,
            enlace["href"],
        )

        ruta = urlparse(
            candidato
        ).path

        if patron.search(
            ruta
        ):

            return candidato

    return None


# ============================================================
# EXTRAER URL DE PRODUCTO
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
    ]

    for elemento in basura:

        if elemento in url_lower:

            return False

    return True


def extraer_url_producto(
    tarjeta,
    url_base,
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
        href=True,
    ):

        url = urljoin(
            url_base,
            enlace["href"],
        )

        if parece_producto_url(
            url
        ):

            return url

    return None


# ============================================================
# EXTRAER PRODUCTOS
# ============================================================

def extraer_productos(
    soup,
    url_base,
):

    selectores = [
        ".ty-grid-list__item",
        ".grid-list__item",
        ".product-cell",
        ".ty-column",
        "[class*='product-grid']",
    ]

    tarjetas = []

    for selector in selectores:

        encontradas = soup.select(
            selector
        )

        tarjetas.extend(
            encontradas
        )

    # --------------------------------------------------------
    # Deduplicar tarjetas
    # --------------------------------------------------------

    unicas = []

    vistas_tarjetas = set()

    for tarjeta in tarjetas:

        identificador = id(
            tarjeta
        )

        if identificador in vistas_tarjetas:
            continue

        vistas_tarjetas.add(
            identificador
        )

        unicas.append(
            tarjeta
        )

    resultado = []

    urls_vistas = set()

    for tarjeta in unicas:

        # ----------------------------------------------------
        # Nombre
        # ----------------------------------------------------

        nombre = ""

        imagen = tarjeta.find(
            "img"
        )

        if imagen:

            nombre = (
                imagen.get("alt")
                or imagen.get("title")
                or ""
            ).strip()

        if not nombre:

            for selector in [
                ".product-title",
                ".ty-grid-list__item-name",
                "[class*='product-title']",
                "[class*='item-name']",
            ]:

                elemento = tarjeta.select_one(
                    selector
                )

                if elemento:

                    nombre = elemento.get_text(
                        " ",
                        strip=True
                    )

                    if nombre:
                        break

        if not nombre:
            continue

        # ----------------------------------------------------
        # URL
        # ----------------------------------------------------

        url_producto = extraer_url_producto(
            tarjeta,
            url_base
        )

        if not url_producto:
            continue

        url_producto = (
            url_producto
            .split("#")[0]
        )

        if url_producto in urls_vistas:
            continue

        urls_vistas.add(
            url_producto
        )

        # ----------------------------------------------------
        # Claves
        # ----------------------------------------------------

        clave_v6 = limpiar_nombre_v6(
            nombre
        )

        clave_flexible = normalizar_nombre_flexible(
            nombre
        )

        if not clave_v6:
            continue

        resultado.append(
            {
                "nombre": nombre,
                "clave_v6": clave_v6,
                "clave_flexible": clave_flexible,
                "url": url_producto,
            }
        )

    return resultado


# ============================================================
# OBTENER TODA LA CATEGORÍA
# ============================================================

def obtener_productos_categoria(
    url_inicial,
):

    todos = {}

    visitadas = set()

    url_actual = agregar_items_por_pagina(
        url_inicial,
        ITEMS_POR_PAGINA,
    )

    pagina = 1

    while url_actual:

        clave_url = (
            url_actual.rstrip("/")
        )

        if clave_url in visitadas:

            print(
                "      🛑 Página repetida."
            )

            break

        visitadas.add(
            clave_url
        )

        print(
            f"      📄 Página {pagina}: "
            f"{url_actual}"
        )

        soup = obtener_html(
            url_actual
        )

        if not soup:
            break

        productos = extraer_productos(
            soup,
            url_actual,
        )

        nuevos = 0

        for producto in productos:

            clave = producto[
                "clave_v6"
            ]

            if clave not in todos:

                todos[clave] = (
                    producto
                )

                nuevos += 1

        print(
            f"         📦 {len(productos)} encontrados"
        )

        print(
            f"         🆕 {nuevos} nuevos"
        )

        siguiente = siguiente_pagina(
            soup,
            url_actual,
        )

        if not siguiente:
            break

        siguiente = agregar_items_por_pagina(
            siguiente,
            ITEMS_POR_PAGINA,
        )

        if (
            siguiente.rstrip("/")
            == url_actual.rstrip("/")
        ):
            break

        url_actual = siguiente

        pagina += 1

        time.sleep(
            PAUSA_ENTRE_PAGINAS
        )

    return todos


# ============================================================
# ESCANEAR PRODUCTOS LOCALES
# ============================================================

EXTENSIONES_IMAGEN = (
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".bmp",
    ".tif",
    ".tiff",
)


def contar_imagenes_en_carpeta(
    carpeta
):

    total = 0

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
                    EXTENSIONES_IMAGEN
                ):

                    total += 1

    except OSError:
        pass

    return total


def obtener_productos_locales(
    carpeta,
):

    productos = {}

    if not os.path.isdir(
        carpeta
    ):
        return productos

    for raiz, directorios, archivos in os.walk(
        carpeta
    ):

        imagenes = [
            archivo
            for archivo in archivos
            if archivo.lower().endswith(
                EXTENSIONES_IMAGEN
            )
        ]

        if not imagenes:
            continue

        nombre = os.path.basename(
            raiz
        )

        # Ignorar carpetas especiales.
        if nombre.startswith("_"):
            continue

        clave_v6 = limpiar_nombre_v6(
            nombre
        )

        clave_flexible = normalizar_nombre_flexible(
            nombre
        )

        if not clave_v6:
            continue

        registro = {
            "nombre": nombre,
            "ruta": raiz,
            "clave_v6": clave_v6,
            "clave_flexible": clave_flexible,
            "imagenes": len(imagenes),
        }

        productos.setdefault(
            clave_v6,
            []
        ).append(
            registro
        )

    return productos


# ============================================================
# CONSTRUIR ÁRBOL WEB
# ============================================================

def construir_nodo_web(
    nombre,
    nodo,
    ruta_logica="",
):

    url = nodo["url"]

    hijos = nodo.get(
        "children",
        {}
    )

    if ruta_logica:

        ruta_actual = (
            f"{ruta_logica}\\{nombre}"
        )

    else:

        ruta_actual = nombre

    print()
    print(
        "🌿 " + ruta_actual
    )

    print(
        f"   🔎 {url}"
    )

    productos_propios = obtener_productos_categoria(
        url
    )

    resultados_hijos = {}

    productos_descendientes = set()

    for nombre_hijo, nodo_hijo in hijos.items():

        resultado_hijo = construir_nodo_web(
            nombre_hijo,
            nodo_hijo,
            ruta_actual,
        )

        resultados_hijos[
            nombre_hijo
        ] = resultado_hijo

        productos_descendientes.update(
            resultado_hijo[
                "todos"
            ]
        )

    propios = set(
        productos_propios.keys()
    )

    if hijos:

        exclusivos = (
            propios
            - productos_descendientes
        )

    else:

        exclusivos = propios

    todos = (
        propios
        | productos_descendientes
    )

    print(
        f"   📦 Productos propios: "
        f"{len(propios)}"
    )

    print(
        f"   🌱 Productos descendientes: "
        f"{len(productos_descendientes)}"
    )

    print(
        f"   📌 Exclusivos del nodo: "
        f"{len(exclusivos)}"
    )

    return {
        "nombre": nombre,
        "ruta": ruta_actual,
        "url": url,
        "productos": productos_propios,
        "hijos": resultados_hijos,
        "exclusivos": exclusivos,
        "todos": todos,
    }


def construir_indice_web():

    indice = {}

    for nombre, nodo in ARBOL_CATEGORIAS.items():

        indice[nombre] = construir_nodo_web(
            nombre,
            nodo
        )

    return indice


# ============================================================
# GENERAR ASIGNACIONES
# ============================================================

def generar_asignaciones(
    resultado,
    categoria_raiz,
    salida,
):

    asignaciones = []

    ruta_nodo = resultado[
        "ruta"
    ]

    hijos = resultado[
        "hijos"
    ]

    exclusivos = resultado[
        "exclusivos"
    ]

    productos = resultado[
        "productos"
    ]

    # --------------------------------------------------------
    # Si tiene hijos, los exclusivos del padre van a INDEX.
    # --------------------------------------------------------

    if hijos and exclusivos:

        ruta_destino = os.path.join(
            salida,
            ruta_nodo,
            "INDEX"
        )

        for clave in sorted(
            exclusivos
        ):

            producto = productos.get(
                clave
            )

            if producto:

                asignaciones.append(
                    {
                        "clave_v6": clave,
                        "clave_flexible": (
                            producto[
                                "clave_flexible"
                            ]
                        ),
                        "nombre_web": (
                            producto[
                                "nombre"
                            ]
                        ),
                        "url_web": (
                            producto[
                                "url"
                            ]
                        ),
                        "categoria": ruta_nodo,
                        "destino": ruta_destino,
                        "tipo": "INDEX",
                        "profundidad": ruta_nodo.count("\\"),
                    }
                )

    # --------------------------------------------------------
    # Si NO tiene hijos, sus productos son canónicos.
    # --------------------------------------------------------

    if not hijos:

        ruta_destino = os.path.join(
            salida,
            ruta_nodo
        )

        for clave in sorted(
            exclusivos
        ):

            producto = productos.get(
                clave
            )

            if producto:

                asignaciones.append(
                    {
                        "clave_v6": clave,
                        "clave_flexible": (
                            producto[
                                "clave_flexible"
                            ]
                        ),
                        "nombre_web": (
                            producto[
                                "nombre"
                            ]
                        ),
                        "url_web": (
                            producto[
                                "url"
                            ]
                        ),
                        "categoria": ruta_nodo,
                        "destino": ruta_destino,
                        "tipo": "HOJA",
                        "profundidad": ruta_nodo.count("\\") + 1,
                    }
                )

    # --------------------------------------------------------
    # Hijos.
    # --------------------------------------------------------

    for resultado_hijo in hijos.values():

        asignaciones.extend(
            generar_asignaciones(
                resultado_hijo,
                categoria_raiz,
                salida,
            )
        )

    return asignaciones


# ============================================================
# RESOLVER PRODUCTO LOCAL
# ============================================================

def construir_indice_flexible(
    locales
):

    indice = {}

    for clave_v6, registros in locales.items():

        for registro in registros:

            clave = registro[
                "clave_flexible"
            ]

            indice.setdefault(
                clave,
                []
            ).append(
                (
                    clave_v6,
                    registro
                )
            )

    return indice


def resolver_producto_local(
    asignacion,
    locales,
    indice_flexible,
):

    clave_v6 = asignacion[
        "clave_v6"
    ]

    # --------------------------------------------------------
    # 1. Coincidencia exacta compatible con V6.
    # --------------------------------------------------------

    if clave_v6 in locales:

        registros = locales[
            clave_v6
        ]

        if len(registros) == 1:

            return {
                "registro": registros[0],
                "metodo": "EXACTA_V6",
                "ambiguo": False,
            }

        return {
            "registro": None,
            "metodo": "DUPLICADO_LOCAL",
            "ambiguo": True,
        }

    # --------------------------------------------------------
    # 2. Coincidencia flexible.
    # --------------------------------------------------------

    clave_flexible = asignacion[
        "clave_flexible"
    ]

    candidatos = indice_flexible.get(
        clave_flexible,
        []
    )

    if len(candidatos) == 1:

        return {
            "registro": candidatos[0][1],
            "metodo": "FLEXIBLE_EXACTA",
            "ambiguo": False,
        }

    if len(candidatos) > 1:

        return {
            "registro": None,
            "metodo": "FLEXIBLE_AMBIGUA",
            "ambiguo": True,
        }

    return {
        "registro": None,
        "metodo": "NO_ENCONTRADO",
        "ambiguo": False,
    }


# ============================================================
# COPIAR PRODUCTO
# ============================================================

def copiar_producto(
    origen,
    destino,
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

            cantidad = copiar_producto(
                origen_elemento,
                destino_elemento
            )

            copiados += cantidad

            continue

        if os.path.isfile(
            origen_elemento
        ):

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
# NOMBRE DE CARPETA SEGURO
# ============================================================

def nombre_seguro(
    nombre
):

    resultado = limpiar_nombre_v6(
        nombre
    )

    if not resultado:

        resultado = (
            "PRODUCTO_SIN_NOMBRE"
        )

    return resultado


# ============================================================
# CONTAR IMÁGENES
# ============================================================

def contar_imagenes_recursivo(
    carpeta
):

    total = 0

    if not os.path.isdir(
        carpeta
    ):

        return 0

    for raiz, directorios, archivos in os.walk(
        carpeta
    ):

        for archivo in archivos:

            if archivo.lower().endswith(
                EXTENSIONES_IMAGEN
            ):

                total += 1

    return total


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 75)
    print(
        "🐣 SPLANET V7.3 — "
        "ORGANIZADOR JERÁRQUICO SIN DUPLICADOS"
    )
    print("=" * 75)
    print()

    # ========================================================
    # ENTRADA
    # ========================================================

    if not os.path.isdir(
        CARPETA_ENTRADA
    ):

        print(
            f"❌ No existe: {CARPETA_ENTRADA}"
        )

        return

    # ========================================================
    # EVITAR MEZCLAR RESULTADOS VIEJOS
    # ========================================================

    if os.path.exists(
        CARPETA_SALIDA
    ):

        print(
            f"⚠️ Ya existe: {CARPETA_SALIDA}"
        )

        print()
        print(
            "Para evitar mezclar resultados, "
            "V7.3 no reutiliza esa carpeta."
        )

        print()
        print(
            "Borra o renombra esa carpeta "
            "y vuelve a ejecutar V7.3."
        )

        return

    # ========================================================
    # ESCANEAR LOCALES
    # ========================================================

    print(
        "📂 Escaneando CATALOGO_LIMPIO..."
    )

    locales = obtener_productos_locales(
        CARPETA_ENTRADA
    )

    cantidad_claves = len(
        locales
    )

    cantidad_carpetas_locales = sum(
        len(registros)
        for registros in locales.values()
    )

    imagenes_fuente = contar_imagenes_recursivo(
        CARPETA_ENTRADA
    )

    print(
        f"📦 Claves únicas locales: "
        f"{cantidad_claves}"
    )

    print(
        f"📁 Carpetas de producto locales: "
        f"{cantidad_carpetas_locales}"
    )

    print(
        f"🖼️ Imágenes fuente: "
        f"{imagenes_fuente}"
    )

    # ========================================================
    # DUPLICADOS LOCALES
    # ========================================================

    duplicados_locales = {
        clave: registros
        for clave, registros in locales.items()
        if len(registros) > 1
    }

    if duplicados_locales:

        print()
        print(
            "⚠️ DUPLICADOS LOCALES:"
        )

        for clave, registros in duplicados_locales.items():

            print()
            print(
                f"🔁 {clave}"
            )

            for registro in registros:

                print(
                    f"   📁 "
                    f"{registro['ruta']} "
                    f"({registro['imagenes']} imágenes)"
                )

        print()
        print(
            "🐣 V7.3 NO los copiará dos veces."
        )

        print(
            "Se considerarán una sola clave."
        )

    # ========================================================
    # ÍNDICE FLEXIBLE
    # ========================================================

    indice_flexible = construir_indice_flexible(
        locales
    )

    # ========================================================
    # CONSULTAR WEB
    # ========================================================

    print()
    print("=" * 75)
    print(
        "🌐 CONSTRUYENDO ÁRBOL WEB"
    )
    print("=" * 75)

    indice_web = construir_indice_web()

    # ========================================================
    # GENERAR ASIGNACIONES
    # ========================================================

    print()
    print("=" * 75)
    print(
        "🧠 GENERANDO ASIGNACIONES"
    )
    print("=" * 75)

    asignaciones = []

    for categoria, resultado in indice_web.items():

        asignaciones.extend(
            generar_asignaciones(
                resultado,
                categoria,
                CARPETA_SALIDA,
            )
        )

    print()
    print(
        f"📌 Asignaciones web generadas: "
        f"{len(asignaciones)}"
    )

    # ========================================================
    # PRIORIZAR HOJAS
    # ========================================================
    #
    # Si por alguna razón el mismo producto aparece en
    # diferentes lugares, primero se intenta conservar
    # la ubicación más profunda.
    #
    # INDEX tiene menor prioridad.
    #
    # ========================================================

    def prioridad_asignacion(
        asignacion
    ):

        tipo = asignacion[
            "tipo"
        ]

        es_index = (
            tipo == "INDEX"
        )

        return (
            es_index,
            -asignacion[
                "profundidad"
            ],
            asignacion[
                "categoria"
            ].upper(),
            asignacion[
                "nombre_web"
            ].upper(),
        )

    asignaciones.sort(
        key=prioridad_asignacion
    )

    # ========================================================
    # CREAR SALIDA
    # ========================================================

    os.makedirs(
        CARPETA_SALIDA,
        exist_ok=True
    )

    # ========================================================
    # ESTADÍSTICAS
    # ========================================================

    usados = set()

    conflictos = []

    no_encontrados = []

    ambiguos = []

    organizados = 0

    imagenes_copiadas = 0

    manifest_rows = []

    # ========================================================
    # ORGANIZAR
    # ========================================================

    print()
    print("=" * 75)
    print(
        "📁 ORGANIZANDO"
    )
    print("=" * 75)

    for asignacion in asignaciones:

        clave = asignacion[
            "clave_v6"
        ]

        resultado = resolver_producto_local(
            asignacion,
            locales,
            indice_flexible,
        )

        registro = resultado[
            "registro"
        ]

        metodo = resultado[
            "metodo"
        ]

        # ----------------------------------------------------
        # No encontrado
        # ----------------------------------------------------

        if registro is None:

            if metodo == "NO_ENCONTRADO":

                no_encontrados.append(
                    asignacion
                )

                manifest_rows.append(
                    {
                        "estado": "NO_ENCONTRADO",
                        "metodo": metodo,
                        "clave_v6": clave,
                        "nombre_web": (
                            asignacion[
                                "nombre_web"
                            ]
                        ),
                        "nombre_local": "",
                        "origen": "",
                        "categoria": (
                            asignacion[
                                "categoria"
                            ]
                        ),
                        "tipo": (
                            asignacion[
                                "tipo"
                            ]
                        ),
                        "destino": "",
                        "url": (
                            asignacion[
                                "url_web"
                            ]
                        ),
                    }
                )

                continue

            # ------------------------------------------------
            # Ambiguo
            # ------------------------------------------------

            if resultado[
                "ambiguo"
            ]:

                ambiguos.append(
                    asignacion
                )

                manifest_rows.append(
                    {
                        "estado": "AMBIGUO",
                        "metodo": metodo,
                        "clave_v6": clave,
                        "nombre_web": (
                            asignacion[
                                "nombre_web"
                            ]
                        ),
                        "nombre_local": "",
                        "origen": "",
                        "categoria": (
                            asignacion[
                                "categoria"
                            ]
                        ),
                        "tipo": (
                            asignacion[
                                "tipo"
                            ]
                        ),
                        "destino": "",
                        "url": (
                            asignacion[
                                "url_web"
                            ]
                        ),
                    }
                )

                continue

        # ----------------------------------------------------
        # Producto ya utilizado
        # ----------------------------------------------------

        ruta_local = registro[
            "ruta"
        ]

        if clave in usados:

            conflictos.append(
                asignacion
            )

            print()
            print(
                "🔁 CONFLICTO DE CATEGORÍA:"
            )

            print(
                f"   📦 "
                f"{registro['nombre']}"
            )

            print(
                f"   📍 Ya asignado."
            )

            print(
                f"   ↪ Ignorado en: "
                f"{asignacion['categoria']}"
            )

            manifest_rows.append(
                {
                    "estado": "CONFLICTO_CATEGORIA",
                    "metodo": metodo,
                    "clave_v6": clave,
                    "nombre_web": (
                        asignacion[
                            "nombre_web"
                        ]
                    ),
                    "nombre_local": (
                        registro[
                            "nombre"
                        ]
                    ),
                    "origen": ruta_local,
                    "categoria": (
                        asignacion[
                            "categoria"
                        ]
                    ),
                    "tipo": (
                        asignacion[
                            "tipo"
                        ]
                    ),
                    "destino": "",
                    "url": (
                        asignacion[
                            "url_web"
                        ]
                    ),
                }
            )

            continue

        # ----------------------------------------------------
        # Marcar como usado ANTES de copiar
        #
        # Esto garantiza que jamás se duplique.
        # ----------------------------------------------------

        usados.add(
            clave
        )

        # ----------------------------------------------------
        # Destino
        # ----------------------------------------------------

        destino_categoria = asignacion[
            "destino"
        ]

        os.makedirs(
            destino_categoria,
            exist_ok=True
        )

        nombre_producto = nombre_seguro(
            registro[
                "nombre"
            ]
        )

        destino_producto = os.path.join(
            destino_categoria,
            nombre_producto
        )

        print()
        print(
            f"📦 {registro['nombre']}"
        )

        print(
            f"   ➜ {asignacion['categoria']}"
        )

        print(
            f"   🔎 {metodo}"
        )

        cantidad = copiar_producto(
            ruta_local,
            destino_producto
        )

        organizados += 1

        imagenes_copiadas += cantidad

        manifest_rows.append(
            {
                "estado": "ORGANIZADO",
                "metodo": metodo,
                "clave_v6": clave,
                "nombre_web": (
                    asignacion[
                        "nombre_web"
                    ]
                ),
                "nombre_local": (
                    registro[
                        "nombre"
                    ]
                ),
                "origen": ruta_local,
                "categoria": (
                    asignacion[
                        "categoria"
                    ]
                ),
                "tipo": (
                    asignacion[
                        "tipo"
                    ]
                ),
                "destino": destino_producto,
                "url": (
                    asignacion[
                        "url_web"
                    ]
                ),
            }
        )

    # ========================================================
    # PRODUCTOS LOCALES QUE NUNCA APARECIERON EN WEB
    # ========================================================

    claves_locales = set(
        locales.keys()
    )

    claves_no_asignadas = (
        claves_locales
        - usados
    )

    # Las claves que tuvieron conflictos de resolución web
    # y por eso no entraron a "usados" deben quedar también
    # para revisión.
    claves_problematicas = set()

    for asignacion in no_encontrados:

        claves_problematicas.add(
            asignacion[
                "clave_v6"
            ]
        )

    for asignacion in ambiguos:

        claves_problematicas.add(
            asignacion[
                "clave_v6"
            ]
        )

    no_encontrados_locales = (
        claves_no_asignadas
        - claves_problematicas
    )

    # ========================================================
    # REVISIÓN DE PRODUCTOS LOCALES
    # ========================================================

    revision_total = 0

    claves_revision = (
        claves_no_asignadas
    )

    if claves_revision:

        carpeta_revision = os.path.join(
            CARPETA_SALIDA,
            CARPETA_REVISION,
        )

        os.makedirs(
            carpeta_revision,
            exist_ok=True
        )

        print()
        print("=" * 75)
        print(
            "⚠️ PRODUCTOS PARA REVISIÓN"
        )
        print("=" * 75)

        for clave in sorted(
            claves_revision
        ):

            registros = locales[
                clave
            ]

            for registro in registros:

                nombre = registro[
                    "nombre"
                ]

                print()
                print(
                    f"⚠️ {nombre}"
                )

                nombre_seguro_local = nombre_seguro(
                    nombre
                )

                destino_revision = os.path.join(
                    carpeta_revision,
                    nombre_seguro_local
                )

                # ------------------------------------------------
                # Evitar colisión.
                # ------------------------------------------------

                if os.path.exists(
                    destino_revision
                ):

                    contador = 2

                    while os.path.exists(
                        f"{destino_revision}_{contador}"
                    ):

                        contador += 1

                    destino_revision = (
                        f"{destino_revision}_{contador}"
                    )

                cantidad = copiar_producto(
                    registro["ruta"],
                    destino_revision
                )

                revision_total += 1

                manifest_rows.append(
                    {
                        "estado": "REVISION_LOCAL",
                        "metodo": "",
                        "clave_v6": clave,
                        "nombre_web": "",
                        "nombre_local": nombre,
                        "origen": registro["ruta"],
                        "categoria": "",
                        "tipo": "REVISION",
                        "destino": destino_revision,
                        "url": "",
                    }
                )

    # ========================================================
    # MANIFEST CSV
    # ========================================================

    ruta_manifest = os.path.join(
        CARPETA_SALIDA,
        MANIFEST
    )

    with open(
        ruta_manifest,
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as archivo:

        campos = [
            "estado",
            "metodo",
            "clave_v6",
            "nombre_web",
            "nombre_local",
            "origen",
            "categoria",
            "tipo",
            "destino",
            "url",
        ]

        escritor = csv.DictWriter(
            archivo,
            fieldnames=campos
        )

        escritor.writeheader()

        escritor.writerows(
            manifest_rows
        )

    # ========================================================
    # VALIDACIÓN FINAL
    # ========================================================

    imagenes_salida = contar_imagenes_recursivo(
        CARPETA_SALIDA
    )

    # ========================================================
    # RESUMEN
    # ========================================================

    print()
    print("=" * 75)
    print(
        "📊 RESUMEN V7.3"
    )
    print("=" * 75)

    print(
        f"📦 Claves locales únicas: "
        f"{cantidad_claves}"
    )

    print(
        f"📁 Carpetas locales de producto: "
        f"{cantidad_carpetas_locales}"
    )

    print(
        f"🌐 Asignaciones web: "
        f"{len(asignaciones)}"
    )

    print(
        f"✅ Productos organizados: "
        f"{organizados}"
    )

    print(
        f"⚠️ Productos en revisión: "
        f"{revision_total}"
    )

    print(
        f"🔁 Duplicados locales: "
        f"{len(duplicados_locales)}"
    )

    print(
        f"⚠️ Ambiguos: "
        f"{len(ambiguos)}"
    )

    print(
        f"🔁 Conflictos de categoría: "
        f"{len(conflictos)}"
    )

    print()
    print(
        f"🖼️ Imágenes en CATALOGO_LIMPIO: "
        f"{imagenes_fuente}"
    )

    print(
        f"🖼️ Imágenes en salida V7.3: "
        f"{imagenes_salida}"
    )

    diferencia = (
        imagenes_salida
        - imagenes_fuente
    )

    print(
        f"📐 Diferencia: "
        f"{diferencia:+d}"
    )

    # ========================================================
    # VALIDACIÓN DE DUPLICACIÓN
    # ========================================================

    print()

    if imagenes_salida > imagenes_fuente:

        print(
            "🚨 ALERTA: "
            "La salida contiene más imágenes "
            "que la fuente."
        )

        print(
            "   Esto NO debería suceder."
        )

    else:

        print(
            "✅ Validación de imágenes correcta."
        )

        print(
            "   Salida <= Fuente."
        )

    # ========================================================
    # VALIDACIÓN DE USO ÚNICO
    # ========================================================

    print()

    if len(usados) == organizados:

        print(
            "✅ Cada producto organizado "
            "fue marcado una sola vez."
        )

    else:

        print(
            "⚠️ Revisar conteo interno."
        )

    # ========================================================
    # RUTA FINAL
    # ========================================================

    print()
    print(
        f"📂 Resultado: "
        f"{CARPETA_SALIDA}"
    )

    print(
        f"📄 Manifest: "
        f"{ruta_manifest}"
    )

    print()
    print(
        "👉 CATALOGO_LIMPIO permanece intacto."
    )

    print()
    print(
        "🐣🐥🐧 ¡V7.3 TERMINADO SIN COPIAS "
        "REDUNDANTES!"
    )

    print()


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":

    main()