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

# CSS para esconder o menu no celular
st.markdown("""
    <style>
    @media (max-width: 768px) {
        section[data-testid="stSidebar"] {
            transform: translateX(-100%);
            transition: all 0.3s ease-in-out;
            position: fixed;
            z-index: 1000;
            height: 100%;
        }
        section[data-testid="stSidebar"][aria-expanded="true"] {
            transform: translateX(0%);
        }
    }
    </style>
""", unsafe_allow_html=True)

st.title("📦 Localização de Produtos nas Lojas")

# Identificação
st.subheader("👤 Identificação")
nome_usuario = st.text_input("Digite seu nome:").strip()
data_preenchimento = st.date_input("Data de preenchimento:", value=datetime.date.today(), format="DD/MM/YYYY")

if not nome_usuario:
    st.warning("⚠️ Por favor, digite seu nome para continuar.")
    st.stop()

# Carrega dados
try:
    df = pd.read_excel("Feedback_Localizacao.xlsx")
except FileNotFoundError:
    st.error("❌ Arquivo 'Feedback_Localizacao.xlsx' não encontrado.")
    st.stop()

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
selecionado = st.selectbox("Escolha a pesquisa:", options)
pesquisa_selecionada = mapa[selecionado]

# Caminho do progresso salvo
nome_limpo = re.sub(r'\W+', '_', nome_usuario.strip())
pesquisa_limpa = re.sub(r'\W+', '_', pesquisa_selecionada.strip())
progresso_path = f"/tmp/progresso_{nome_limpo}_{pesquisa_limpa}.xlsx"

# Carrega progresso salvo se existir
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

# Exibir os itens da pesquisa
respostas = []
df_filtrado = df[df["PESQUISA"] == pesquisa_selecionada].reset_index(drop=True)

if df_filtrado.empty:
    st.warning("⚠️ Nenhum produto encontrado nesta pesquisa.")
    st.stop()

st.subheader(f"📝 Pesquisa: {pesquisa_selecionada}")

for idx, row in df_filtrado.iterrows():
    st.markdown("---")
    st.markdown(f"**🛍️ Produto:** {row['DESCRIÇÃO']}")
    st.markdown(f"**🏷️ EAN:** {row.get('EAN', '---')}")
    st.markdown(f"**🔢 Código Interno:** {row.get('COD.INT', '---')}")
    st.markdown(f"**📦 Estoque:** {row.get('ESTOQUE', '---')}")
    st.markdown(f"**📆 Dias sem movimentação:** {row.get('DIAS SEM MOVIMENTAÇÃO', '---')}")
    st.markdown(f"**📍 Seção:** {row.get('SEÇÃO', '---')}")

    cod_int = row.get("COD.INT", "")
    valor_inicial = progresso_antigo.get(cod_int, {}).get("LOCAL INFORMADO", "")
    validade_inicial = progresso_antigo.get(cod_int, {}).get("VALIDADE", "")

    local = st.selectbox(
        f"📍 Onde está o produto ({row['DESCRIÇÃO']}):",
        ["", "SEÇÃO", "DEPÓSITO", "ERRO DE ESTOQUE"],
        key=f"local_{idx}",
        index=["", "SEÇÃO", "DEPÓSITO", "ERRO DE ESTOQUE"].index(valor_inicial) if valor_inicial in ["SEÇÃO", "DEPÓSITO", "ERRO DE ESTOQUE"] else 0
    )

    validade = st.text_input(
    f"📅 Validade ({row['DESCRIÇÃO']}):",
    value="" if pd.isna(validade_inicial) else str(validade_inicial),
    key=f"validade_{idx}"
)


    respostas.append({
        "USUÁRIO": nome_usuario,
        "DATA": data_preenchimento.strftime('%d/%m/%Y'),
        "PESQUISA": pesquisa_selecionada,
        "LOJA": row["LOJA"],
        "DESCRIÇÃO": row["DESCRIÇÃO"],
        "COD.INT": cod_int,
        "EAN": row.get("EAN", ""),
        "ESTOQUE": row.get("ESTOQUE", ""),
        "DIAS SEM MOVIMENTAÇÃO": row.get("DIAS SEM MOVIMENTAÇÃO", ""),
        "SEÇÃO": row.get("SEÇÃO", ""),
        "LOCAL INFORMADO": local,
        "VALIDADE": validade
    })

# Salva o progresso local
df_temp = pd.DataFrame(respostas)
df_temp.to_excel(progresso_path, index=False)
st.toast("💾 Progresso salvo localmente.", icon="💾")

# Exportar PDF com layout bonito
def exportar_pdf(respostas):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, f"Relatório de Pesquisa - {pesquisa_selecionada}", ln=True, align="C")

    # Resumo
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
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="relatorio_{pesquisa_limpa}.pdf">📄 Baixar PDF</a>'
    st.markdown(href, unsafe_allow_html=True)

# Botão salvar
if st.button("📅 Salvar respostas"):
    df_novas = pd.DataFrame(respostas)
    RESP_ARQ = "respostas.xlsx"
    if os.path.exists(RESP_ARQ):
        with pd.ExcelWriter(RESP_ARQ, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
            wb = writer.book
            ws = wb.active
            startrow = ws.max_row
            df_novas.to_excel(writer, index=False, header=False, startrow=startrow)
    else:
        df_novas.to_excel(RESP_ARQ, index=False)

    # Salva no Google Sheets
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

    # Exportar PDF
    exportar_pdf(respostas)
