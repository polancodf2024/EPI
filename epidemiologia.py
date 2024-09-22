import csv
import numpy as np
from geopy.geocoders import Nominatim
from sklearn.cluster import DBSCAN
import pandas as pd
import streamlit as st
from collections import Counter

# Inicializar el geolocalizador de Nominatim
geolocator = Nominatim(user_agent="mi_sistema_de_clustering")

# Función para obtener la ubicación a partir de la geolocalización
def obtener_ubicacion_automatica():
    # Utilizando Nominatim de OpenStreetMap para obtener la ubicación real del usuario
    try:
        location = geolocator.geocode("San Jerónimo Lídice, Ciudad de México, 10200")
        if location:
            return location.latitude, location.longitude
        else:
            return None, None
    except Exception as e:
        return None, None

# Función para obtener la ubicación aproximada de un clúster basado en la latitud y longitud más repetida
def obtener_ubicacion_aproximada(cluster_data):
    # Extraer latitud y longitud de los registros del clúster
    lat_long = list(zip(cluster_data['latitud'], cluster_data['longitud']))
    
    # Contar cuál es la latitud/longitud más repetida
    coord_mas_repetida = Counter(lat_long).most_common(1)[0][0]
    
    # Realizar geocodificación inversa para obtener la dirección
    try:
        location = geolocator.reverse(coord_mas_repetida, language='es')
        return location.address if location else "Ubicación no encontrada"
    except Exception as e:
        return str(e)

# Función para guardar respuestas y ubicación en un archivo CSV
def guardar_en_archivo(respuestas, latitud, longitud):
    with open('respuestas.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([*respuestas.values(), latitud, longitud])

# Algoritmo de clustering con un radio de 3 km utilizando DBSCAN
def clustering_3km(data):
    coords = data[['latitud', 'longitud']].to_numpy()
    kms_per_radian = 6371.0088  # radio de la tierra en km
    epsilon = 3 / kms_per_radian  # 3 km en radianes
    
    # DBSCAN con distancia en coordenadas geográficas
    db = DBSCAN(eps=epsilon, min_samples=1, algorithm='ball_tree', metric='haversine').fit(np.radians(coords))
    data['cluster'] = db.labels_
    return data

# Función para calcular la matriz de transición por clúster y mostrar número de elementos y ubicación
def calcular_matriz_transicion(data):
    clústeres = data['cluster'].unique()
    resultados = {}
    
    for clúster in clústeres:
        if clúster == -1:
            continue  # Ignorar ruido (puntos sin clúster)
        
        cluster_data = data[data['cluster'] == clúster]
        numero_elementos = len(cluster_data)
        
        # Obtener la ubicación aproximada basada en la coordenada más repetida
        ubicacion_aproximada = obtener_ubicacion_aproximada(cluster_data)
        
        # Contar transiciones entre niveles de peligrosidad
        transiciones = {'Baja': 0, 'Moderada': 0, 'Alta': 0}
        for _, row in cluster_data.iterrows():
            # Determinar el nivel de peligrosidad
            nivel = 'Baja'
            if row['dificultad_respiratoria_grave'] or row['perdida_olfato_gusto'] or row['fatiga_extrema']:
                nivel = 'Alta'
            elif row['tos_perruna'] or row['apnea_bebes'] or row['neumonia_bronquiolitis']:
                nivel = 'Moderada'
            transiciones[nivel] += 1
        
        # Calcular matriz de transición
        total = sum(transiciones.values())
        if total > 0:
            matriz = {nivel: count / total for nivel, count in transiciones.items()}
            resultados[clúster] = {"matriz": matriz, "elementos": numero_elementos, "ubicacion": ubicacion_aproximada}
        else:
            resultados[clúster] = {"matriz": transiciones, "elementos": numero_elementos, "ubicacion": ubicacion_aproximada}
    
    return resultados

# Interfaz con Streamlit
st.title("Evaluación de Riesgo Epidémico por Enfermedades Respiratorias")

# Sección: Preguntas sobre síntomas graves
st.header("Evaluación de Síntomas Graves")
dificultad_respiratoria_grave = st.checkbox("¿Ha experimentado dificultad respiratoria grave?")
perdida_olfato_gusto = st.checkbox("¿Ha tenido pérdida repentina del olfato o del gusto?")
fatiga_extrema = st.checkbox("¿Ha tenido fatiga extrema que comenzó rápidamente?")
escalofrios_intensos = st.checkbox("¿Ha notado escalofríos intensos con fiebre alta?")
tos_perruna = st.checkbox("¿Ha presentado tos perruna o ronquera grave?")
apnea_bebes = st.checkbox("¿Ha sufrido de apnea o problemas respiratorios graves en bebés?")
neumonia_bronquiolitis = st.checkbox("¿Le han diagnosticado neumonía o bronquiolitis recientemente?")

# Sección: Preguntas adicionales (puedes añadir más preguntas aquí)
st.header("Evaluación de Condiciones y Factores de Riesgo")
movilidad_poblacional = st.checkbox("¿Ha viajado o estado en contacto con muchas personas recientemente?")
hacinamiento = st.checkbox("¿Vive en un lugar con alta densidad de personas?")
acceso_servicios = st.checkbox("¿Tiene acceso limitado a servicios médicos de calidad?")
contaminacion_aire = st.checkbox("¿Vive en una zona con altos niveles de contaminación del aire?")

# Botón para procesar y guardar los datos
if st.button("Procesar y Guardar"):
    # Obtener la ubicación automáticamente
    latitud, longitud = obtener_ubicacion_automatica()
    
    # Recopilar todas las respuestas en un diccionario
    respuestas = {
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
    
    # Verificar si se pudo obtener la ubicación
    if latitud is not None and longitud is not None:
        guardar_en_archivo(respuestas, latitud, longitud)
        st.success(f"Datos guardados con éxito. Ubicación: {latitud}, {longitud}")
    else:
        guardar_en_archivo(respuestas, None, None)
        st.error("No se pudo obtener la ubicación, pero los datos fueron guardados sin la ubicación.")
    
    # Leer el archivo CSV para clustering
    try:
        data = pd.read_csv('respuestas.csv', names=[
            'dificultad_respiratoria_grave', 'perdida_olfato_gusto', 'fatiga_extrema',
            'escalofrios_intensos', 'tos_perruna', 'apnea_bebes', 'neumonia_bronquiolitis',
            'movilidad_poblacional', 'hacinamiento', 'acceso_servicios', 'contaminacion_aire',
            'latitud', 'longitud'])
        
        # Realizar clustering con un radio de 3 km
        data_clustering = clustering_3km(data)
        
        # Excluir ruido (-1) de los clústeres
        clústeres_validos = data_clustering[data_clustering['cluster'] != -1]['cluster'].nunique()
        st.write(f"Se han detectado {clústeres_validos} clústeres.")
        
        # Calcular la matriz de transición por clúster y mostrar número de elementos y ubicación
        matrices_transicion = calcular_matriz_transicion(data_clustering)
        
        for clúster, info in matrices_transicion.items():
            st.write(f"Matriz de transición para el clúster {clúster} con {info['elementos']} elementos:")
            st.write(info['matriz'])
            st.write(f"Ubicación representativa del clúster: {info['ubicacion']}")
    
    except FileNotFoundError:
        st.error("No se encontró el archivo de respuestas. Asegúrate de que se haya guardado algún registro.")

