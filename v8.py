# V8 — IMAGE CLEANER SPLANET

# Fondo transparente + 1080x1080 + estructura recursiva

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

# Qué porcentaje máximo del lienzo puede ocupar el producto.

# 0.90 = 90%

ESCALA_PRODUCTO = 0.90

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

# PROCESAR IMAGEN

# ============================================================

def procesar_imagen(
ruta_entrada,
ruta_salida
):


    try:

        # ----------------------------------------------------
        # Abrir
        # ----------------------------------------------------

        original = Image.open(
            ruta_entrada
        )

        dimensiones_originales = (
            original.width,
            original.height
        )

        # ----------------------------------------------------
        # Convertir a RGB/RGBA apropiadamente.
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

        if sin_fondo.mode != "RGBA":

            sin_fondo = sin_fondo.convert(
                "RGBA"
            )

        # ----------------------------------------------------
        # Recortar el espacio transparente sobrante.
        # ----------------------------------------------------

        alpha = sin_fondo.getchannel(
            "A"
        )

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

        producto = sin_fondo.crop(
            bbox
        )

        # ----------------------------------------------------
        # Tamaño máximo del producto.
        # ----------------------------------------------------

        tamaño_maximo = int(
            TAMAÑO_FINAL * ESCALA_PRODUCTO
        )

        escala = min(
            tamaño_maximo / producto.width,
            tamaño_maximo / producto.height
        )

        nuevo_ancho = max(
            1,
            int(producto.width * escala)
        )

        nuevo_alto = max(
            1,
            int(producto.height * escala)
        )

        producto = producto.resize(
            (
                nuevo_ancho,
                nuevo_alto
            ),
            Image.Resampling.LANCZOS
        )

        # ----------------------------------------------------
        # Lienzo 1080x1080 transparente.
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
        # Centrar.
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
        # Guardar PNG.
        # ----------------------------------------------------

        os.makedirs(
            os.path.dirname(
                ruta_salida
            ),
            exist_ok=True
        )

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

# RECORRIDO RECURSIVO

# ============================================================

def procesar_carpeta(
carpeta_entrada,
carpeta_salida,
reporte
):


    for elemento in os.listdir(
        carpeta_entrada
    ):

        ruta_entrada = os.path.join(
            carpeta_entrada,
            elemento
        )

        ruta_salida = os.path.join(
            carpeta_salida,
            elemento
        )

        # ----------------------------------------------------
        # Subcarpeta.
        # ----------------------------------------------------

        if os.path.isdir(
            ruta_entrada
        ):

            os.makedirs(
                ruta_salida,
                exist_ok=True
            )

            procesar_carpeta(
                ruta_entrada,
                ruta_salida,
                reporte
            )

            continue

        # ----------------------------------------------------
        # Archivo.
        # ----------------------------------------------------

        if not elemento.lower().endswith(
            EXTENSIONES
        ):

            continue

        nombre_sin_extension = os.path.splitext(
            elemento
        )[0]

        ruta_final = os.path.join(
            carpeta_salida,
            nombre_sin_extension + ".png"
        )

        print()
        print(
            f"🧼 Procesando: {ruta_entrada}"
        )

        # ----------------------------------------------------
        # Si ya existe, no repetir.
        # ----------------------------------------------------

        if os.path.exists(
            ruta_final
        ):

            print(
                "   ⏭️ Ya existe. Saltando."
            )

            continue

        resultado = procesar_imagen(
            ruta_entrada,
            ruta_final
        )

        estado = resultado.get(
            "estado",
            "ERROR"
        )

        if estado == "OK":

            print(
                "   ✅ 1080x1080 PNG transparente"
            )

        elif estado == "SIN_PRODUCTO":

            print(
                "   ⚠️ No se detectó producto."
            )

        else:

            print(
                f"   ❌ {resultado.get('error')}"
            )

        fila = {
            "archivo_original":
                os.path.relpath(
                    ruta_entrada,
                    CARPETA_ENTRADA
                ),

            "archivo_procesado":
                os.path.relpath(
                    ruta_final,
                    CARPETA_SALIDA
                ),

            **resultado
        }

        reporte.append(
            fila
        )


# ============================================================

# MAIN

# ============================================================

def main():


    print()
    print("=" * 70)
    print("🐥 SPLANET V8 — IMAGE CLEANER")
    print("=" * 70)

    if not os.path.isdir(
        CARPETA_ENTRADA
    ):

        print(
            f"❌ No existe: {CARPETA_ENTRADA}"
        )

        return

    os.makedirs(
        CARPETA_SALIDA,
        exist_ok=True
    )

reporte = []

procesar_carpeta(
    CARPETA_ENTRADA,
    CARPETA_SALIDA,
    reporte
)

# --------------------------------------------------------
# CSV
# --------------------------------------------------------

ruta_csv = os.path.join(
    CARPETA_SALIDA,
    "reporte_v8.csv"
)

if reporte:

    campos = set()

    for fila in reporte:
        campos.update(
            fila.keys()
        )

    campos = list(
        campos
    )

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

# --------------------------------------------------------
# Resumen
# --------------------------------------------------------

total = len(reporte)

correctas = sum(
    1
    for x in reporte
    if x.get("estado") == "OK"
)

sin_producto = sum(
    1
    for x in reporte
    if x.get("estado")
    == "SIN_PRODUCTO"
)

errores = sum(
    1
    for x in reporte
    if x.get("estado") == "ERROR"
)

print()
print("=" * 70)
print("🎉 V8 TERMINADO")
print("=" * 70)

print(
    f"🖼️ Imágenes encontradas: {total}"
)

print(
    f"✅ Procesadas: {correctas}"
)

print(
    f"⚠️ Sin producto: {sin_producto}"
)

print(
    f"❌ Errores: {errores}"
)

print()
print(
    f"📄 Reporte: {ruta_csv}"
)


if __name__ == "__main__":
    main()
