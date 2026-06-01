import streamlit as st
import pandas as pd
import re

SHEET_URL = "https://docs.google.com/spreadsheets/d/1IwcjGY4WhkkAABbyCdZmuOsdWrS99XAf7968rcV7GMg/export?format=csv&gid=1898188061"

df = pd.read_csv(SHEET_URL)

st.write("### Columnas disponibles:")
st.write(df.columns.tolist())

st.write("### Primeras 5 filas:")
st.write(df.head())

st.write("### Datos de la columna 'EFECTIVO RENDIDO' (si existe):")
if "EFECTIVO RENDIDO" in df.columns:
    st.write(df["EFECTIVO RENDIDO"].head())
    st.write(f"Tipo de dato: {df['EFECTIVO RENDIDO'].dtype}")
    st.write(f"Suma: {df['EFECTIVO RENDIDO'].sum()}")
else:
    st.error("La columna 'EFECTIVO RENDIDO' no existe")
