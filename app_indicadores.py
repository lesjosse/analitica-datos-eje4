import streamlit as st
import pandas as pd
import plotly.express as px
from reporte_correo import enviar_reporte_email

st.set_page_config(page_title="Indicadores del Desarrollo Mundial", layout="wide")

@st.cache_data
def cargar_datos():
    df = pd.read_csv("wIndicadoresdeldesarrollomundial.csv", skiprows=3, encoding="latin1")
    df["Indicador_Completo"] = df["Indicator Name"] + " [" + df["Indicator Code"] + "]"
    anios = [str(y) for y in range(1960, 2021)]
    df_long = df.melt(
        id_vars=["Indicador_Completo", "Indicator Name", "Indicator Code"],
        value_vars=anios,
        var_name="Año",
        value_name="Valor"
    )
    df_long["Año"] = df_long["Año"].astype(int)
    return df_long.dropna(subset=["Valor"])

df = cargar_datos()

st.title(" Dashboard 3: Indicadores del Desarrollo Mundial (Mundo - WLD)")
st.markdown("Exploración multivariante de 1,442 indicadores globales (1960 - 2020)")

st.sidebar.header("Selección de Indicadores")
indicadores = sorted(df["Indicador_Completo"].unique())
default_ind = next((i for i in indicadores if "IT.NET.USER.ZS" in i), indicadores[0])
ind_principal = st.sidebar.selectbox("Indicador Principal:", indicadores, index=indicadores.index(default_ind))

default_ind2 = next((i for i in indicadores if "MS.MIL.XPND.ZS" in i), indicadores[1])
ind_comparacion = st.sidebar.selectbox("Indicador para Correlación (Eje Y):", indicadores, index=indicadores.index(default_ind2))

rango_anios = st.sidebar.slider("Rango de años:", 1960, 2020, (1980, 2020))

df_p1 = df[(df["Indicador_Completo"] == ind_principal) & (df["Año"].between(rango_anios[0], rango_anios[1]))].sort_values("Año")
df_p2 = df[(df["Indicador_Completo"] == ind_comparacion) & (df["Año"].between(rango_anios[0], rango_anios[1]))].sort_values("Año")

# KPIs
col1, col2, col3, col4 = st.columns(4)
if not df_p1.empty:
    col1.metric("Último valor registrado", f"{df_p1.iloc[-1]['Valor']:,.2f}", f"Año {df_p1.iloc[-1]['Año']}")
    col2.metric("Promedio histórico", f"{df_p1['Valor'].mean():,.2f}")
    col3.metric("Valor mínimo", f"{df_p1['Valor'].min():,.2f}")
    col4.metric("Valor máximo", f"{df_p1['Valor'].max():,.2f}")

tab1, tab2 = st.tabs([" Serie de Tiempo e Histograma", " Análisis de Correlación entre 2 Indicadores"])

with tab1:
    c1, c2 = st.columns([2, 1])
    fig_line = px.line(
        df_p1, x="Año", y="Valor", markers=True,
        title=f"Evolución Mundial: {ind_principal}"
    )
    c1.plotly_chart(fig_line, use_container_width=True)

    fig_hist = px.histogram(
        df_p1, x="Valor", nbins=15,
        title="Distribución de Frecuencias"
    )
    c2.plotly_chart(fig_hist, use_container_width=True)

with tab2:
    df_merge = pd.merge(
        df_p1[["Año", "Valor"]].rename(columns={"Valor": "Indicador_1"}),
        df_p2[["Año", "Valor"]].rename(columns={"Valor": "Indicador_2"}),
        on="Año"
    )
    if len(df_merge) >= 2:
        corr = df_merge["Indicador_1"].corr(df_merge["Indicador_2"])
        st.info(f"**Coeficiente de correlación de Pearson ($r$):** `{corr:.4f}` (entre {df_merge['Año'].min()} y {df_merge['Año'].max()})")
        fig_scatter = px.scatter(
            df_merge, x="Indicador_1", y="Indicador_2", text="Año",
            title="Diagrama de Dispersión entre Indicadores Globales",
            labels={"Indicador_1": ind_principal[:45], "Indicador_2": ind_comparacion[:45]}
        )
        fig_scatter.update_traces(textposition="top center")
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.warning("No hay suficientes años coincidentes entre ambos indicadores para calcular correlación.")

st.subheader(" Resumen Estadístico y Envío de Reporte")
if not df_p1.empty:
    stats_text = df_p1["Valor"].describe().to_string()
    st.code(stats_text)

    with st.expander(" Programar / Enviar Reporte al Correo del Estudiante"):
        dest = st.text_input("Correo destino (tu correo):", placeholder="estudiante@areandina.edu.co")
        rem = st.text_input("Correo remitente (Gmail):", placeholder="tu_usuario@gmail.com")
        pwd = st.text_input("Contraseña de aplicación de Google:", type="password")
        if st.button("Enviar Reporte Ahora"):
            try:
                enviar_reporte_email(dest, rem, pwd, f"Indicadores Mundiales: {ind_principal}", stats_text, df_p1)
                st.success(f"¡Reporte enviado exitosamente a {dest}!")
            except Exception as e:
                st.error(f"Error al enviar el correo: {e}")