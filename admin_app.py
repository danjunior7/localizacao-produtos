import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Painel Admin - Localização", layout="wide")
st.title("🛠️ Painel de Administração")

# Setup Google Sheets
SHEET_NAME = "Respostas Pesquisa"
escopos = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

# Autenticação
creds_dict = dict(st.secrets["google_service_account"])
creds = Credentials.from_service_account_info(creds_dict, scopes=escopos)
cliente = gspread.authorize(creds)

try:
    planilha = cliente.open(SHEET_NAME)
    abas = planilha.worksheets()
except Exception as e:
    st.error(f"❌ Não foi possível acessar a planilha: {e}")
    st.stop()

# Carregar dados de todas as abas
df_list = []
for aba in abas:
    try:
        dados = aba.get_all_records()
        df_aba = pd.DataFrame(dados)
        df_aba["LOJA"] = aba.title  # Garante que cada aba tem a loja
        df_list.append(df_aba)
    except:
        continue

if not df_list:
    st.warning("⚠️ Nenhum dado encontrado na planilha.")
    st.stop()

df = pd.concat(df_list, ignore_index=True)

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
        df_filtros["DATA"] = pd.to_datetime(df_filtros["DATA"], errors='coerce')
        df_filtros = df_filtros[
            (df_filtros["DATA"] >= pd.to_datetime(filtro_data[0])) &
            (df_filtros["DATA"] <= pd.to_datetime(filtro_data[1]))
        ]

# Exibir dados
st.subheader(f"📄 Respostas filtradas: {len(df_filtros)} registros")
st.dataframe(df_filtros, use_container_width=True)

# Exportar Excel
def gerar_excel(df):
    from io import BytesIO
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Respostas")
    output.seek(0)
    return output

excel_bytes = gerar_excel(df_filtros)
st.download_button("📥 Baixar Excel filtrado", data=excel_bytes, file_name="respostas_admin.xlsx")

