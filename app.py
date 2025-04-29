import streamlit as st
import pandas as pd
import datetime
import os
from openpyxl import load_workbook

import gspread
from google.oauth2.service_account import Credentials

# Configuração da página
st.set_page_config(page_title="Localização de Produtos", layout="centered")
st.title("📦 Localização de Produtos nas Lojas")

# 1. Identificação do usuário
st.subheader("👤 Identificação")
nome_usuario = st.text_input("Digite seu nome:")
data_preenchimento = st.date_input("Data de preenchimento:", value=datetime.date.today())

st.markdown("---")

# 2. Carrega os dados principais (apenas o admin coloca os itens)
@st.cache_data
def carregar_dados():
    return pd.read_excel("Feedback_Localizacao.xlsx")

try:
    df = carregar_dados()
except FileNotFoundError:
    st.error("Arquivo 'Feedback_Localizacao.xlsx' não encontrado.")
    st.stop()

if not nome_usuario:
    st.warning("⚠️ Por favor, digite seu nome para continuar.")
    st.stop()

if "PESQUISA" not in df.columns:
    st.error("❌ A planilha precisa da coluna 'PESQUISA'.")
    st.stop()

# Google Sheets - Setup
SHEET_NAME = "Respostas Pesquisa"

def salvar_google_sheets(respostas):
    try:
        st.write("🔍 Secrets carregado:", st.secrets)

        escopos = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds_dict = st.secrets["google_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=escopos)
        cliente = gspread.authorize(creds)
        planilha = cliente.open(SHEET_NAME)

        for resposta in respostas:
            nome_aba = resposta.get("LOJA", "Sem Loja")

            try:
                aba = planilha.worksheet(nome_aba)
            except gspread.exceptions.WorksheetNotFound:
                aba = planilha.add_worksheet(title=nome_aba, rows="1000", cols="20")
                cabecalhos = list(resposta.keys())
                aba.append_row(cabecalhos)

            valores = list(resposta.values())
            aba.append_row(valores)

        st.success("✅ Respostas enviadas para o Google Sheets com sucesso!")
    except Exception as e:
        st.error(f"Erro ao salvar no Google Sheets: {e}")

# 4. Opções de pesquisa com status
RESP_ARQ = "respostas.xlsx"
expected_cols = [
    "USUÁRIO", "DATA", "PESQUISA", "LOJA", "DESCRIÇÃO", "COD.INT", "EAN", "ESTOQUE",
    "DIAS SEM MOVIMENTAÇÃO", "SEÇÃO", "LOCAL INFORMADO"
]

if os.path.exists(RESP_ARQ):
    try:
        df_resp = pd.read_excel(RESP_ARQ)
        for col in expected_cols:
            if col not in df_resp.columns:
                df_resp[col] = None
        df_resp = df_resp[expected_cols]
    except Exception:
        st.warning("⚠️ Arquivo 'respostas.xlsx' está corrompido. Iniciando vazio.")
        df_resp = pd.DataFrame(columns=expected_cols)
else:
    df_resp = pd.DataFrame(columns=expected_cols)

pesquisas = sorted(df["PESQUISA"].dropna().unique())
options = []
mapa = {}

for pesq in pesquisas:
    total = len(df[df["PESQUISA"] == pesq])
    responded = df_resp[df_resp["PESQUISA"] == pesq].shape[0]
    badge = "🆕" if responded == 0 else ("🔴" if responded < total else "✔️")
    label = f"{pesq} {badge}"
    options.append(label)
    mapa[label] = pesq

st.subheader("🔍 Selecione a pesquisa")
selecionado = st.selectbox("Escolha a pesquisa:", options)
pesquisa_selecionada = mapa[selecionado]

st.markdown("---")

# Exibição dos itens
df_filtrado = df[df["PESQUISA"] == pesquisa_selecionada].reset_index(drop=True)

if df_filtrado.empty:
    st.warning("⚠️ Nenhum produto encontrado nesta pesquisa.")
else:
    st.subheader(f"🏷️ Pesquisa: {pesquisa_selecionada}")
    respostas = []

    for idx, row in df_filtrado.iterrows():
        st.markdown("---")
        st.markdown(f"**🛍️ Produto:** {row['DESCRIÇÃO']}")
        st.markdown(f"**🔢 Código Interno:** {row.get('COD.INT','---')}")
        st.markdown(f"**📦 Estoque:** {row.get('ESTOQUE','---')}")
        st.markdown(f"**📆 Dias sem movimentação:** {row.get('DIAS SEM MOVIMENTAÇÃO','---')}")
        st.markdown(f"**🏷️ EAN:** {row.get('EAN','---')}")
        st.markdown(f"**📍 Seção:** {row.get('SEÇÃO','---')}")

        local = st.selectbox(
            f"📍 Onde está o produto ({row['DESCRIÇÃO']}):",
            ["", "SEÇÃO", "DEPÓSITO", "ERRO DE ESTOQUE"],
            key=f"local_{idx}"
        )

        respostas.append({
            "USUÁRIO": nome_usuario,
            "DATA": data_preenchimento.strftime('%Y-%m-%d'),
            "PESQUISA": pesquisa_selecionada,
            "LOJA": row["LOJA"],
            "DESCRIÇÃO": row["DESCRIÇÃO"],
            "COD.INT": row.get("COD.INT", ""),
            "EAN": row.get("EAN", ""),
            "ESTOQUE": row.get("ESTOQUE", ""),
            "DIAS SEM MOVIMENTAÇÃO": row.get("DIAS SEM MOVIMENTAÇÃO", ""),
            "SEÇÃO": row.get("SEÇÃO", ""),
            "LOCAL INFORMADO": local
        })

    # Salvar
    if st.button("📥 Salvar respostas"):
        df_novas = pd.DataFrame(respostas)

        # Salvar local (opcional, se quiser manter backup)
        if os.path.exists(RESP_ARQ):
            with pd.ExcelWriter(RESP_ARQ, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
                wb = writer.book
                ws = wb.active
                startrow = ws.max_row
                df_novas.to_excel(writer, index=False, header=False, startrow=startrow)
        else:
            df_novas.to_excel(RESP_ARQ, index=False)

        # Salvar no Google Sheets
        salvar_google_sheets(respostas)
