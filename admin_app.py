import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import matplotlib.pyplot as plt
from io import BytesIO
import openpyxl

st.set_page_config(page_title="Painel Admin - Localização", layout="wide")
st.title("🛠️ Painel de Administração")

# Setup Google Sheets
SHEET_NAME = "Respostas Pesquisa"
escopos = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
creds_dict = dict(st.secrets["google_service_account"])
creds = Credentials.from_service_account_info(creds_dict, scopes=escopos)
cliente = gspread.authorize(creds)

# Carrega todas as abas (lojas)
try:
    planilha = cliente.open(SHEET_NAME)
    abas = planilha.worksheets()
except Exception as e:
    st.error(f"❌ Não foi possível acessar a planilha: {e}")
    st.stop()

df_list = []
for aba in abas:
    try:
        dados = aba.get_all_records()
        df_aba = pd.DataFrame(dados)
        df_aba["LOJA"] = aba.title
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

df_filtros = df[df["LOJA"].isin(filtro_loja) & df["PESQUISA"].isin(filtro_pesquisa)]

if filtro_data:
    if isinstance(filtro_data, list) and len(filtro_data) == 2:
        df_filtros["DATA"] = pd.to_datetime(df_filtros["DATA"], errors='coerce')
        df_filtros = df_filtros[
            (df_filtros["DATA"] >= pd.to_datetime(filtro_data[0])) &
            (df_filtros["DATA"] <= pd.to_datetime(filtro_data[1]))
        ]

# Tabela principal
st.subheader(f"📄 Respostas filtradas: {len(df_filtros)} registros")
st.dataframe(df_filtros, use_container_width=True)

# Resumo por loja
st.subheader("📊 Resumo por Loja")
resumo_loja = (
    df_filtros.groupby("LOJA")
    .agg(
        Total_Produtos=("LOCAL INFORMADO", "count"),
        Localizados=("LOCAL INFORMADO", lambda x: (x.isin(["SEÇÃO", "DEPÓSITO"])).sum()),
        Erro_Estoque=("LOCAL INFORMADO", lambda x: (x == "ERRO DE ESTOQUE").sum())
    )
)
resumo_loja["% Localizados"] = (resumo_loja["Localizados"] / resumo_loja["Total_Produtos"]) * 100
resumo_loja["% Erro de Estoque"] = (resumo_loja["Erro_Estoque"] / resumo_loja["Total_Produtos"]) * 100
resumo_loja = resumo_loja.reset_index()

st.dataframe(resumo_loja, use_container_width=True)

# Gráfico de barras
st.subheader("📈 Gráfico de Localização por Loja")
fig, ax = plt.subplots(figsize=(10, 5))
ax.bar(resumo_loja["LOJA"], resumo_loja["% Localizados"], label='% Localizados')
ax.bar(resumo_loja["LOJA"], resumo_loja["% Erro de Estoque"], bottom=resumo_loja["% Localizados"], label='% Erro Estoque')
ax.set_ylabel('Percentual (%)')
ax.set_title('Localização de Produtos por Loja')
ax.legend()
plt.xticks(rotation=45)
st.pyplot(fig)

# Exportar dados filtrados
def gerar_excel(df_exportar):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_exportar.to_excel(writer, index=False, sheet_name="Respostas")
    output.seek(0)
    return output

st.download_button("📥 Baixar Excel com todos os dados filtrados",
    data=gerar_excel(df_filtros),
    file_name="respostas_filtradas.xlsx"
)

# Exportar apenas erros
st.subheader("🚨 Produtos com Erro de Estoque")
df_erros = df_filtros[df_filtros["LOCAL INFORMADO"] == "ERRO DE ESTOQUE"]
if not df_erros.empty:
    st.download_button(
        label="📥 Baixar apenas os erros de estoque",
        data=gerar_excel(df_erros),
        file_name="erros_estoque.xlsx"
    )
else:
    st.info("✅ Nenhum erro de estoque encontrado.")
