import csv
import numpy as np
from geopy.geocoders import Nominatim
from sklearn.linear_model import LinearRegression
import pandas as pd
import streamlit as st
from collections import Counter
from opencage.geocoder import OpenCageGeocode
from datetime import datetime
import matplotlib.pyplot as plt

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

# Función para guardar resultados y ubicación en un archivo CSV con fecha y hora
def guardar_en_archivo(resultados, latitud, longitud):
    with open('resultados.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        fecha_hora_actual = datetime.now().strftime('%Y-%m-%d %H:%M')
        writer.writerow([*resultados.values(), latitud, longitud, fecha_hora_actual])

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

        # Leer el archivo CSV para generar el gráfico
        try:
            data = pd.read_csv('resultados.csv', names=[
                'dificultad_respiratoria_grave', 'perdida_olfato_gusto', 'fatiga_extrema',
                'escalofrios_intensos', 'tos_perruna', 'apnea_bebes', 'neumonia_bronquiolitis',
                'movilidad_poblacional', 'hacinamiento', 'acceso_servicios', 'contaminacion_aire',
                'latitud', 'longitud', 'fecha_hora'], parse_dates=['fecha_hora'])

            # Filtrar registros para México
            mexico_lat = 19.0
            mexico_lon = -99.0
            data = data[(data['latitud'] >= mexico_lat - 5) & (data['latitud'] <= mexico_lat + 5) &
                        (data['longitud'] >= mexico_lon - 10) & (data['longitud'] <= mexico_lon + 10)]

            # Convertir fecha_hora a solo fecha
            data['fecha_dia'] = data['fecha_hora'].dt.date

            # Contar las incidencias diarias
            casos_diarios = data.groupby('fecha_dia').size().reset_index(name='casos_diarios')

            # Convertir fecha_dia a datetime
            casos_diarios['fecha_dia'] = pd.to_datetime(casos_diarios['fecha_dia'])

            # Crear la columna de tiempo en días para el ajuste por mínimos cuadrados
            casos_diarios['dias'] = (casos_diarios['fecha_dia'] - casos_diarios['fecha_dia'].min()).dt.days

            # Ajuste por mínimos cuadrados de grado 1
            X = casos_diarios['dias'].values.reshape(-1, 1)
            y = casos_diarios['casos_diarios'].values
            modelo = LinearRegression()
            modelo.fit(X, y)
            y_pred = modelo.predict(X)

            # Configurar el gráfico
            plt.figure(figsize=(10, 6))
            plt.scatter(casos_diarios['dias'], casos_diarios['casos_diarios'], color='black', label='Casos Diarios Reales')
            plt.plot(casos_diarios['dias'], y_pred, color='maroon', linestyle='--', label='Ajuste por Mínimos Cuadrados (Grado 1)')
            plt.axhline(y=10, color='darkgreen', linestyle='-.', label='Umbral = 10')
            plt.xlabel('Tiempo (días)')
            plt.ylabel('Casos Diarios')
            plt.title('Comparación de Casos Diarios y Ajuste por Mínimos Cuadrados (Grado 1)')
            plt.legend()
            plt.grid()
            
            # Guardar y mostrar el gráfico
            plt.savefig('comparacion_casos_minimos_cuadrados.png')
            st.image('comparacion_casos_minimos_cuadrados.png')

        except FileNotFoundError:
            st.error("No se encontró el archivo de resultados. Asegúrate de que se haya guardado algún registro.")
    else:
        st.error("No se pudo obtener la ubicación. Verifica el código postal y país.")

