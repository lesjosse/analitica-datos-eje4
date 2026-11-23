import streamlit as st
import pandas as pd
import plotly.express as px
from reporte_correo import enviar_reporte_email

st.set_page_config(page_title="Población Total Mundial", layout="wide")

@st.cache_data
def cargar_datos():
    df = pd.read_csv("poblaciontotal.csv", skiprows=3, encoding="latin1")
    df["Country Name"] = df["Country Name"].fillna(df["Country Code"])
    anios = [str(y) for y in range(1960, 2021)]
    df_long = df.melt(
        id_vars=["Country Name", "Country Code", "Indicator Name"],
        value_vars=anios,
        var_name="Año",
        value_name="Poblacion"
    )
    df_long["Año"] = df_long["Año"].astype(int)
    return df_long.dropna(subset=["Poblacion"])

df = cargar_datos()

st.title(" Dashboard 2: Crecimiento de la Población Total")
st.markdown("Análisis demográfico mundial (1960 - 2020) — Fuente: Banco Mundial")

st.sidebar.header("Filtros Demográficos")
paises_default = ["Colombia", "Argentina", "Perú", "España", "Estados Unidos"]
paises_disponibles = sorted(df["Country Name"].unique())
paises_sel = st.sidebar.multiselect(
    "Selecciona países o regiones:",
    options=paises_disponibles,
    default=[p for p in paises_default if p in paises_disponibles]
)
rango_anios = st.sidebar.slider("Rango de años:", 1960, 2020, (1960, 2020))

df_filtrado = df[(df["Country Name"].isin(paises_sel)) & (df["Año"].between(rango_anios[0], rango_anios[1]))]

# KPIs
col1, col2, col3 = st.columns(3)
if not df_filtrado.empty:
    anio_max = df_filtrado["Año"].max()
    pob_actual = df_filtrado[df_filtrado["Año"] == anio_max]["Poblacion"].sum()
    col1.metric(f"Población acumulada seleccionada ({anio_max})", f"{pob_actual:,.0f}")
    col2.metric("Promedio del periodo", f"{df_filtrado['Poblacion'].mean():,.0f}")
    idx_max = df_filtrado["Poblacion"].idxmax()
    col3.metric("Mayor población registrada", f"{df_filtrado.loc[idx_max, 'Poblacion']:,.0f}", df_filtrado.loc[idx_max, "Country Name"])

tab1, tab2, tab3 = st.tabs([" Evolución Demográfica", " Proporción y Comparativa", " Mapa Demográfico"])

with tab1:
    fig_area = px.area(
        df_filtrado, x="Año", y="Poblacion", color="Country Name",
        title="Evolución de la Población Total en el tiempo"
    )
    st.plotly_chart(fig_area, use_container_width=True)

with tab2:
    c1, c2 = st.columns(2)
    ultimo_anio = df_filtrado["Año"].max() if not df_filtrado.empty else 2020
    df_ult = df_filtrado[df_filtrado["Año"] == ultimo_anio]
    fig_pie = px.pie(
        df_ult, names="Country Name", values="Poblacion", hole=0.4,
        title=f"Participación porcentual en {ultimo_anio}"
    )
    c1.plotly_chart(fig_pie, use_container_width=True)

    fig_bar = px.bar(
        df_ult.sort_values("Poblacion", ascending=True),
        x="Poblacion", y="Country Name", orientation="h", color="Country Name",
        title=f"Ranking de Población ({ultimo_anio})"
    )
    c2.plotly_chart(fig_bar, use_container_width=True)

with tab3:
    anio_mapa = st.selectbox("Año a visualizar en el mapa:", sorted(df["Año"].unique(), reverse=True))
    df_mapa = df[(df["Año"] == anio_mapa) & (df["Country Code"] != "WLD")]
    fig_map = px.choropleth(
        df_mapa, locations="Country Code", color="Poblacion",
        hover_name="Country Name", color_continuous_scale="Plasma",
        title=f"Distribución Geográfica de la Población - {anio_mapa}"
    )
    st.plotly_chart(fig_map, use_container_width=True)

st.subheader(" Tabla Estadística y Reporte Automatizado")
if not df_filtrado.empty:
    resumen_df = df_filtrado.groupby("Country Name")["Poblacion"].agg(["count", "mean", "median", "min", "max"]).round(0)
    st.dataframe(resumen_df, use_container_width=True)

    with st.expander(" Programar / Enviar Reporte al Correo del Estudiante"):
        dest = st.text_input("Correo destino (tu correo):", placeholder="estudiante@areandina.edu.co")
        rem = st.text_input("Correo remitente (Gmail):", placeholder="usuario@gmail.com")
        pwd = st.text_input("Contraseña de aplicación de Google:", type="password")
        if st.button("Enviar Reporte Ahora"):
            try:
                enviar_reporte_email(dest, rem, pwd, "Población Total Mundial", resumen_df.to_string(), df_filtrado)
                st.success(f"¡Reporte enviado exitosamente a {dest}!")
            except Exception as e:
                st.error(f"Error al enviar el correo: {e}")