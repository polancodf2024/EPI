import csv
import numpy as np
from geopy.geocoders import Nominatim
from sklearn.cluster import DBSCAN
import pandas as pd
import streamlit as st
from collections import Counter
from opencage.geocoder import OpenCageGeocode
from datetime import datetime

# Clave de API de OpenCage
API_KEY = '83d69dc8ddf54be29e0dbe921396a26c'
geocoder = OpenCageGeocode(API_KEY)

# Lista de países de América Latina y Europa
paises_latam_europa = [
    "Argentina", "Bolivia", "Brasil", "Chile", "Colombia", "Costa Rica", "Cuba", 
    "Ecuador", "El Salvador", "Guatemala", "Honduras", "Mexico", "Nicaragua", "Panamá", 
    "Paraguay", "Perú", "Uruguay", "Venezuela", "España", "Francia", "Italia", 
    "Alemania", "Reino Unido", "Portugal"
]

# Función para obtener latitud y longitud basadas en el código postal y país
def obtener_coordenadas_por_codigo_postal(codigo_postal, pais):
    query = f"{codigo_postal}, {pais}"
    results = geocoder.geocode(query)
    if results and len(results) > 0:
        return results[0]['geometry']['lat'], results[0]['geometry']['lng']
    else:
        return None, None

# Función para obtener la ubicación aproximada de un clúster basado en la latitud y longitud más repetida
def obtener_ubicacion_aproximada(cluster_data):
    lat_long = list(zip(cluster_data['latitud'], cluster_data['longitud']))
    coord_mas_repetida = Counter(lat_long).most_common(1)[0][0]

    geolocator = Nominatim(user_agent="mi_sistema_de_clustering")
    try:
        location = geolocator.reverse(coord_mas_repetida, language='es')
        return location.address if location else "Ubicación no encontrada"
    except Exception as e:
        return str(e)

# Función para guardar resultados y ubicación en un archivo CSV con fecha y hora
def guardar_en_archivo(resultados, latitud, longitud):
    with open('resultados.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        fecha_hora_actual = datetime.now().strftime('%Y-%m-%d %H:%M')
        writer.writerow([*resultados.values(), latitud, longitud, fecha_hora_actual])

# Algoritmo de clustering con un radio fijo de 3 kilómetros utilizando DBSCAN
def clustering_ajustado(data):
    coords = data[['latitud', 'longitud']].to_numpy()

    if np.isnan(coords).any():
        st.error("Existen valores nulos en las coordenadas. Verifica los datos.")
        return data

    kms_per_radian = 6371.0088  # radio de la Tierra en km
    epsilon = 3 / kms_per_radian  # Fijar el radio a 3 km, convertido a radianes

    db = DBSCAN(eps=epsilon, min_samples=2, algorithm='ball_tree', metric='haversine').fit(np.radians(coords))
    data['cluster'] = db.labels_

    return data

# Función para calcular la matriz de transición por clúster y mostrar el formato solicitado
def calcular_matriz_transicion(data):
    clústeres = data['cluster'].unique()
    resultados = []

    for clúster in clústeres:
        if clúster == -1:
            continue

        cluster_data = data[data['cluster'] == clúster]
        numero_elementos = len(cluster_data)
        ubicacion_aproximada = obtener_ubicacion_aproximada(cluster_data)

        transiciones = {'Baja': 0, 'Moderada': 0, 'Alta': 0}
        for _, row in cluster_data.iterrows():
            nivel = 'Baja'
            if row['dificultad_respiratoria_grave'] or row['perdida_olfato_gusto'] or row['fatiga_extrema']:
                nivel = 'Alta'
            elif row['tos_perruna'] or row['apnea_bebes'] or row['neumonia_bronquiolitis']:
                nivel = 'Moderada'
            transiciones[nivel] += 1

        total = sum(transiciones.values())
        if total > 0:
            matriz = {nivel: count / total for nivel, count in transiciones.items()}
            resultado = f'Ubicación representativa del cúmulo: {ubicacion_aproximada}, "Baja":{matriz["Baja"]}, "Moderada":{matriz["Moderada"]}, "Alta":{matriz["Alta"]}, cúmulo {clúster} con {numero_elementos} elementos.'
            resultados.append(resultado)
        else:
            resultado = f'Ubicación representativa del cúmulo: {ubicacion_aproximada}, "Baja":{transiciones["Baja"]}, "Moderada":{transiciones["Moderada"]}, "Alta":{transiciones["Alta"]}, cúmulo {clúster} con {numero_elementos} elementos.'
            resultados.append(resultado)

    return resultados

# Interfaz con Streamlit
st.title("Mapa de Riesgo Pandémico")

# Sección: Preguntas sobre síntomas graves
st.header("Síntomas")
dificultad_respiratoria_grave = st.checkbox("¿Ha tenido dificultad respiratoria grave?")
perdida_olfato_gusto = st.checkbox("¿Ha experimentado pérdida repentina del olfato o del gusto?")
fatiga_extrema = st.checkbox("¿Ha tenido fatiga extrema de aparición repentina?")
escalofrios_intensos = st.checkbox("¿Ha sufrido escalofríos intensos acompañados de fiebre alta?")
tos_perruna = st.checkbox("¿Ha presentado tos seca y ronquera severa?")
apnea_bebes = st.checkbox("¿Ha tenido episodios de apnea o problemas respiratorios graves?")
neumonia_bronquiolitis = st.checkbox("¿Le han diagnosticado neumonía o bronquiolitis recientemente?")

# Sección: Preguntas adicionales (sobre condiciones y factores de riesgo)
st.header("Factores")
movilidad_poblacional = st.checkbox("¿Ha viajado o estado en contacto con muchas personas últimamente?")
hacinamiento = st.checkbox("¿Vive en un lugar con alta densidad de personas?")
acceso_servicios = st.checkbox("¿Tiene dificultades para acceder a servicios médicos de calidad?")
contaminacion_aire = st.checkbox("¿Vive en una zona con altos niveles de contaminación del aire?")

# Código Postal y País
st.header("Ubicación")
codigo_postal = st.text_input("Introduce el código postal de la ubicación desde donde respondes este cuestionario")
pais = st.selectbox("Selecciona el país desde el cual respondes este cuestionario", sorted(paises_latam_europa), index=sorted(paises_latam_europa).index("Mexico"))

# Botón para procesar y guardar los datos (incluyendo la obtención automática de coordenadas)
if st.button("Procesar y Guardar"):
    # Obtener coordenadas por código postal y país
    latitud, longitud = obtener_coordenadas_por_codigo_postal(codigo_postal, pais)
    
    if latitud and longitud:
        st.session_state["latitud"] = latitud
        st.session_state["longitud"] = longitud
        
        resultados = {
            'dificultad_respiratoria_grave': dificultad_respiratoria_grave,
            'perdida_olfato_gusto': perdida_olfato_gusto,
            'fatiga_extrema': fatiga_extrema,
            'escalofrios_intensos': escalofrios_intensos,
            'tos_perruna': tos_perruna,
            'apnea_bebes': apnea_bebes,
            'neumonia_bronquiolitis': neumonia_bronquiolitis,
            'movilidad_poblacional': movilidad_poblacional,
            'hacinamiento': hacinamiento,
            'acceso_servicios': acceso_servicios,
            'contaminacion_aire': contaminacion_aire
        }

        # Guardar los datos junto con la ubicación y fecha/hora
        guardar_en_archivo(resultados, latitud, longitud)
        st.success(f"Datos guardados con éxito. Ubicación: Latitud {latitud}, Longitud {longitud}")

        # Leer el archivo CSV para clustering
        try:
            data = pd.read_csv('resultados.csv', names=[
                'dificultad_respiratoria_grave', 'perdida_olfato_gusto', 'fatiga_extrema',
                'escalofrios_intensos', 'tos_perruna', 'apnea_bebes', 'neumonia_bronquiolitis',
                'movilidad_poblacional', 'hacinamiento', 'acceso_servicios', 'contaminacion_aire',
                'latitud', 'longitud', 'fecha_hora'])

            st.write(f"Total de registros cargados: {len(data)}")

            # Realizar clustering con un radio fijo de 3 km
            data_clustering = clustering_ajustado(data)

            clústeres_validos = data_clustering[data_clustering['cluster'] != -1]['cluster'].nunique()
            st.write(f"Se han detectado {clústeres_validos} cúmulos.")

            matrices_transicion = calcular_matriz_transicion(data_clustering)

            # Guardar los resultados en un archivo
            with open('cluster_resultados.csv', 'a', newline='') as file:
                writer = csv.writer(file)
                for resultado in matrices_transicion:
                    st.write(resultado)
                    writer.writerow([resultado])

        except FileNotFoundError:
            st.error("No se encontró el archivo de resultados. Asegúrate de que se haya guardado algún registro.")
    else:
        st.error("No se pudo obtener la ubicación. Verifica el código postal y país.")

