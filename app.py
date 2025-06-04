import streamlit as st
import pandas as pd
import os
from datetime import datetime
from fpdf import FPDF

st.set_page_config(page_title="Localização de Produtos", layout="wide")

# Função para listar pesquisas salvas no /tmp
def listar_pesquisas_salvas():
    arquivos = os.listdir("/tmp")
    return [f.replace("progresso_", "").replace(".xlsx", "") for f in arquivos if f.startswith("progresso_")]

# Função para carregar o progresso
def carregar_progresso(nome_pesquisa):
    caminho = f"/tmp/progresso_{nome_pesquisa}.xlsx"
    if os.path.exists(caminho):
        return pd.read_excel(caminho)
    else:
        return pd.DataFrame(columns=["Produto", "Local", "Usuário", "Data", "Validade"])

# Função para salvar progresso
def salvar_progresso(nome_pesquisa, df):
    caminho = f"/tmp/progresso_{nome_pesquisa}.xlsx"
    df.to_excel(caminho, index=False)

# Função para gerar PDF
def gerar_pdf(nome_pesquisa, df_filtrado):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, f"Relatório da Pesquisa: {nome_pesquisa}", ln=True)

    # Resumo
    total = len(df_filtrado)
    respondidos = df_filtrado["Local"].notna().sum()
    nao_respondidos = total - respondidos
    locais_informados = df_filtrado["Local"].nunique()

    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Total de Itens: {total}", ln=True)
    pdf.cell(0, 10, f"Respondidos: {respondidos}", ln=True)
    pdf.cell(0, 10, f"Não Respondidos: {nao_respondidos}", ln=True)
    pdf.cell(0, 10, f"Locais diferentes informados: {locais_informados}", ln=True)
    pdf.ln(10)

    # Cabeçalho da tabela
    pdf.set_font("Arial", "B", 11)
    pdf.cell(60, 10, "Produto", border=1)
    pdf.cell(40, 10, "Local", border=1)
    pdf.cell(40, 10, "Validade", border=1)
    pdf.cell(50, 10, "Usuário", border=1)
    pdf.ln()

    pdf.set_font("Arial", "", 10)
    for _, row in df_filtrado.iterrows():
        pdf.cell(60, 10, str(row["Produto"])[:25], border=1)
        pdf.cell(40, 10, str(row["Local"])[:15], border=1)
        pdf.cell(40, 10, str(row["Validade"])[:15], border=1)
        pdf.cell(50, 10, str(row["Usuário"])[:20], border=1)
        pdf.ln()

    nome_pdf = f"/tmp/relatorio_{nome_pesquisa}.pdf"
    pdf.output(nome_pdf)
    return nome_pdf

# --- INTERFACE ---

st.title("📦 Localização de Produtos nas Lojas")

# Lista de usuários permitidos
usuarios_padrao = ["Daniel Ramos", "Wislley"]
usuario = st.selectbox("Selecione seu nome", [""] + usuarios_padrao)

if not usuario:
    st.warning("Por favor, selecione seu nome para continuar.")
    st.stop()

# Lista de pesquisas salvas
lista_pesquisas = listar_pesquisas_salvas()
pesquisa_selecionada = st.selectbox("Selecione a pesquisa", [""] + lista_pesquisas)

if not pesquisa_selecionada:
    st.warning("Por favor, selecione a pesquisa.")
    st.stop()

df = carregar_progresso(pesquisa_selecionada)

# Filtros
st.sidebar.header("Filtros")
filtro_produto = st.sidebar.text_input("Filtrar por nome do produto")
filtro_data = st.sidebar.date_input("Filtrar por data", value=None)
filtro_usuario = st.sidebar.selectbox("Filtrar por usuário", ["Todos"] + usuarios_padrao)

df_filtrado = df.copy()
if filtro_produto:
    df_filtrado = df_filtrado[df_filtrado["Produto"].str.contains(filtro_produto, case=False, na=False)]

if filtro_data:
    df_filtrado = df_filtrado[df_filtrado["Data"] == pd.to_datetime(filtro_data)]

if filtro_usuario != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Usuário"] == filtro_usuario]

# Interface principal
st.subheader(f"Pesquisa: {pesquisa_selecionada}")
st.write("Clique em cada linha para preencher as informações:")

for i in df_filtrado.index:
    with st.expander(f"{df_filtrado.at[i, 'Produto']}"):
        local = st.text_input("Local encontrado", value=df_filtrado.at[i, "Local"] or "", key=f"local_{i}")
        validade = st.text_input("Validade (ex: 20/02/2024)", value="" if pd.isna(df_filtrado.at[i, "Validade"]) else df_filtrado.at[i, "Validade"], key=f"validade_{i}")
        if st.button("Salvar", key=f"salvar_{i}"):
            df.at[i, "Local"] = local
            df.at[i, "Validade"] = validade
            df.at[i, "Usuário"] = usuario
            df.at[i, "Data"] = datetime.today().date()
            salvar_progresso(pesquisa_selecionada, df)
            st.success("Salvo com sucesso!")

# Exportação
st.markdown("---")
if st.button("📄 Exportar em PDF"):
    caminho_pdf = gerar_pdf(pesquisa_selecionada, df)
    with open(caminho_pdf, "rb") as f:
        st.download_button(label="📥 Baixar Relatório em PDF", data=f, file_name=f"Relatorio_{pesquisa_selecionada}.pdf")

