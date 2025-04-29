import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Painel Admin - Localização", layout="wide")
st.title("🛠️ Painel de Administração")

RESP_ARQ = "respostas.xlsx"

# Carregar respostas
if not os.path.exists(RESP_ARQ):
    st.warning("⚠️ Nenhum dado encontrado ainda.")
    st.stop()

df = pd.read_excel(RESP_ARQ)

# Filtros
st.sidebar.header("🔎 Filtros")
lojas = sorted(df["LOJA"].dropna().unique())
pesquisas = sorted(df["PESQUISA"].dropna().unique())

filtro_loja = st.sidebar.multiselect("Filtrar por loja:", lojas, default=lojas)
filtro_pesquisa = st.sidebar.multiselect("Filtrar por pesquisa:", pesquisas, default=pesquisas)
filtro_data = st.sidebar.date_input("Filtrar por data:", [])

# Aplicar filtros
df_filtros = df[
    df["LOJA"].isin(filtro_loja) &
    df["PESQUISA"].isin(filtro_pesquisa)
]

if filtro_data:
    if isinstance(filtro_data, list) and len(filtro_data) == 2:
        df_filtros = df_filtros[
            (pd.to_datetime(df_filtros["DATA"]) >= pd.to_datetime(filtro_data[0])) &
            (pd.to_datetime(df_filtros["DATA"]) <= pd.to_datetime(filtro_data[1]))
        ]

# Exibir dados
st.subheader(f"📄 Respostas filtradas: {len(df_filtros)} registros")
st.dataframe(df_filtros, use_container_width=True)

# Download Excel
def converter_para_excel(df):
    from io import BytesIO
    import openpyxl

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Respostas")
    output.seek(0)
    return output

excel_bytes = converter_para_excel(df_filtros)
st.download_button("📥 Baixar Excel com os dados filtrados", data=excel_bytes, file_name="respostas_filtradas.xlsx")
