# ============================================================
# V8 — SPLANET IMAGE CLEANER
# ============================================================
#
# Fondo transparente
# 1080x1080
# Estructura recursiva
# REANUDABLE
# Guarda progreso durante la ejecución
#
# ============================================================

import os
import csv

from PIL import Image
from rembg import remove


# ============================================================
# CONFIGURACIÓN
# ============================================================

CARPETA_ENTRADA = "CATALOGO_ORGANIZADO"
CARPETA_SALIDA = "CATALOGO_LIMPIO"

TAMAÑO_FINAL = 1080

# Porcentaje máximo que ocupará el producto
# dentro del lienzo.
#
# 0.90 = 90%
ESCALA_PRODUCTO = 0.90

# ------------------------------------------------------------
# Si True:
#   si el PNG ya existe y es válido, se salta.
#
# Esto permite detener el programa y continuar después.
# ------------------------------------------------------------

REANUDAR = True

# ------------------------------------------------------------
# Si True:
#   comprueba que los PNG existentes realmente puedan abrirse.
#
# Si encuentra uno corrupto, lo vuelve a procesar.
# ------------------------------------------------------------

VERIFICAR_ARCHIVOS_EXISTENTES = True


# ============================================================
# EXTENSIONES ADMITIDAS
# ============================================================

EXTENSIONES = (
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
    ".tif",
    ".tiff",
)


# ============================================================
# ESTADÍSTICAS
# ============================================================

estadisticas = {
    "encontradas": 0,
    "procesadas": 0,
    "saltadas": 0,
    "sin_producto": 0,
    "errores": 0,
}


# ============================================================
# REPORTE
# ============================================================

reporte = []


# ============================================================
# VALIDAR PNG EXISTENTE
# ============================================================

def imagen_existente_valida(ruta):
    """
    Comprueba si un archivo PNG existente realmente puede abrirse.

    Devuelve:

        True  = archivo válido
        False = archivo inexistente/corrupto
    """

    if not os.path.isfile(ruta):
        return False

    try:

        with Image.open(ruta) as imagen:

            # Verifica la estructura interna.
            imagen.verify()

        return True

    except Exception:
        return False


# ============================================================
# DECIDIR SI HAY QUE PROCESAR
# ============================================================

def necesita_procesamiento(
    ruta_entrada,
    ruta_salida
):
    """
    Determina si una imagen necesita ser procesada.

    Casos:

    1. No existe PNG de salida
       -> procesar

    2. Existe PNG pero está corrupto
       -> procesar

    3. El original es más reciente que el PNG
       -> procesar

    4. Todo está correcto
       -> saltar
    """

    if not REANUDAR:
        return True

    if not os.path.exists(ruta_salida):
        return True

    # --------------------------------------------------------
    # Comprobar integridad.
    # --------------------------------------------------------

    if VERIFICAR_ARCHIVOS_EXISTENTES:

        if not imagen_existente_valida(
            ruta_salida
        ):

            print(
                "   ⚠️ PNG existente corrupto."
            )

            print(
                "   🔄 Se volverá a procesar."
            )

            return True

    # --------------------------------------------------------
    # Si el original cambió después del PNG,
    # necesitamos actualizarlo.
    # --------------------------------------------------------

    try:

        fecha_original = os.path.getmtime(
            ruta_entrada
        )

        fecha_salida = os.path.getmtime(
            ruta_salida
        )

        if fecha_original > fecha_salida:

            print(
                "   🔄 El original es más reciente."
            )

            return True

    except OSError:

        return True

    return False


# ============================================================
# PROCESAR IMAGEN
# ============================================================

def procesar_imagen(
    ruta_entrada,
    ruta_salida
):

    try:

        # ----------------------------------------------------
        # Abrir imagen original.
        # ----------------------------------------------------

        original = Image.open(
            ruta_entrada
        )

        dimensiones_originales = (
            original.width,
            original.height
        )

        # ----------------------------------------------------
        # Convertir a RGBA.
        # ----------------------------------------------------

        if original.mode not in (
            "RGB",
            "RGBA"
        ):

            original = original.convert(
                "RGBA"
            )

        # ----------------------------------------------------
        # Quitar fondo.
        # ----------------------------------------------------

        sin_fondo = remove(
            original
        )

        # ----------------------------------------------------
        # Asegurar RGBA.
        # ----------------------------------------------------

        if sin_fondo.mode != "RGBA":

            sin_fondo = sin_fondo.convert(
                "RGBA"
            )

        # ----------------------------------------------------
        # Obtener canal alfa.
        # ----------------------------------------------------

        alpha = sin_fondo.getchannel(
            "A"
        )

        # ----------------------------------------------------
        # Encontrar el producto.
        # ----------------------------------------------------

        bbox = alpha.getbbox()

        if bbox is None:

            return {
                "estado": "SIN_PRODUCTO",

                "ancho_original":
                    dimensiones_originales[0],

                "alto_original":
                    dimensiones_originales[1],

                "ancho_final": 0,

                "alto_final": 0,
            }

        # ----------------------------------------------------
        # Recortar transparencia sobrante.
        # ----------------------------------------------------

        producto = sin_fondo.crop(
            bbox
        )

        # ----------------------------------------------------
        # Tamaño máximo.
        # ----------------------------------------------------

        tamaño_maximo = int(
            TAMAÑO_FINAL
            * ESCALA_PRODUCTO
        )

        # ----------------------------------------------------
        # Calcular escala conservando proporción.
        # ----------------------------------------------------

        escala = min(
            tamaño_maximo / producto.width,
            tamaño_maximo / producto.height
        )

        nuevo_ancho = max(
            1,
            int(
                producto.width
                * escala
            )
        )

        nuevo_alto = max(
            1,
            int(
                producto.height
                * escala
            )
        )

        # ----------------------------------------------------
        # Redimensionar.
        # ----------------------------------------------------

        producto = producto.resize(
            (
                nuevo_ancho,
                nuevo_alto
            ),
            Image.Resampling.LANCZOS
        )

        # ----------------------------------------------------
        # Crear lienzo transparente.
        # ----------------------------------------------------

        lienzo = Image.new(
            "RGBA",
            (
                TAMAÑO_FINAL,
                TAMAÑO_FINAL
            ),
            (
                0,
                0,
                0,
                0
            )
        )

        # ----------------------------------------------------
        # Centrar producto.
        # ----------------------------------------------------

        x = (
            TAMAÑO_FINAL
            - producto.width
        ) // 2

        y = (
            TAMAÑO_FINAL
            - producto.height
        ) // 2

        lienzo.alpha_composite(
            producto,
            (
                x,
                y
            )
        )

        # ----------------------------------------------------
        # Crear carpeta de salida.
        # ----------------------------------------------------

        os.makedirs(
            os.path.dirname(
                ruta_salida
            ),
            exist_ok=True
        )

        # ----------------------------------------------------
        # Guardar PNG.
        # ----------------------------------------------------

        lienzo.save(
            ruta_salida,
            "PNG",
            optimize=True
        )

        return {
            "estado": "OK",

            "ancho_original":
                dimensiones_originales[0],

            "alto_original":
                dimensiones_originales[1],

            "ancho_final":
                lienzo.width,

            "alto_final":
                lienzo.height,

            "ancho_producto":
                producto.width,

            "alto_producto":
                producto.height,
        }

    except Exception as error:

        return {
            "estado": "ERROR",
            "error": str(error)
        }


# ============================================================
# AGREGAR AL REPORTE
# ============================================================

def agregar_reporte(
    ruta_entrada,
    ruta_salida,
    resultado,
    accion
):

    fila = {
        "archivo_original":
            os.path.relpath(
                ruta_entrada,
                CARPETA_ENTRADA
            ),

        "archivo_procesado":
            os.path.relpath(
                ruta_salida,
                CARPETA_SALIDA
            ),

        "accion": accion,

        **resultado
    }

    reporte.append(
        fila
    )


# ============================================================
# GUARDAR REPORTE INMEDIATAMENTE
# ============================================================

def guardar_reporte():
    """
    Guarda el CSV cada vez que se actualiza el reporte.

    Esto es importante:
    si apagas la computadora a mitad del proceso,
    el progreso anterior ya quedó registrado.
    """

    if not reporte:
        return

    ruta_csv = os.path.join(
        CARPETA_SALIDA,
        "reporte_v8.csv"
    )

    # --------------------------------------------------------
    # Obtener todas las columnas.
    # --------------------------------------------------------

    campos = set()

    for fila in reporte:

        campos.update(
            fila.keys()
        )

    # Orden estable.
    campos = sorted(
        campos
    )

    try:

        with open(
            ruta_csv,
            "w",
            newline="",
            encoding="utf-8-sig"
        ) as archivo:

            escritor = csv.DictWriter(
                archivo,
                fieldnames=campos
            )

            escritor.writeheader()

            escritor.writerows(
                reporte
            )

    except Exception as error:

        print(
            f"   ⚠️ No se pudo actualizar "
            f"el reporte: {error}"
        )


# ============================================================
# PROCESAR CARPETA RECURSIVAMENTE
# ============================================================

def procesar_carpeta(
    carpeta_entrada,
    carpeta_salida
):

    # --------------------------------------------------------
    # Obtener elementos ordenados.
    #
    # Así, si alguna vez necesitamos saber aproximadamente
    # dónde se quedó, el orden será estable.
    # --------------------------------------------------------

    try:

        elementos = sorted(
            os.listdir(
                carpeta_entrada
            ),
            key=str.lower
        )

    except OSError as error:

        print(
            f"❌ No se pudo leer: "
            f"{carpeta_entrada}"
        )

        print(
            f"   {error}"
        )

        return

    for elemento in elementos:

        ruta_entrada = os.path.join(
            carpeta_entrada,
            elemento
        )

        ruta_salida = os.path.join(
            carpeta_salida,
            elemento
        )

        # ====================================================
        # SUBCARPETA
        # ====================================================

        if os.path.isdir(
            ruta_entrada
        ):

            os.makedirs(
                ruta_salida,
                exist_ok=True
            )

            procesar_carpeta(
                ruta_entrada,
                ruta_salida
            )

            continue

        # ====================================================
        # ARCHIVO
        # ====================================================

        if not elemento.lower().endswith(
            EXTENSIONES
        ):

            continue

        estadisticas["encontradas"] += 1

        # ----------------------------------------------------
        # Nombre sin extensión.
        # ----------------------------------------------------

        nombre_sin_extension = (
            os.path.splitext(
                elemento
            )[0]
        )

        # ----------------------------------------------------
        # TODAS las imágenes de salida serán PNG.
        # ----------------------------------------------------

        ruta_final = os.path.join(
            carpeta_salida,
            nombre_sin_extension + ".png"
        )

        print()
        print(
            f"🧼 Procesando:"
        )

        print(
            f"   {ruta_entrada}"
        )

        # ====================================================
        # COMPROBAR SI YA EXISTE
        # ====================================================

        if not necesita_procesamiento(
            ruta_entrada,
            ruta_final
        ):

            print(
                "   ⏭️ Ya procesada. "
                "No se vuelve a filtrar."
            )

            estadisticas["saltadas"] += 1

            agregar_reporte(
                ruta_entrada,
                ruta_final,
                {
                    "estado": "YA_EXISTIA"
                },
                "SALTADA"
            )

            # ------------------------------------------------
            # Guardar progreso.
            # ------------------------------------------------

            guardar_reporte()

            continue

        # ====================================================
        # PROCESAR
        # ====================================================

        resultado = procesar_imagen(
            ruta_entrada,
            ruta_final
        )

        estado = resultado.get(
            "estado",
            "ERROR"
        )

        # ====================================================
        # RESULTADO OK
        # ====================================================

        if estado == "OK":

            estadisticas["procesadas"] += 1

            print(
                "   ✅ 1080x1080 PNG transparente"
            )

            print(
                f"   📐 Producto: "
                f"{resultado.get('ancho_producto')}x"
                f"{resultado.get('alto_producto')}"
            )

            agregar_reporte(
                ruta_entrada,
                ruta_final,
                resultado,
                "PROCESADA"
            )

        # ====================================================
        # SIN PRODUCTO
        # ====================================================

        elif estado == "SIN_PRODUCTO":

            estadisticas["sin_producto"] += 1

            print(
                "   ⚠️ No se detectó producto."
            )

            agregar_reporte(
                ruta_entrada,
                ruta_final,
                resultado,
                "SIN_PRODUCTO"
            )

        # ====================================================
        # ERROR
        # ====================================================

        else:

            estadisticas["errores"] += 1

            print(
                f"   ❌ Error:"
            )

            print(
                f"      {resultado.get('error')}"
            )

            agregar_reporte(
                ruta_entrada,
                ruta_final,
                resultado,
                "ERROR"
            )

        # ----------------------------------------------------
        # Guardar inmediatamente.
        # ----------------------------------------------------

        guardar_reporte()


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print(
        "=" * 70
    )

    print(
        "🐥 SPLANET V8 — IMAGE CLEANER"
    )

    print(
        "=" * 70
    )

    print()

    print(
        "🧠 Modo reanudable: "
        f"{'ACTIVADO' if REANUDAR else 'DESACTIVADO'}"
    )

    print(
        "🔎 Verificación de PNG existentes: "
        f"{'ACTIVADA' if VERIFICAR_ARCHIVOS_EXISTENTES else 'DESACTIVADA'}"
    )

    print()

    # ========================================================
    # COMPROBAR ENTRADA
    # ========================================================

    if not os.path.isdir(
        CARPETA_ENTRADA
    ):

        print(
            f"❌ No existe la carpeta:"
        )

        print(
            f"   {CARPETA_ENTRADA}"
        )

        print()

        print(
            "💡 Crea la carpeta o revisa "
            "el nombre de CARPETA_ENTRADA."
        )

        return

    # ========================================================
    # CREAR SALIDA
    # ========================================================

    os.makedirs(
        CARPETA_SALIDA,
        exist_ok=True
    )

    # ========================================================
    # INICIAR
    # ========================================================

    print(
        "📂 Entrada:"
    )

    print(
        f"   {os.path.abspath(CARPETA_ENTRADA)}"
    )

    print()

    print(
        "📁 Salida:"
    )

    print(
        f"   {os.path.abspath(CARPETA_SALIDA)}"
    )

    print()

    print(
        "🚀 Iniciando procesamiento..."
    )

    print()

    procesar_carpeta(
        CARPETA_ENTRADA,
        CARPETA_SALIDA
    )

    # ========================================================
    # GUARDAR REPORTE FINAL
    # ========================================================

    guardar_reporte()

    # ========================================================
    # RESUMEN
    # ========================================================

    print()
    print(
        "=" * 70
    )

    print(
        "🎉 V8 TERMINADO / PAUSADO CON SEGURIDAD"
    )

    print(
        "=" * 70
    )

    print(
        f"🖼️ Imágenes encontradas: "
        f"{estadisticas['encontradas']}"
    )

    print(
        f"✅ Procesadas ahora: "
        f"{estadisticas['procesadas']}"
    )

    print(
        f"⏭️ Ya existentes / saltadas: "
        f"{estadisticas['saltadas']}"
    )

    print(
        f"⚠️ Sin producto: "
        f"{estadisticas['sin_producto']}"
    )

    print(
        f"❌ Errores: "
        f"{estadisticas['errores']}"
    )

    print()

    print(
        "📄 Reporte:"
    )

    print(
        f"   {os.path.join(CARPETA_SALIDA, 'reporte_v8.csv')}"
    )

    print()

    print(
        "🐣 Puedes ejecutar V8 nuevamente."
    )

    print(
        "   Las imágenes ya procesadas serán saltadas."
    )

    print(
        "🐥 Si lo detienes y apagas la PC, "
        "puedes continuar después."
    )

    print(
        "🐧 Tus originales permanecen intactos."
    )

    print()


# ============================================================
# PUNTO DE ENTRADA
# ============================================================

if __name__ == "__main__":
    main()