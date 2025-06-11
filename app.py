import streamlit as st
import pandas as pd
import datetime
import os
import gspread
from google.oauth2.service_account import Credentials
import re
from fpdf import FPDF
import base64

st.set_page_config(
    page_title="Localização de Produtos",
    layout="wide",
    initial_sidebar_state="auto"
)

st.title("📦 Localização de Produtos nas Lojas")

# Identificação
st.subheader("👤 Identificação")
usuarios_padrao = ["Daniel Ramos", "Wislley"]
nome_usuario = st.selectbox("Selecione seu nome:", [""] + usuarios_padrao)
if not nome_usuario:
    st.warning("⚠️ Por favor, selecione seu nome para continuar.")
    st.stop()

data_preenchimento = st.date_input("Data de preenchimento:", value=datetime.date.today(), format="DD/MM/YYYY")

# Caminho do progresso local temporário
arquivo_progresso = f"/tmp/progresso_{nome_usuario}.xlsx"

# Carregar dados
if os.path.exists(arquivo_progresso):
    df = pd.read_excel(arquivo_progresso)
else:
    df = pd.read_excel("Feedback_Localizacao.xlsx")
    df["Local Informado"] = ""
    df["Validade"] = ""

# Navegação
st.subheader("🔍 Produtos para Localização")
if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = 0

produtos_por_pagina = 1
inicio = st.session_state.pagina_atual * produtos_por_pagina
fim = inicio + produtos_por_pagina
pagina_df = df.iloc[inicio:fim]

if not pagina_df.empty:
    for i, r in pagina_df.iterrows():
        st.markdown(f"### 🛒 Produto: {r['DESCRICAO PRODUTO']}")
        st.markdown(
            f"EAN: {r['EAN']} | Estoque: {r['ESTOQUE']} | Dias s/ mov: {r['DIAS SEM MOVIMENTAÇÃO']}"
        )
        local = st.text_input(f"Informe o local do produto (ID: {r['ID']}):", value=r["Local Informado"], key=f"local_{i}")
        validade = st.text_input(f"Validade (se aplicável):", value=r["Validade"], key=f"validade_{i}")

        df.at[i, "Local Informado"] = local
        df.at[i, "Validade"] = validade

# Botões de navegação
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("⬅️ Voltar") and st.session_state.pagina_atual > 0:
        st.session_state.pagina_atual -= 1
with col2:
    st.write(f"Página {st.session_state.pagina_atual + 1} de {((len(df)-1)//produtos_por_pagina)+1}")
with col3:
    if st.button("➡️ Avançar") and fim < len(df):
        st.session_state.pagina_atual += 1

# Salvamento automático
df.to_excel(arquivo_progresso, index=False)

# Resumo no topo para PDF
def gerar_resumo_respostas(df):
    total = len(df)
    respondidos = df["Local Informado"].astype(str).str.strip().replace("nan", "").replace("None", "").ne("").sum()
    nao_respondidos = total - respondidos
    locais_distintos = df["Local Informado"].dropna().unique()
    return total, respondidos, nao_respondidos, locais_distintos

# Exportar para PDF
def exportar_pdf():
    total, respondidos, nao_respondidos, locais = gerar_resumo_respostas(df)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Relatório de Localização de Produtos", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, f"Usuário: {nome_usuario}", ln=True)
    pdf.cell(0, 10, f"Data de preenchimento: {data_preenchimento.strftime('%d/%m/%Y')}", ln=True)
    pdf.cell(0, 10, f"Total de produtos: {total}", ln=True)
    pdf.cell(0, 10, f"Respondidos: {respondidos}", ln=True)
    pdf.cell(0, 10, f"Não respondidos: {nao_respondidos}", ln=True)
    pdf.cell(0, 10, f"Locais distintos informados: {', '.join(map(str, locais))}", ln=True)
    pdf.ln(10)

    for _, row in df.iterrows():
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, f"Produto: {row['DESCRICAO PRODUTO']}", ln=True)
        pdf.set_font("Arial", '', 11)
        pdf.cell(0, 8, f"EAN: {row['EAN']} | Estoque: {row['ESTOQUE']} | Dias s/ mov: {row['DIAS SEM MOVIMENTAÇÃO']}", ln=True)
        pdf.cell(0, 8, f"Local Informado: {row['Local Informado']}", ln=True)
        pdf.cell(0, 8, f"Validade: {row['Validade']}", ln=True)
        pdf.ln(5)

    pdf_bytes = pdf.output(dest='S').encode('latin1')
    b64 = base64.b64encode(pdf_bytes).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="relatorio_localizacao.pdf">📄 Clique aqui para baixar o PDF</a>'
    st.markdown(href, unsafe_allow_html=True)

st.markdown("---")
if st.button("📤 Exportar Respostas em PDF"):
    exportar_pdf()
