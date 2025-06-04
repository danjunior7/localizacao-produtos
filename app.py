import streamlit as st
import pandas as pd
import datetime
import os
import gspread
from google.oauth2.service_account import Credentials
import re
from fpdf import FPDF

# Configuração da página
st.set_page_config(
    page_title="Localização de Produtos",
    layout="wide",
    initial_sidebar_state="auto"
)

# CSS para menu responsivo
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
data_preenchimento = st.date_input("Data de preenchimento:", value=datetime.date.today())

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
selecionado = st.selectbox("🔍 Escolha a pesquisa:", pesquisas)
pesquisa_selecionada = selecionado

# Caminho do progresso salvo
nome_limpo = re.sub(r'\W+', '_', nome_usuario)
pesquisa_limpa = re.sub(r'\W+', '_', pesquisa_selecionada)
progresso_path = f"/tmp/progresso_{nome_limpo}_{pesquisa_limpa}.xlsx"

# Carrega progresso salvo se existir
progresso_antigo = {}
if os.path.exists(progresso_path):
    try:
        df_antigo = pd.read_excel(progresso_path)
        for _, row in df_antigo.iterrows():
            progresso_antigo[row["COD.INT"]] = (row["LOCAL INFORMADO"], row.get("VALIDADE", ""))
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

    local_key = f"local_{idx}"
    validade_key = f"validade_{idx}"

    valor_inicial, validade_inicial = progresso_antigo.get(row.get("COD.INT", ""), ("", ""))
    local = st.selectbox(
        f"📍 Onde está o produto ({row['DESCRIÇÃO']}):",
        ["", "SEÇÃO", "DEPÓSITO", "ERRO DE ESTOQUE"],
        key=local_key,
        index=["", "SEÇÃO", "DEPÓSITO", "ERRO DE ESTOQUE"].index(valor_inicial) if valor_inicial in ["SEÇÃO", "DEPÓSITO", "ERRO DE ESTOQUE"] else 0
    )
    validade = st.text_input(f"📅 Validade do produto ({row['DESCRIÇÃO']}):", value=validade_inicial, key=validade_key)

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
        "LOCAL INFORMADO": local,
        "VALIDADE": validade
    })

# Salva localmente
df_temp = pd.DataFrame(respostas)
df_temp.to_excel(progresso_path, index=False)
st.toast("💾 Progresso salvo localmente (automático).", icon="💾")

# Botão para exportar PDF
def gerar_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, f"Relatório da Pesquisa: {pesquisa_selecionada}", ln=True)

    total = len(df)
    respondidos = df["LOCAL INFORMADO"].apply(lambda x: x.strip() != "").sum()
    nao_respondidos = total - respondidos
    locais = df["LOCAL INFORMADO"].value_counts().to_dict()

    pdf.set_font("Arial", "", 12)
    pdf.ln(5)
    pdf.multi_cell(0, 8, f"Usuário: {nome_usuario}\nData: {data_preenchimento.strftime('%d/%m/%Y')}\n"
                         f"Total de Itens: {total}\nRespondidos: {respondidos}\nNão Respondidos: {nao_respondidos}")
    for local, qtd in locais.items():
        pdf.cell(0, 8, f"{local}: {qtd}", ln=True)

    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Detalhamento", ln=True)
    pdf.set_font("Arial", "", 10)

    for _, row in df.iterrows():
        pdf.cell(0, 8, f"Produto: {row['DESCRIÇÃO']}", ln=True)
        pdf.cell(0, 8, f"EAN: {row['EAN']} | Cód.Int: {row['COD.INT']}", ln=True)
        pdf.cell(0, 8, f"Local: {row['LOCAL INFORMADO']} | Validade: {row['VALIDADE']}", ln=True)
        pdf.ln(5)

    return pdf.output(dest='S').encode('latin-1')

with st.expander("📄 Exportar PDF"):
    if st.button("📤 Baixar PDF"):
        pdf_bytes = gerar_pdf(pd.DataFrame(respostas))
        st.download_button(
            label="📥 Clique aqui para baixar o PDF",
            data=pdf_bytes,
            file_name=f"relatorio_{nome_limpo}_{pesquisa_limpa}.pdf",
            mime="application/pdf"
        )

# Função para salvar no Google Sheets
def salvar_google_sheets(respostas):
    try:
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds_dict = dict(st.secrets["google_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)

        planilha = client.open("Respostas Pesquisa")
        abas_dict = {}
        for resposta in respostas:
            nome_aba = resposta.get("LOJA", "Sem Loja")
            if nome_aba not in abas_dict:
                abas_dict[nome_aba] = []
            abas_dict[nome_aba].append(resposta)

        for nome_aba, respostas_da_aba in abas_dict.items():
            try:
                aba = planilha.worksheet(nome_aba)
            except gspread.exceptions.WorksheetNotFound:
                aba = planilha.add_worksheet(title=nome_aba, rows="1000", cols="20")
                aba.append_row(list(respostas_da_aba[0].keys()))
            linhas = [list(resp.values()) for resp in respostas_da_aba]
            aba.append_rows(linhas)

        st.success("✅ Respostas enviadas para o Google Sheets com sucesso!")
    except Exception as e:
        st.error(f"Erro ao salvar no Google Sheets: {e}")

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

    salvar_google_sheets(respostas)
