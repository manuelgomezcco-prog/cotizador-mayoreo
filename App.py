import streamlit as st
from fpdf import FPDF
import datetime
import os
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import time

# --- CONFIGURACIÓN Y LOGIN ---
st.set_page_config(page_title="Comcast Solar Wholesale ⚡", layout="wide", page_icon="☀️")

# PIN DE ACCESO (Basado en tus preferencias guardadas)
PIN_CORRECTO = "Comcast2026" 

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.markdown("<h2 style='text-align: center; color: #00509E;'>⚡ Sistema de Ventas Mayoreo Comcast</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Introduce el PIN de acceso para comenzar.</p>", unsafe_allow_html=True)
    
    col_login_1, col_login_2, col_login_3 = st.columns([1,2,1])
    with col_login_2:
        pin_ingresado = st.text_input("PIN de Acceso:", type="password")
        if st.button("Ingresar al Cotizador"):
            if pin_ingresado == PIN_CORRECTO:
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("PIN incorrecto.")
    st.stop()

# --- CONEXIÓN A DATOS ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("⚠️ Error de Conexión con la Base de Datos.")

# Configuración del Logo
logo_path = "comcast_logo_FINAL.png.png"

# --- CLASE PDF PROFESIONAL ---
class PDF(FPDF):
    def header(self):
        if os.path.exists(logo_path):
            try: self.image(logo_path, 10, 8, 48) 
            except: pass
        self.set_font("Arial", "B", 15)
        self.set_text_color(0, 80, 158)
        self.cell(0, 10, "COTIZACIÓN MAYOREO COMCAST", 0, 1, "R")
        self.ln(25) 

    def footer(self):
        self.set_y(-35)
        self.set_font("Arial", "I", 8)
        self.set_text_color(100, 100, 100)
        leyenda = "Precios sujetos a cambio sin previo aviso. Moneda: USD. Vigencia 15 días."
        self.multi_cell(0, 4, leyenda, 0, "C")
        self.ln(2)
        self.set_font("Arial", "B", 8)
        self.cell(0, 10, f"Página {self.page_no()}/{{nb}} - Comcast Energía Solar", 0, 0, "C")

# --- INTERFAZ PRINCIPAL ---
st.markdown("<h1 style='text-align: center; color: #00509E;'>Comcast - Cotizador Mayoreo</h1>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🚀 Nueva Cotización", "📂 Historial"])

# Lista de productos (puedes editarla después)
PRODUCTOS_DISPONIBLES = [
    "Panel Solar 620W Monocristalino",
    "Panel Solar 725W Bifacial",
    "Inversor Solis 5kW 1P",
    "Inversor Solis 10kW 3P",
    "Microinversor Hoymiles 2000W",
    "Batería Litio 5.12kWh",
    "Kit Estructura Coplanar",
    "Cable Fotovoltaico 10 AWG (m)"
]

with tab1:
    with st.sidebar:
        st.header("📋 Datos del Cliente")
        cliente = st.text_input("Nombre de la Empresa / Cliente", "Cliente Nuevo")
        vendedor = st.text_input("Vendedor", "Manuel Gomez")
        st.divider()
        st.info("Agrega filas en la tabla central para cotizar.")

    # TABLA DINÁMICA DE PRODUCTOS
    st.subheader("📦 Detalle de Equipos")
    
    if "df_mayoreo" not in st.session_state:
        st.session_state.df_mayoreo = pd.DataFrame(
            [{"Producto": PRODUCTOS_DISPONIBLES[0], "Cantidad": 1, "Precio Unitario (USD)": 0.0}]
        )

    edited_df = st.data_editor(
        st.session_state.df_mayoreo,
        num_rows="dynamic",
        column_config={
            "Producto": st.column_config.SelectboxColumn(
                "Seleccionar Equipo",
                options=PRODUCTOS_DISPONIBLES,
                required=True,
            ),
            "Cantidad": st.column_config.NumberColumn("Cantidad", min_value=1, step=1),
            "Precio Unitario (USD)": st.column_config.NumberColumn("Precio Unit. (USD)", min_value=0.0, format="$%.2f"),
        },
        use_container_width=True,
        key="editor_mayoreo"
    )

    # Cálculos de Totales
    edited_df["Subtotal"] = edited_df["Cantidad"] * edited_df["Precio Unitario (USD)"]
    total_usd = edited_df["Subtotal"].sum()

    st.markdown(f"### Inversión Total: **${total_usd:,.2f} USD**")

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("☁️ Guardar en Google Sheets"):
            try:
                # Resumen para el historial
                detalle_resumen = ", ".join([f"{row['Cantidad']}x {row['Producto']}" for _, row in edited_df.iterrows()])
                df_old = conn.read(ttl=0)
                nuevo = pd.DataFrame([{
                    "Fecha": str(datetime.date.today()), 
                    "Cliente": cliente, 
                    "Equipos": detalle_resumen, 
                    "Total_USD": round(total_usd, 2),
                    "Vendedor": vendedor
                }])
                conn.update(data=pd.concat([df_old, nuevo], ignore_index=True))
                st.success(f"¡Cotización de {cliente} guardada!")
            except Exception as e:
                st.error(f"Error al guardar: {e}")

    with col_b:
        if st.button("📄 Generar PDF"):
            try:
                pdf = PDF()
                pdf.alias_nb_pages()
                pdf.add_page()
                
                # Datos de cabecera
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 10, f"CLIENTE: {cliente.upper()}", ln=True)
                pdf.set_font("Arial", "", 10)
                pdf.cell(0, 7, f"Fecha: {datetime.date.today()}", ln=True)
                pdf.cell(0, 7, f"Atendido por: {vendedor}", ln=True)
                pdf.ln(5)

                # Tabla de productos en PDF
                pdf.set_fill_color(0, 80, 158)
                pdf.set_text_color(255)
                pdf.set_font("Arial", "B", 10)
                pdf.cell(90, 10, " Producto", 1, 0, "L", True)
                pdf.cell(20, 10, "Cant.", 1, 0, "C", True)
                pdf.cell(35, 10, "P. Unit.", 1, 0, "C", True)
                pdf.cell(35, 10, "Subtotal", 1, 1, "C", True)

                pdf.set_text_color(0)
                pdf.set_font("Arial", "", 9)
                for _, row in edited_df.iterrows():
                    pdf.cell(90, 8, f" {row['Producto']}", 1)
                    pdf.cell(20, 8, str(row['Cantidad']), 1, 0, "C")
                    pdf.cell(35, 8, f"${row['Precio Unitario (USD)']:,.2f}", 1, 0, "R")
                    pdf.cell(35, 8, f"${row['Subtotal']:,.2f}", 1, 1, "R")

                pdf.set_font("Arial", "B", 10)
                pdf.cell(145, 10, "TOTAL (USD)  ", 1, 0, "R")
                pdf.cell(35, 10, f"${total_usd:,.2f}", 1, 1, "R")

                pdf_bytes = pdf.output(dest='S').encode('latin-1', errors='replace')
                st.download_button(label="📥 DESCARGAR PDF", data=pdf_bytes, file_name=f"Cotizacion_{cliente}.pdf", mime="application/pdf")
            except Exception as e:
                st.error(f"Error al crear PDF: {e}")

with tab2:
    st.header("📂 Historial de Ventas")
    try:
        data_historial = conn.read(ttl=0)
        st.dataframe(data_historial, use_container_width=True)
    except:
        st.info("Sin datos disponibles en la hoja de cálculo.")
