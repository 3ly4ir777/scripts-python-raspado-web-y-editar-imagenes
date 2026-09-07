import os
from PIL import Image
from rembg import remove

def procesar_imagenes_masivo(carpeta_entrada, carpeta_salida, tamaño_objetivo=(1080, 1080)):
    # Crear la carpeta de salida si no existe
    os.makedirs(carpeta_salida, existok=True)
    
    # Recorrer todos los archivos descargados
    for archivo in os.listdir(carpeta_entrada):
        if archivo.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            ruta_input = os.path.join(carpeta_entrada, archivo)
            # Cambiamos la extensión a .png obligatoriamente para soportar transparencia
            nombre_sin_ext = os.path.splitext(archivo)[0]
            ruta_output = os.path.join(carpeta_salida, f"{nombre_sin_ext}.png")
            
            print(f"Procesando: {archivo}...")
            
            try:
                # 1. Abrir la imagen original
                img_original = Image.open(ruta_input)
                
                # 2. Quitar el fondo con IA (Rembg)
                img_sin_fondo = remove(img_original)
                
                # 3. Redimensionar de forma inteligente (Manteniendo relación de aspecto)
                # Usamos thumbnail para que el producto quepa perfecto en un lienzo de 1080x1080
                img_sin_fondo.thumbnail(tamaño_objetivo, Image.Resampling.LANCZOS)
                
                # 4. Crear un lienzo cuadrado transparente de 1080x1080 exactos
                lienzo_final = Image.new("RGBA", tamaño_objetivo, (0, 0, 0, 0))
                
                # Centrar el producto en el lienzo transparente de 1080p
                pos_x = (tamaño_objetivo[0] - img_sin_fondo.width) // 2
                pos_y = (tamaño_objetivo[1] - img_sin_fondo.height) // 2
                lienzo_final.paste(img_sin_fondo, (pos_x, pos_y), img_sin_fondo)
                
                # 5. Guardar el resultado impecable
                lienzo_final.save(ruta_output, "PNG")
                
            except Exception as e:
                print(f"❌ Error procesando {archivo}: {e}")

# Ejemplo de uso:
# procesar_imagenes_masivo("tus_imagenes_descargadas", "imagenes_limpias_1080p")
