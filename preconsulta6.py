import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
import smtplib
import ssl

# Establecer la configuración de la página
st.set_page_config(page_title="Consulta de Primera Vez", page_icon="🌞", layout="centered", initial_sidebar_state="auto")

# Estilos CSS personalizados
st.markdown(
    """
    <style>
    /* Establecer el color de fondo a blanco */
    .stApp {
        background-color: white;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Función para enviar el correo electrónico
def enviar_correo(destinatario, nombre):
    smtp_server = "smtp.gmail.com"
    port = 587  # Puerto para usar TLS
    remitente = "abcdf2024dfabc@gmail.com"
    password = "hjdd gqaw vvpj hbsy"  # Tu contraseña de aplicación

    mensaje = f"""\
    Subject: Registro Completo

    Hola {nombre},

    Gracias por completar tu registro en el Instituto Nacional de Cardiología Ignacio Chávez.
    """

    # Establecer conexión segura con el servidor SMTP
    context = ssl.create_default_context()

    try:
        with smtplib.SMTP(smtp_server, port) as server:
            server.starttls(context=context)  # Iniciar una conexión segura
            server.login(remitente, password)  # Autenticarse en el servidor
            server.sendmail(remitente, destinatario, mensaje.encode('utf-8'))  # Enviar el correo
        return True
    except Exception as e:
        print(f"Error al enviar el correo: {e}")
        return False

# Función para guardar los datos en un archivo Excel
def guardar_en_excel(data):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        data.to_excel(writer, index=False, sheet_name='Consulta')
    output.seek(0)
    return output

# Mostrar el logo y títulos
st.image("escudo_COLOR.jpg", width=100)  # Ajustar el tamaño del logo
st.title("Consulta de Primera Vez")
st.subheader("Instituto Nacional de Cardiología Ignacio Chávez")

# Campos del formulario
nombre_completo = st.text_input("Nombre Completo")
genero = st.selectbox("Género", ["Masculino", "Femenino", "Otro"])
fecha_nacimiento = st.date_input("Fecha de Nacimiento", value=None, min_value=pd.Timestamp('1900-01-01'))

# Lista de países con "Mexico" sin acento y como opción predeterminada
paises_america = ["Argentina", "Bolivia", "Brasil", "Canada", "Chile", "Colombia", "Costa Rica", "Cuba", "Ecuador", "El Salvador", "Estados Unidos", "Guatemala", "Honduras", "Mexico", "Nicaragua", "Panama", "Paraguay", "Peru", "Republica Dominicana", "Uruguay", "Venezuela"]
paises_europa = ["Alemania", "España", "Francia", "Italia", "Portugal", "Reino Unido"]

pais_nacimiento = st.selectbox("País de Nacimiento", paises_america + paises_europa, index=paises_america.index("Mexico"))
whatsapp = st.text_input("Número de WhatsApp", placeholder="+521234567890")
correo = st.text_input("Correo Electrónico")
correo_confirmacion = st.text_input("Confirma tu Correo Electrónico")

# Validación y guardado de información
if st.button("Enviar"):
    if not nombre_completo or not whatsapp or not correo or not correo_confirmacion or not fecha_nacimiento:
        st.error("Por favor, completa todos los campos antes de enviar.")
    elif correo != correo_confirmacion:
        st.error("Los correos electrónicos no coinciden.")
    else:
        resultados = {
            "Nombre Completo": nombre_completo,
            "Género": genero,
            "Fecha de Nacimiento": fecha_nacimiento.strftime('%d/%m/%Y'),
            "País de Nacimiento": pais_nacimiento,
            "WhatsApp": whatsapp,
            "Correo Electrónico": correo
        }

        # Convertir a un DataFrame
        df = pd.DataFrame([resultados])
        
        # Guardar los datos en un archivo Excel en memoria
        excel_data = guardar_en_excel(df)

        # Guardar el archivo en el estado de sesión para descargarlo más tarde
        st.session_state['excel_data'] = excel_data
        
        # Enviar el correo electrónico al usuario
        if enviar_correo(correo, nombre_completo):
            st.success("¡Registro completado y correo enviado! Los datos han sido guardados.")
        else:
            st.error("Registro completado, pero hubo un problema al enviar el correo.")

# Botón para descargar el archivo guardado
if 'excel_data' in st.session_state:
    st.download_button(
        label="Descargar Excel",
        data=st.session_state['excel_data'],
        file_name=f"consulta_primera_vez_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx",
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

