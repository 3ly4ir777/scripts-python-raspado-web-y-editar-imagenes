# V9 — CONTROL DE CALIDAD SPLANET

# Revisión automática de imágenes procesadas

import os
import csv
import shutil

from PIL import Image

# ============================================================

# CONFIGURACIÓN

# ============================================================

CARPETA_ENTRADA = "CATALOGO_LIMPIO"

CARPETA_REVISION = os.path.join(
CARPETA_ENTRADA,
"_REVISION_V9"
)

TAMAÑO_ESPERADO = (
1080,
1080
)

# Si el contenido ocupa menos de este porcentaje

# del lienzo, se considera posiblemente demasiado pequeño.

MINIMO_OCUPACION = 0.10

# Si toca los bordes, lo marcamos.

MARGEN_MINIMO = 2

# ============================================================

# ANALIZAR IMAGEN

# ============================================================

def analizar_imagen(
ruta
):


    resultado = {
    "estado": "OK",
    "problemas": "",
}

try:

    with Image.open(
        ruta
    ) as imagen:

        # ------------------------------------------------
        # Dimensiones
        # ------------------------------------------------

        if imagen.size != TAMAÑO_ESPERADO:

            resultado["problemas"] += (
                "DIMENSIONES; "
            )

        # ------------------------------------------------
        # Formato
        # ------------------------------------------------

        if imagen.format != "PNG":

            resultado["problemas"] += (
                "NO_PNG; "
            )

        # ------------------------------------------------
        # Transparencia
        # ------------------------------------------------

        if imagen.mode != "RGBA":

            resultado["problemas"] += (
                "SIN_RGBA; "
            )

            # Convertir solo para poder analizar.
            imagen = imagen.convert(
                "RGBA"
            )

        alpha = imagen.getchannel(
            "A"
        )

        bbox = alpha.getbbox()

        # ------------------------------------------------
        # Imagen vacía
        # ------------------------------------------------

        if bbox is None:

            resultado["problemas"] += (
                "IMAGEN_VACIA; "
            )

            resultado["estado"] = "REVISAR"

            return resultado

        izquierda, arriba, derecha, abajo = bbox

        ancho_producto = (
            derecha - izquierda
        )

        alto_producto = (
            abajo - arriba
        )

        ocupacion = (
            ancho_producto
            * alto_producto
        ) / (
            imagen.width
            * imagen.height
        )

        resultado[
            "ancho_producto"
        ] = ancho_producto

        resultado[
            "alto_producto"
        ] = alto_producto

        resultado[
            "ocupacion"
        ] = round(
            ocupacion,
            4
        )

        # ------------------------------------------------
        # Producto demasiado pequeño
        # ------------------------------------------------

        if ocupacion < MINIMO_OCUPACION:

            resultado["problemas"] += (
                "PRODUCTO_MUY_PEQUENO; "
            )

        # ------------------------------------------------
        # Producto pegado a los bordes
        # ------------------------------------------------

        if izquierda <= MARGEN_MINIMO:

            resultado["problemas"] += (
                "TOCA_BORDE_IZQUIERDO; "
            )

        if arriba <= MARGEN_MINIMO:

            resultado["problemas"] += (
                "TOCA_BORDE_SUPERIOR; "
            )

        if (
            imagen.width - derecha
            <= MARGEN_MINIMO
        ):

            resultado["problemas"] += (
                "TOCA_BORDE_DERECHO; "
            )

        if (
            imagen.height - abajo
            <= MARGEN_MINIMO
        ):

            resultado["problemas"] += (
                "TOCA_BORDE_INFERIOR; "
            )

        # ------------------------------------------------
        # Resultado
        # ------------------------------------------------

        if resultado["problemas"]:

            resultado["estado"] = (
                "REVISAR"
            )

except Exception as error:

    resultado["estado"] = "ERROR"

    resultado["problemas"] = (
        f"ERROR_LECTURA: {error}"
    )

return resultado


# ============================================================

# RECORRIDO

# ============================================================

def recorrer(
carpeta
):


archivos = []

for raiz, carpetas, nombres in os.walk(
    carpeta
):

    # No analizar nuestra propia carpeta de revisión.
    carpetas[:] = [
        x
        for x in carpetas
        if x != "_REVISION_V9"
    ]

    for nombre in nombres:

        if nombre.lower().endswith(
            ".png"
        ):

            archivos.append(
                os.path.join(
                    raiz,
                    nombre
                )
            )

return archivos


# ============================================================

# MAIN

# ============================================================

def main():


print()
print("=" * 70)
print("🐧 SPLANET V9 — CONTROL DE CALIDAD")
print("=" * 70)

if not os.path.isdir(
    CARPETA_ENTRADA
):

    print(
        f"❌ No existe: {CARPETA_ENTRADA}"
    )

    return

os.makedirs(
    CARPETA_REVISION,
    exist_ok=True
)

archivos = recorrer(
    CARPETA_ENTRADA
)

print()
print(
    f"🔎 Imágenes a revisar: "
    f"{len(archivos)}"
)

reporte = []

correctas = 0
revision = 0
errores = 0

for indice, ruta in enumerate(
    archivos,
    start=1
):

    print(
        f"[{indice}/{len(archivos)}] "
        f"{os.path.basename(ruta)}"
    )

    resultado = analizar_imagen(
        ruta
    )

    estado = resultado[
        "estado"
    ]

    relativa = os.path.relpath(
        ruta,
        CARPETA_ENTRADA
    )

    fila = {
        "archivo": relativa,
        **resultado
    }

    reporte.append(
        fila
    )

    # ----------------------------------------------------
    # OK
    # ----------------------------------------------------

    if estado == "OK":

        correctas += 1

        print(
            "   ✅ OK"
        )

    # ----------------------------------------------------
    # REVISAR
    # ----------------------------------------------------

    elif estado == "REVISAR":

        revision += 1

        print(
            f"   ⚠️ "
            f"{resultado.get('problemas', '')}"
        )

        # Mantener estructura relativa.
        destino = os.path.join(
            CARPETA_REVISION,
            relativa
        )

        os.makedirs(
            os.path.dirname(destino),
            exist_ok=True
        )

        try:

            shutil.copy2(
                ruta,
                destino
            )

        except Exception as error:

            print(
                f"   ❌ No se pudo copiar "
                f"a revisión: {error}"
            )

    # ----------------------------------------------------
    # ERROR
    # ----------------------------------------------------

    else:

        errores += 1

        print(
            f"   ❌ "
            f"{resultado.get('problemas', '')}"
        )

# ========================================================
# CSV
# ========================================================

ruta_csv = os.path.join(
    CARPETA_ENTRADA,
    "reporte_v9.csv"
)

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

# ========================================================
# RESUMEN
# ========================================================

print()
print("=" * 70)
print("🎉 V9 TERMINADO")
print("=" * 70)

print(
    f"🖼️ Total: {len(archivos)}"
)

print(
    f"✅ Correctas: {correctas}"
)

print(
    f"⚠️ Para revisión: {revision}"
)

print(
    f"❌ Errores: {errores}"
)

print()
print(
    f"📁 Revisión: {CARPETA_REVISION}"
)

print(
    f"📄 Reporte: {ruta_csv}"
)


if **name** == "**main**":
main()
