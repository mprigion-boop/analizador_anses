import streamlit as st
import PyPDF2
from openai import OpenAI

# 1. Configuración visual de la página web
st.set_page_config(page_title="Asistente Legal ANSeS", page_icon="⚖️", layout="centered")

# 2. El Master Prompt (El mismo que ya teníamos pulido)
PROMPT_MAESTRO = """Actúa como un Abogado Especialista en Derecho de la Seguridad Social (Argentina).

Tu Misión: Analizar un escrito de contestación de demanda presentado por la ANSeS en juicios de reajuste y movilidad. El objetivo es identificar con precisión quirúrgica cada argumento, defensa y excepción planteada para permitir una réplica efectiva.

Dinámica de Procesamiento Interno (Secuencial y Automático):
A continuación te enviaré el texto del documento completo, el cual he dividido internamente en "Partes" secuenciales. Tu tarea es procesarlo siguiendo estrictamente esta secuencia lógica:
1. Lee y analiza exclusivamente la PRIMERA PARTE. Extrae internamente los títulos, argumentos y datos clave.
2. Pasa a la siguiente parte. Analízala con el mismo nivel de detalle y suma esos hallazgos a tu análisis previo.
3. Repite este proceso secuencialmente hasta procesar la ÚLTIMA PARTE.
4. Solo cuando hayas finalizado la lectura de TODO el texto, consolida la información y genera un único informe final utilizando el Formato de Salida.

Protocolo de Análisis:
- Fidelidad Documental Estricta: Basarás tus respuestas únicamente en el texto cargado. No utilices conocimientos externos no citados.
- Mapeo Estructural: Realiza un punteo exhaustivo de todos los títulos y subtítulos del escrito, sin omitir ninguno.
- Detección de Argumentos Clave: Resume el argumento central de la ANSeS. Detecta si exige prueba de "confiscatoriedad" (umbral del 15%) y si existen contradicciones con los datos fácticos del actor.
- Identificación de Variables: Detecta la ley aplicable (24.241, 27.426, Decreto 274/24, 18.037/38, etc.).

Formato de Salida Único:
- Índice Estructural
- Matriz de Defensa
- Tabla de Jurisprudencia Invocada
- Alertas Procesales"""

# 3. Interfaz de Usuario
st.title("⚖️ Analizador de Demandas: ANSeS")
st.write("Sube el expediente en PDF y obtén la estrategia de defensa estructurada en segundos.")

# Barra lateral para configuraciones de seguridad
st.sidebar.header("⚙️ Configuración")
mi_llave = st.sidebar.text_input("Tu API Key de OpenAI", type="password", help="Ingresa tu clave sk-...")

# Zona para arrastrar y soltar el archivo
archivo_subido = st.file_uploader("Arrastra tu expediente PDF aquí", type="pdf")

# Botón de acción principal
if st.button("🚀 Analizar Expediente"):
    if not mi_llave:
        st.warning("⚠️ Por favor, ingresa tu API Key de OpenAI en el panel izquierdo para comenzar.")
    elif archivo_subido is None:
        st.warning("⚠️ Por favor, sube un documento PDF primero.")
    else:
        # Aquí arranca el motor cuando el usuario hace clic
        cliente = OpenAI(api_key=mi_llave)
        texto_completo_para_ia = ""
        paginas_por_bloque = 15
        
        # Elemento visual de "Cargando..."
        with st.spinner('1️⃣ Leyendo y extrayendo texto del documento...'):
            try:
                lector = PyPDF2.PdfReader(archivo_subido)
                total_paginas = len(lector.pages)
                
                texto_bloque_actual = ""
                numero_bloque = 1
                
                for i in range(total_paginas):
                    texto_extraido = lector.pages[i].extract_text()
                    if texto_extraido:
                        texto_bloque_actual += texto_extraido + "\n"
                        
                    if (i + 1) % paginas_por_bloque == 0 or i == total_paginas - 1:
                        texto_completo_para_ia += f"\n\n--- INICIO PARTE {numero_bloque} ---\n"
                        texto_completo_para_ia += texto_bloque_actual
                        texto_completo_para_ia += f"\n--- FIN PARTE {numero_bloque} ---\n"
                        texto_bloque_actual = ""
                        numero_bloque += 1
                        
            except Exception as e:
                st.error(f"Error al leer el PDF: {e}")
                st.stop()

        with st.spinner(f'2️⃣ Procesando {total_paginas} páginas con ChatGPT. Por favor espera...'):
            try:
                respuesta = cliente.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": PROMPT_MAESTRO},
                        {"role": "user", "content": f"Aquí tienes el documento estructurado:\n{texto_completo_para_ia}"}
                    ],
                    temperature=0.2 
                )
                
                informe_final = respuesta.choices[0].message.content
                
                st.success("✅ ¡Análisis completado con éxito!")
                
                # Mostramos el resultado en la pantalla web
                st.markdown("### 📄 Reporte Final")
                st.write(informe_final)
                
                # Botón mágico para descargar el resultado en texto
                st.download_button(
                    label="💾 Descargar Reporte",
                    data=informe_final,
                    file_name="Reporte_Estrategia_ANSeS.txt",
                    mime="text/plain"
                )
                
            except Exception as e:
                st.error(f"Error en la comunicación con la IA: {e}")