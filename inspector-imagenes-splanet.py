import requests
from bs4 import BeautifulSoup

URL_PRUEBA = "https://tienda.splanet.com.mx/store/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

print("🕵️‍♂️ Ejecutando diagnóstico de etiquetas HTML en SPlanet...")
try:
    response = requests.get(URL_PRUEBA, headers=HEADERS, timeout=15)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print("\n--- 1. BUSCANDO IMÁGENES DISPONIBLES EN LA PÁGINA ---")
        imagenes = soup.find_all('img')
        print(f"Se encontraron {len(imagenes)} imágenes en total.")
        
        # Mostrar las primeras 15 imágenes para ver sus clases y atributos
        for idx, img in enumerate(imagenes[:15]):
            src = img.get('src', 'No tiene src')
            data_src = img.get('data-src', 'No tiene data-src')
            clases = img.get('class', 'No tiene clases')
            alt = img.get('alt', 'No tiene alt')
            print(f"📸 Foto [{idx}]: Alt: {alt} | Src: {src} | Data-Src: {data_src} | Clases: {clases}")
            
        print("\n--- 2. BUSCANDO ENLACES O CONTENEDORES DE PRODUCTO ---")
        # Vamos a ver si los títulos de los productos usan alguna clase común
        for tag in ['h2', 'h3', 'h4', 'span', 'a']:
            elementos = soup.find_all(tag, class_=True)
            if elementos:
                print(f"Clases detectadas en etiquetas <{tag}> (Muestra de las primeras 5):")
                for el in elementos[:5]:
                    print(f"   Etiqueta <{tag}> con clase: {el['class']} | Texto: '{el.text.strip()[:30]}'")

    else:
        print(f"❌ Error: El servidor respondió con código {response.status_code}")
except Exception as e:
    print(f"❌ Error de conexión: {e}")
