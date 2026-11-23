import streamlit as st
import pandas as pd
import plotly.express as px
from reporte_correo import enviar_reporte_email

st.set_page_config(page_title="Exportaciones (% del PIB)", layout="wide")

@st.cache_data
def cargar_datos():
    df = pd.read_csv("exportacionesdebienesyserviciosdelpib.csv", skiprows=3, encoding="latin1")
    df["Country Name"] = df["Country Name"].fillna(df["Country Code"])
    anios = [str(y) for y in range(1960, 2021)]
    df_long = df.melt(
        id_vars=["Country Name", "Country Code", "Indicator Name"],
        value_vars=anios,
        var_name="Año",
        value_name="Exportaciones_PIB"
    )
    df_long["Año"] = df_long["Año"].astype(int)
    return df_long.dropna(subset=["Exportaciones_PIB"])

df = cargar_datos()

st.title(" Dashboard 1: Exportaciones de Bienes y Servicios (% del PIB)")
st.markdown("Análisis histórico global (1960 - 2020) — Fuente: Banco Mundial")

# Barra lateral de filtros
st.sidebar.header("Filtros de Exploración")
paises_default = ["Colombia", "Brasil", "México", "Chile", "Estados Unidos", "China"]
paises_disponibles = sorted(df["Country Name"].unique())
paises_sel = st.sidebar.multiselect(
    "Selecciona países o regiones:",
    options=paises_disponibles,
    default=[p for p in paises_default if p in paises_disponibles]
)
rango_anios = st.sidebar.slider("Rango de años:", 1960, 2020, (1990, 2020))

df_filtrado = df[(df["Country Name"].isin(paises_sel)) & (df["Año"].between(rango_anios[0], rango_anios[1]))]

# KPIs principales
col1, col2, col3, col4 = st.columns(4)
if not df_filtrado.empty:
    col1.metric("Promedio (% PIB)", f"{df_filtrado['Exportaciones_PIB'].mean():.2f}%")
    col2.metric("Mediana (% PIB)", f"{df_filtrado['Exportaciones_PIB'].median():.2f}%")
    idx_max = df_filtrado["Exportaciones_PIB"].idxmax()
    col3.metric("Máximo registrado", f"{df_filtrado.loc[idx_max, 'Exportaciones_PIB']:.2f}%", df_filtrado.loc[idx_max, "Country Name"])
    col4.metric("Desviación Estándar", f"{df_filtrado['Exportaciones_PIB'].std():.2f}%")

# Gráficos interactivos
tab1, tab2, tab3 = st.tabs([" Evolución Temporal", " Comparativa y Distribución", " Mapa Mundial"])

with tab1:
    fig_line = px.line(
        df_filtrado, x="Año", y="Exportaciones_PIB", color="Country Name",
        markers=True, title="Tendencia de Exportaciones (% del PIB) en el tiempo",
        labels={"Exportaciones_PIB": "% del PIB", "Country Name": "País/Región"}
    )
    st.plotly_chart(fig_line, use_container_width=True)

with tab2:
    c1, c2 = st.columns(2)
    ultimo_anio = df_filtrado["Año"].max() if not df_filtrado.empty else 2020
    df_ult = df_filtrado[df_filtrado["Año"] == ultimo_anio].sort_values("Exportaciones_PIB", ascending=False)
    fig_bar = px.bar(
        df_ult, x="Country Name", y="Exportaciones_PIB", color="Country Name",
        title=f"Comparación por País en el año {ultimo_anio}"
    )
    c1.plotly_chart(fig_bar, use_container_width=True)

    fig_box = px.box(
        df_filtrado, x="Country Name", y="Exportaciones_PIB", color="Country Name",
        title="Distribución y valores atípicos (Boxplot)"
    )
    c2.plotly_chart(fig_box, use_container_width=True)

with tab3:
    anio_mapa = st.selectbox("Selecciona año para el mapa global:", sorted(df["Año"].unique(), reverse=True))
    df_mapa = df[df["Año"] == anio_mapa]
    fig_map = px.choropleth(
        df_mapa, locations="Country Code", color="Exportaciones_PIB",
        hover_name="Country Name", color_continuous_scale="Viridis",
        title=f"Mapa Global de Exportaciones (% del PIB) - {anio_mapa}"
    )
    st.plotly_chart(fig_map, use_container_width=True)

# Tabla resumen y envío de reporte por correo
st.subheader(" Resumen Estadístico y Envío de Reporte")
if not df_filtrado.empty:
    resumen_df = df_filtrado.groupby("Country Name")["Exportaciones_PIB"].agg(["count", "mean", "median", "min", "max", "std"]).round(2)
    st.dataframe(resumen_df, use_container_width=True)

    with st.expander(" Programar / Enviar Reporte al Correo del Estudiante"):
        dest = st.text_input("Correo destino (tu correo):", placeholder="jecheverri16@estudiantes.areandina.edu.co")
        rem = st.text_input("Correo remitente (Gmail):", placeholder="lesanchez296@gmail.com")
        pwd = st.text_input("Contraseña de aplicación de Google:", type="password")
        if st.button("Enviar Reporte Ahora"):
            try:
                enviar_reporte_email(dest, rem, pwd, "Exportaciones de bienes y servicios (% del PIB)", resumen_df.to_string(), df_filtrado)
                st.success(f"¡Reporte enviado exitosamente a {dest}!")
            except Exception as e:
                st.error(f"Error al enviar el correo: {e}")