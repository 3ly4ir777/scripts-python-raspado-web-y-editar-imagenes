# ============================================================
# V7.2 — ORGANIZADOR INTELIGENTE DEL CATÁLOGO SPLANET
# ============================================================
#
# Lee:
#     CATALOGO_LIMPIO
#
# Crea:
#     CATALOGO_FINAL
#
# Estrategia:
#
#   1. Lee el árbol real de categorías.
#   2. Consulta las categorías/subcategorías de la tienda.
#   3. Normaliza nombres de productos.
#   4. Limpia caracteres no permitidos por Windows.
#   5. Soporta productos con "/" y otros símbolos.
#   6. Detecta duplicados locales.
#   7. Intenta coincidencia exacta.
#   8. Intenta coincidencia flexible.
#   9. Mantiene la jerarquía correcta.
#  10. Usa REVISION solamente como último recurso.
#
# Los originales de CATALOGO_LIMPIO NO se modifican.
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

CARPETA_REVISION = "_REVISION_V7"

ITEMS_POR_PAGINA = 96

PAUSA_ENTRE_PAGINAS = 1.0

BASE_URL = "https://tienda.splanet.com.mx/store/"


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
# MAPA MAESTRO
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

    # --------------------------------------------------------
    # VARIOS
    #
    # Se conserva porque forma parte del mapa maestro,
    # pero puedes dejarla fuera del procesamiento si ya
    # decidiste no utilizarla.
    # --------------------------------------------------------

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

    "VITAMINAS & MINERALES": [
        "https://tienda.splanet.com.mx/store/vitaminas-and-minerales/",
        "https://tienda.splanet.com.mx/store/vitaminas-and-minerales/antioxidantes/",
        "https://tienda.splanet.com.mx/store/vitaminas-and-minerales/salud-articular/",
        "https://tienda.splanet.com.mx/store/vitaminas-and-minerales/varios/",
        "https://tienda.splanet.com.mx/store/vitaminas-and-minerales/vitaminas/",
    ],
}


# ============================================================
# CATEGORÍAS QUE QUEREMOS PROCESAR
# ============================================================
#
# Como me dijiste que VARIOS no forma parte de lo que
# necesitas actualmente, lo dejamos desactivado.
#
# Si algún día lo quieres incluir:
#
#   "VARIOS",
#
# ============================================================

CATEGORIAS_ACTIVAS = {
    "BCAA S",
    "COLAGENO",
    "CREATINA",
    "GANADORES DE MASA MUSCULAR",
    "POST-ENTRENOS",
    "PRE-ENTRENOS",
    "PROMOTORES",
    "PROTEINAS",
    "QUEMA GRASAS",
    "VITAMINAS & MINERALES",
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
        backoff_factor=1,
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
        adaptador,
    )

    sesion.mount(
        "https://",
        adaptador,
    )

    sesion.headers.update(
        HEADERS
    )

    return sesion


SESSION = crear_sesion()


# ============================================================
# NORMALIZAR TEXTO
# ============================================================

def normalizar_nombre(texto):

    if not texto:
        return ""

    texto = str(texto)

    # --------------------------------------------------------
    # Unicode.
    # --------------------------------------------------------

    texto = unicodedata.normalize(
        "NFKD",
        texto,
    )

    # --------------------------------------------------------
    # Eliminar acentos.
    # --------------------------------------------------------

    texto = "".join(
        caracter
        for caracter in texto
        if not unicodedata.combining(caracter)
    )

    # --------------------------------------------------------
    # Mayúsculas.
    # --------------------------------------------------------

    texto = texto.upper()

    # --------------------------------------------------------
    # Convertir TODOS los separadores y símbolos
    # en espacios.
    #
    # Esto incluye:
    #
    # /
    # -
    # _
    # .
    # ,
    # :
    # %
    # &
    # etc.
    #
    # --------------------------------------------------------

    texto = re.sub(
        r"[^A-Z0-9]+",
        " ",
        texto,
    )

    # --------------------------------------------------------
    # Quitar espacios duplicados.
    # --------------------------------------------------------

    texto = " ".join(
        texto.split()
    )

    return texto.strip()


# ============================================================
# LIMPIAR NOMBRE PARA WINDOWS
# ============================================================

def limpiar_nombre_windows(texto):

    if not texto:
        return ""

    texto = str(texto).strip()

    # --------------------------------------------------------
    # Caracteres prohibidos por Windows.
    # --------------------------------------------------------

    texto = re.sub(
        r'[\\/:*?"<>|]',
        "",
        texto,
    )

    # --------------------------------------------------------
    # Caracteres de control.
    # --------------------------------------------------------

    texto = "".join(
        caracter
        for caracter in texto
        if ord(caracter) >= 32
    )

    # --------------------------------------------------------
    # Espacios repetidos.
    # --------------------------------------------------------

    texto = " ".join(
        texto.split()
    )

    # --------------------------------------------------------
    # Windows no permite terminar con:
    #
    # espacio
    # punto
    #
    # --------------------------------------------------------

    texto = texto.rstrip(
        " ."
    )

    # --------------------------------------------------------
    # Nombres reservados.
    # --------------------------------------------------------

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

    if texto.upper() in reservados:
        texto = "_" + texto + "_"

    return texto


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
            f"      ⚠️ HTTP {respuesta.status_code}: "
            f"{url}"
        )

    except requests.RequestException as error:

        print(
            f"      ❌ Error HTTP: {error}"
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
    # Texto "Siguiente"
    # --------------------------------------------------------

    for enlace in soup.find_all(
        "a",
        href=True,
    ):

        texto = normalizar_nombre(
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

        if patron.search(
            urlparse(
                candidato
            ).path
        ):

            return candidato

    return None


# ============================================================
# EXTRAER PRODUCTOS DE UNA PÁGINA
# ============================================================

def extraer_productos(
    soup,
    url_base,
):

    tarjetas = []

    selectores = [
        ".ty-grid-list__item",
        ".grid-list__item",
        ".product-cell",
        ".ty-column",
        "[class*='product-grid']",
    ]

    for selector in selectores:

        encontradas = soup.select(
            selector
        )

        tarjetas.extend(
            encontradas
        )

    # --------------------------------------------------------
    # Deduplicar tarjetas.
    # --------------------------------------------------------

    unicas = []

    vistas = set()

    for tarjeta in tarjetas:

        identificador = id(
            tarjeta
        )

        if identificador in vistas:
            continue

        vistas.add(
            identificador
        )

        unicas.append(
            tarjeta
        )

    tarjetas = unicas

    resultado = []

    urls_vistas = set()

    for tarjeta in tarjetas:

        # ----------------------------------------------------
        # Nombre.
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
            )

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
                        strip=True,
                    )

                    if nombre:
                        break

        if not nombre:
            continue

        # ----------------------------------------------------
        # URL.
        # ----------------------------------------------------

        url_producto = None

        for enlace in tarjeta.find_all(
            "a",
            href=True,
        ):

            candidato = urljoin(
                url_base,
                enlace["href"],
            )

            if (
                "/store/" in candidato
                and "/images/" not in candidato
            ):

                url_producto = candidato

                break

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

        clave = normalizar_nombre(
            nombre
        )

        if not clave:
            continue

        resultado.append(
            {
                "nombre": nombre,
                "clave": clave,
                "url": url_producto,
            }
        )

    return resultado


# ============================================================
# OBTENER PRODUCTOS DE UNA CATEGORÍA
# ============================================================

def obtener_productos_categoria(
    url_inicial,
):

    todos = []

    visitadas = set()

    url_actual = agregar_items_por_pagina(
        url_inicial,
        ITEMS_POR_PAGINA,
    )

    while url_actual:

        clave_url = (
            url_actual.rstrip("/")
        )

        if clave_url in visitadas:

            break

        visitadas.add(
            clave_url
        )

        print(
            f"      📄 {url_actual}"
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

        todos.extend(
            productos
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

        url_actual = siguiente

        time.sleep(
            PAUSA_ENTRE_PAGINAS
        )

    return todos


# ============================================================
# ESCANEAR PRODUCTOS LOCALES
# ============================================================

def obtener_productos_locales(
    carpeta,
):

    productos = {}

    if not os.path.isdir(
        carpeta
    ):

        return productos

    # --------------------------------------------------------
    # Recorremos recursivamente.
    #
    # Esto permite que funcione aunque CATALOGO_LIMPIO tenga
    # categorías internas.
    # --------------------------------------------------------

    for raiz, directorios, archivos in os.walk(
        carpeta
    ):

        # ----------------------------------------------------
        # Si esta carpeta contiene archivos PNG, JPG, etc.,
        # consideramos que es una carpeta de producto.
        # ----------------------------------------------------

        imagenes = [
            archivo
            for archivo in archivos
            if archivo.lower().endswith(
                (
                    ".png",
                    ".jpg",
                    ".jpeg",
                    ".webp",
                )
            )
        ]

        if not imagenes:
            continue

        nombre = os.path.basename(
            raiz
        )

        clave = normalizar_nombre(
            nombre
        )

        if not clave:
            continue

        registro = {
            "nombre": nombre,
            "ruta": raiz,
        }

        # ----------------------------------------------------
        # Ahora NO sobrescribimos duplicados.
        # ----------------------------------------------------

        productos.setdefault(
            clave,
            []
        )

        productos[
            clave
        ].append(
            registro
        )

    return productos


# ============================================================
# CONSTRUIR ÍNDICE WEB
# ============================================================

def construir_indice_web():

    indice = {}

    for categoria, urls in URLS_MAESTRAS.items():

        if categoria not in CATEGORIAS_ACTIVAS:
            continue

        print()
        print(
            f"🌳 CATEGORÍA: {categoria}"
        )

        indice[
            categoria
        ] = {}

        # ----------------------------------------------------
        # Primera URL = raíz.
        #
        # IMPORTANTE:
        #
        # Ya NO la llamamos INDEX.
        #
        # Si la categoría no tiene subcategorías,
        # sus productos van directamente allí.
        #
        # Si tiene subcategorías, esta raíz solamente
        # sirve para descubrir productos realmente sueltos.
        # ----------------------------------------------------

        for posicion, url in enumerate(
            urls
        ):

            print(
                f"   🔎 {url}"
            )

            productos = obtener_productos_categoria(
                url
            )

            # ------------------------------------------------
            # Determinar nivel de URL.
            # ------------------------------------------------

            ruta = urlparse(
                url
            ).path

            partes = [
                parte
                for parte in ruta.split("/")
                if parte
            ]

            # ------------------------------------------------
            # La última parte es el slug.
            # ------------------------------------------------

            slug = (
                partes[-1]
                if partes
                else ""
            )

            # ------------------------------------------------
            # Determinar si es raíz.
            # ------------------------------------------------

            es_raiz = (
                posicion == 0
            )

            if es_raiz:

                nombre_destino = categoria

            else:

                nombre_destino = (
                    slug
                    .replace(
                        "-",
                        " ",
                    )
                    .upper()
                )

                nombre_destino = (
                    limpiar_nombre_windows(
                        nombre_destino
                    )
                )

            # ------------------------------------------------
            # Crear entrada.
            # ------------------------------------------------

            indice[
                categoria
            ].setdefault(
                nombre_destino,
                set(),
            )

            # ------------------------------------------------
            # Agregar claves.
            # ------------------------------------------------

            for producto in productos:

                indice[
                    categoria
                ][
                    nombre_destino
                ].add(
                    producto["clave"]
                )

    return indice


# ============================================================
# COPIAR PRODUCTO
# ============================================================

def copiar_producto(
    origen,
    destino,
):

    os.makedirs(
        destino,
        exist_ok=True,
    )

    for elemento in os.listdir(
        origen
    ):

        origen_elemento = os.path.join(
            origen,
            elemento,
        )

        destino_elemento = os.path.join(
            destino,
            elemento,
        )

        if os.path.isdir(
            origen_elemento
        ):

            shutil.copytree(
                origen_elemento,
                destino_elemento,
                dirs_exist_ok=True,
            )

        else:

            shutil.copy2(
                origen_elemento,
                destino_elemento,
            )


# ============================================================
# ENCONTRAR MEJOR COINCIDENCIA
# ============================================================

def encontrar_mejor_coincidencia(
    clave_producto,
    claves_web,
):

    # --------------------------------------------------------
    # 1. Exacta.
    # --------------------------------------------------------

    if clave_producto in claves_web:

        return clave_producto

    # --------------------------------------------------------
    # 2. Comparación ignorando pequeñas diferencias.
    # --------------------------------------------------------

    palabras_producto = set(
        clave_producto.split()
    )

    mejor_clave = None

    mejor_puntuacion = 0

    for clave_web in claves_web:

        palabras_web = set(
            clave_web.split()
        )

        if not palabras_web:
            continue

        interseccion = (
            palabras_producto
            & palabras_web
        )

        if not interseccion:
            continue

        # ----------------------------------------------------
        # Jaccard sencillo.
        # ----------------------------------------------------

        union = (
            palabras_producto
            | palabras_web
        )

        puntuacion = (
            len(interseccion)
            / len(union)
        )

        # ----------------------------------------------------
        # Bonus si uno contiene al otro.
        # ----------------------------------------------------

        if (
            clave_producto in clave_web
            or clave_web in clave_producto
        ):

            puntuacion += 0.20

        if puntuacion > mejor_puntuacion:

            mejor_puntuacion = (
                puntuacion
            )

            mejor_clave = clave_web

    # --------------------------------------------------------
    # Umbral deliberadamente conservador.
    #
    # No queremos mandar productos al lugar equivocado.
    # --------------------------------------------------------

    if mejor_puntuacion >= 0.80:

        return mejor_clave

    return None


# ============================================================
# COPIAR CON NOMBRE SEGURO
# ============================================================

def copiar_producto_seguro(
    origen,
    destino_categoria,
    nombre_original,
):

    nombre_seguro = limpiar_nombre_windows(
        nombre_original
    )

    if not nombre_seguro:

        nombre_seguro = "PRODUCTO_SIN_NOMBRE"

    destino_producto = os.path.join(
        destino_categoria,
        nombre_seguro,
    )

    # --------------------------------------------------------
    # Si ya existe, no destruirlo.
    # --------------------------------------------------------

    if os.path.exists(
        destino_producto
    ):

        # ----------------------------------------------------
        # Si es exactamente la misma ruta de origen,
        # simplemente saltamos.
        # ----------------------------------------------------

        print(
            f"      ⏭️ Ya existe: "
            f"{nombre_seguro}"
        )

        return False

    copiar_producto(
        origen,
        destino_producto,
    )

    return True


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("🐣 SPLANET V7.2 — ORGANIZADOR INTELIGENTE")
    print("=" * 70)

    # --------------------------------------------------------
    # Comprobar entrada.
    # --------------------------------------------------------

    if not os.path.isdir(
        CARPETA_ENTRADA
    ):

        print()
        print(
            f"❌ No existe: "
            f"{CARPETA_ENTRADA}"
        )

        return

    # --------------------------------------------------------
    # Escanear.
    # --------------------------------------------------------

    print()
    print(
        "📂 Escaneando catálogo limpio..."
    )

    locales = obtener_productos_locales(
        CARPETA_ENTRADA
    )

    print(
        f"📦 Claves de productos locales: "
        f"{len(locales)}"
    )

    # --------------------------------------------------------
    # Duplicados.
    # --------------------------------------------------------

    duplicados = {
        clave: registros
        for clave, registros
        in locales.items()
        if len(registros) > 1
    }

    if duplicados:

        print()
        print(
            "⚠️ DUPLICADOS LOCALES DETECTADOS:"
        )

        for clave, registros in duplicados.items():

            print()
            print(
                f"   🔁 {clave}"
            )

            for registro in registros:

                print(
                    f"      📁 "
                    f"{registro['ruta']}"
                )

    # --------------------------------------------------------
    # Índice web.
    # --------------------------------------------------------

    print()
    print(
        "=" * 70
    )

    print(
        "🌐 CONSTRUYENDO ÍNDICE DE LA TIENDA"
    )

    print(
        "=" * 70
    )

    indice = construir_indice_web()

    # --------------------------------------------------------
    # Crear salida.
    # --------------------------------------------------------

    os.makedirs(
        CARPETA_SALIDA,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Crear estructura.
    # --------------------------------------------------------

    encontrados = set()

    copiados = 0

    revisiones = 0

    ambiguos = 0

    # ========================================================
    # ORGANIZAR
    # ========================================================

    print()
    print(
        "=" * 70
    )

    print(
        "📁 ORGANIZANDO"
    )

    print(
        "=" * 70
    )

    for categoria, subcategorias in indice.items():

        print()
        print(
            f"📁 {categoria}"
        )

        # ----------------------------------------------------
        # Ordenar.
        # ----------------------------------------------------

        for subcategoria, claves in subcategorias.items():

            # ------------------------------------------------
            # Si la categoría raíz es igual a la categoría,
            # los productos van directamente:
            #
            # CATEGORIA/producto
            #
            # ------------------------------------------------

            if subcategoria == categoria:

                destino_categoria = os.path.join(
                    CARPETA_SALIDA,
                    categoria,
                )

            else:

                destino_categoria = os.path.join(
                    CARPETA_SALIDA,
                    categoria,
                    subcategoria,
                )

            os.makedirs(
                destino_categoria,
                exist_ok=True,
            )

            # ------------------------------------------------
            # Buscar cada producto.
            # ------------------------------------------------

            for clave in claves:

                if clave not in locales:

                    continue

                registros = locales[
                    clave
                ]

                # ------------------------------------------------
                # Si hay más de uno, no elegir arbitrariamente.
                # ------------------------------------------------

                if len(registros) > 1:

                    ambiguos += 1

                    print()
                    print(
                        f"   ⚠️ COINCIDENCIA LOCAL MÚLTIPLE:"
                    )

                    print(
                        f"      {clave}"
                    )

                    for registro in registros:

                        print(
                            f"      📁 "
                            f"{registro['ruta']}"
                        )

                    continue

                registro = registros[0]

                nombre_local = registro[
                    "nombre"
                ]

                ruta_local = registro[
                    "ruta"
                ]

                destino_producto = os.path.join(
                    destino_categoria,
                    limpiar_nombre_windows(
                        nombre_local
                    ),
                )

                # ------------------------------------------------
                # Ya organizado.
                # ------------------------------------------------

                if os.path.exists(
                    destino_producto
                ):

                    print(
                        f"   ⏭️ Ya existe: "
                        f"{subcategoria}/"
                        f"{nombre_local}"
                    )

                    encontrados.add(
                        clave
                    )

                    continue

                # ------------------------------------------------
                # Copiar.
                # ------------------------------------------------

                print(
                    f"   📦 {subcategoria}/"
                    f"{nombre_local}"
                )

                correcto = copiar_producto_seguro(
                    ruta_local,
                    destino_categoria,
                    nombre_local,
                )

                if correcto:

                    copiados += 1

                encontrados.add(
                    clave
                )

    # ========================================================
    # PRODUCTOS SIN COINCIDENCIA
    # ========================================================

    no_encontrados = (
        set(locales.keys())
        - encontrados
    )

    if no_encontrados:

        carpeta_revision = os.path.join(
            CARPETA_SALIDA,
            CARPETA_REVISION,
        )

        os.makedirs(
            carpeta_revision,
            exist_ok=True,
        )

        print()
        print(
            "=" * 70
        )

        print(
            "⚠️ PRODUCTOS PARA REVISIÓN"
        )

        print(
            "=" * 70
        )

        for clave in sorted(
            no_encontrados
        ):

            registros = locales[
                clave
            ]

            # ------------------------------------------------
            # Si hay duplicados, todos se conservan en revisión
            # con nombres seguros.
            # ------------------------------------------------

            for registro in registros:

                nombre = registro[
                    "nombre"
                ]

                ruta = registro[
                    "ruta"
                ]

                print()
                print(
                    f"   ⚠️ {nombre}"
                )

                nombre_seguro = limpiar_nombre_windows(
                    nombre
                )

                destino = os.path.join(
                    carpeta_revision,
                    nombre_seguro,
                )

                # ------------------------------------------------
                # Evitar colisión.
                # ------------------------------------------------

                if os.path.exists(
                    destino
                ):

                    contador = 2

                    while os.path.exists(
                        f"{destino}_{contador}"
                    ):

                        contador += 1

                    destino = (
                        f"{destino}_{contador}"
                    )

                copiar_producto(
                    ruta,
                    destino,
                )

                revisiones += 1

    # ========================================================
    # RESUMEN
    # ========================================================

    print()
    print(
        "=" * 70
    )

    print(
        "🎉 V7.2 TERMINADO"
    )

    print(
        "=" * 70
    )

    print(
        f"📦 Productos locales únicos: "
        f"{len(locales)}"
    )

    print(
        f"📁 Productos copiados: "
        f"{copiados}"
    )

    print(
        f"⚠️ Productos en revisión: "
        f"{revisiones}"
    )

    print(
        f"🔁 Claves duplicadas locales: "
        f"{len(duplicados)}"
    )

    print(
        f"⚠️ Coincidencias ambiguas: "
        f"{ambiguos}"
    )

    print()
    print(
        f"📂 Resultado: "
        f"{CARPETA_SALIDA}"
    )

    print()
    print(
        "👉 CATALOGO_LIMPIO permanece intacto."
    )

    print()
    print(
        "🐣🐥🐧 ¡Organizador V7.2 terminado!"
    )


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":

    main()