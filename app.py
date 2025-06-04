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

# Carrega dados
df = pd.read_excel("Feedback_Localizacao.xlsx")
if "PESQUISA" not in df.columns:
    st.error("❌ A planilha precisa da coluna 'PESQUISA'.")
    st.stop()

# Pesquisa
pesquisas = sorted(df["PESQUISA"].dropna().unique())
options = []
mapa = {}
for pesq in pesquisas:
    label = f"{pesq}"
    options.append(label)
    mapa[label] = pesq

st.subheader("🔍 Selecione a pesquisa")
opcoes_selectbox = [""] + options
selecionado = st.selectbox("Escolha a pesquisa:", opcoes_selectbox)
if not selecionado:
    st.warning("⚠️ Por favor, selecione uma pesquisa.")
    st.stop()

pesquisa_selecionada = mapa[selecionado]
nome_limpo = re.sub(r'\W+', '_', nome_usuario.strip())
pesquisa_limpa = re.sub(r'\W+', '_', pesquisa_selecionada.strip())
progresso_path = f"/tmp/progresso_{nome_limpo}_{pesquisa_limpa}.xlsx"

# Carrega progresso salvo
progresso_antigo = {}
if os.path.exists(progresso_path):
    try:
        df_antigo = pd.read_excel(progresso_path)
        for _, row in df_antigo.iterrows():
            progresso_antigo[row["COD.INT"]] = {
                "LOCAL INFORMADO": row["LOCAL INFORMADO"],
                "VALIDADE": row.get("VALIDADE", "")
            }
        st.info("🔄 Progresso anterior carregado automaticamente.")
    except:
        st.warning("⚠️ Não foi possível carregar progresso anterior.")

# Exibir os itens da pesquisa com paginação
df_filtrado = df[df["PESQUISA"] == pesquisa_selecionada].reset_index(drop=True)
if df_filtrado.empty:
    st.warning("⚠️ Nenhum produto encontrado nesta pesquisa.")
    st.stop()

st.subheader(f"📝 Pesquisa: {pesquisa_selecionada}")

# Paginação
itens_por_pagina = 20
total_paginas = (len(df_filtrado) - 1) // itens_por_pagina + 1
if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = 1
pagina = st.number_input("Página:", min_value=1, max_value=total_paginas, value=st.session_state.pagina_atual, step=1)
st.session_state.pagina_atual = pagina

inicio = (pagina - 1) * itens_por_pagina
fim = inicio + itens_por_pagina
df_pagina = df_filtrado.iloc[inicio:fim]

respostas = []

for idx, row in df_pagina.iterrows():
    st.markdown("---")
    st.markdown(f"**🛍️ Produto:** {row['DESCRIÇÃO']}")
    st.markdown(f"**🏷️ EAN:** {row.get('EAN', '---')}")
    st.markdown(f"**🔢 Código Interno:** {row.get('COD.INT', '---')}")
    st.markdown(f"**📦 Estoque:** {row.get('ESTOQUE', '---')}")
    st.markdown(f"**📆 Dias sem movimentação:** {row.get('DIAS SEM MOVIMENTAÇÃO', '---')}")
    st.markdown(f"**📍 Seção:** {row.get('SEÇÃO', '---')}")

    cod_int = row.get("COD.INT", f"vazio_{idx}")
    valor_inicial = progresso_antigo.get(cod_int, {}).get("LOCAL INFORMADO", "")
    validade_raw = progresso_antigo.get(cod_int, {}).get("VALIDADE", "")
    validade_inicial = "" if pd.isna(validade_raw) else str(validade_raw)

    local = st.selectbox(
        f"📍 Onde está o produto ({row['DESCRIÇÃO']}):",
        ["", "SEÇÃO", "DEPÓSITO", "ERRO DE ESTOQUE"],
        key=f"local_{cod_int}_{idx}",
        index=["", "SEÇÃO", "DEPÓSITO", "ERRO DE ESTOQUE"].index(valor_inicial)
        if valor_inicial in ["SEÇÃO", "DEPÓSITO", "ERRO DE ESTOQUE"] else 0
    )

    validade = st.text_input(
        f"📅 Validade ({row['DESCRIÇÃO']}):",
        value=validade_inicial,
        key=f"validade_{cod_int}_{idx}"
    )

    respostas.append({
        "USUÁRIO": nome_usuario,
        "DATA": data_preenchimento.strftime('%d/%m/%Y'),
        "PESQUISA": pesquisa_selecionada,
        "LOJA": row.get("LOJA", ""),
        "DESCRIÇÃO": row.get("DESCRIÇÃO", ""),
        "COD.INT": cod_int,
        "EAN": row.get("EAN", ""),
        "ESTOQUE": row.get("ESTOQUE", ""),
        "DIAS SEM MOVIMENTAÇÃO": row.get("DIAS SEM MOVIMENTAÇÃO", ""),
        "SEÇÃO": row.get("SEÇÃO", ""),
        "LOCAL INFORMADO": local,
        "VALIDADE": validade
    })

# Salvar localmente
df_temp = pd.DataFrame(respostas)
df_temp.to_excel(progresso_path, index=False)
st.toast("💾 Progresso salvo localmente.", icon="💾")

# Botões finais
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    if st.button("📤 Enviar respostas para o Google Sheets"):
        try:
            scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
            creds_dict = dict(st.secrets["google_service_account"])
            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            client = gspread.authorize(creds)
            planilha = client.open("Respostas Pesquisa")

            abas_dict = {}
            for resposta in respostas:
                aba = resposta.get("LOJA", "Sem Loja")
                if aba not in abas_dict:
                    abas_dict[aba] = []
                abas_dict[aba].append(resposta)

            for aba, valores in abas_dict.items():
                try:
                    aba_sheet = planilha.worksheet(aba)
                except:
                    aba_sheet = planilha.add_worksheet(title=aba, rows="1000", cols="20")
                    aba_sheet.append_row(list(valores[0].keys()))
                aba_sheet.append_rows([list(r.values()) for r in valores])

            st.success("✅ Respostas enviadas com sucesso!")
        except Exception as e:
            st.error(f"Erro ao salvar no Google Sheets: {e}")

with col2:
    def exportar_pdf(respostas):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, f"Relatório de Pesquisa - {pesquisa_selecionada}", ln=True, align="C")

        df_respostas = pd.DataFrame(respostas)
        total = len(df_respostas)
        respondidos = df_respostas[df_respostas["LOCAL INFORMADO"] != ""].shape[0]
        nao_respondidos = total - respondidos
        por_local = df_respostas["LOCAL INFORMADO"].value_counts()

        pdf.set_font("Arial", "", 12)
        pdf.ln(10)
        pdf.cell(0, 10, f"Total de itens: {total}", ln=True)
        pdf.cell(0, 10, f"Respondidos: {respondidos}", ln=True)
        pdf.cell(0, 10, f"Não respondidos: {nao_respondidos}", ln=True)
        for local, qtd in por_local.items():
            pdf.cell(0, 10, f"{local}: {qtd}", ln=True)

        pdf.ln(10)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Detalhamento por Produto", ln=True)
        pdf.set_font("Arial", "", 10)

        for r in respostas:
            pdf.ln(5)
            pdf.multi_cell(0, 5,
                f"Produto: {r['DESCRIÇÃO']}\n"
                f"EAN: {r['EAN']}\n"
                f"Cód. Interno: {r['COD.INT']} | Estoque: {r['ESTOQUE']}\n"
                f"Dias sem movimentação: {r['DIAS SEM MOVIMENTAÇÃO']} | Seção: {r['SEÇÃO']}\n"
                f"Local Informado: {r['LOCAL INFORMADO']} | Validade: {r['VALIDADE']}"
            )

        caminho_pdf = f"/tmp/relatorio_{nome_limpo}_{pesquisa_limpa}.pdf"
        pdf.output(caminho_pdf)
        with open(caminho_pdf, "rb") as f:
            pdf_data = f.read()

        b64 = base64.b64encode(pdf_data).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="relatorio_{pesquisa_limpa}.pdf">📄 Baixar Relatório em PDF</a>'
        st.markdown(href, unsafe_allow_html=True)

    if st.button("📄 Gerar Relatório em PDF"):
        exportar_pdf(respostas)
