import streamlit as st
import PyPDF2
from openai import OpenAI
from docx import Document
from io import BytesIO

# 1. Configuración de la página
st.set_page_config(page_title="Asistente Legal", page_icon="⚖️")

# 2. Master Prompt
PROMPT_MAESTRO = """Actúa como un Abogado Especialista.
Analiza el texto que se enviará a continuación. 
Espera a leer todas las partes para generar un informe final con:
- Índice Estructural
- Matriz de Defensa
- Tabla de Jurisprudencia Invocada
- Alertas Procesales.
Usa un tono profesional y técnico."""

# Función para crear el archivo Word
def crear_word(texto_ia):
    doc = Document()
    doc.add_heading('Reporte de Análisis Legal', 0)
    
    # Dividimos por secciones si la IA usa "###" o similares para dar formato
    for linea in texto_ia.split('\n'):
        if linea.startswith('###'):
            doc.add_heading(linea.replace('###', '').strip(), level=2)
        elif linea.startswith('##'):
            doc.add_heading(linea.replace('##', '').strip(), level=1)
        else:
            doc.add_paragraph(linea)
            
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# 3. Interfaz de Usuario
st.title("⚖️ Analizador de Demandas")
st.sidebar.header("⚙️ Configuración")
mi_llave = st.sidebar.text_input("Tu API Key de OpenAI", type="password")

archivo_subido = st.file_uploader("Sube el PDF del expediente", type="pdf")

if st.button("🚀 Iniciar Análisis"):
    if not mi_llave:
        st.warning("Falta la API Key en el panel izquierdo.")
    elif archivo_subido is None:
        st.warning("Por favor, sube un archivo PDF.")
    else:
        cliente = OpenAI(api_key=mi_llave)
        texto_completo = ""
        
        with st.spinner('Procesando documento...'):
            lector = PyPDF2.PdfReader(archivo_subido)
            for pagina in lector.pages:
                texto_completo += pagina.extract_text() + "\n"
            
            try:
                respuesta = cliente.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": PROMPT_MAESTRO},
                        {"role": "user", "content": texto_completo}
                    ],
                    temperature=0.2
                )
                
                resultado = respuesta.choices[0].message.content
                st.success("¡Análisis Terminado!")
                st.markdown(resultado)
                
                # Generar el archivo Word en memoria
                archivo_word = crear_word(resultado)
                
                # Botón de descarga de Word
                st.download_button(
                    label="📥 Descargar Reporte en Word",
                    data=archivo_word,
                    file_name="Reporte_Legal.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            except Exception as e:
                st.error(f"Error: {e}")
