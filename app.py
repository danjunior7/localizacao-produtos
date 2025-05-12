import streamlit as st
import pandas as pd
import datetime
import os
import gspread
from google.oauth2.service_account import Credentials

# Configuração da página
st.set_page_config(
    page_title="Localização de Produtos",
    layout="wide",
    initial_sidebar_state="auto"
)

# CSS para menu responsivo (oculto no celular, sempre visível no PC)
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
import re
nome_limpo = re.sub(r'\W+', '_', nome_usuario.strip())
pesquisa_limpa = re.sub(r'\W+', '_', pesquisa_selecionada.strip())
progresso_path = f"/tmp/progresso_{nome_limpo}_{pesquisa_limpa}.xlsx"


# Carrega progresso salvo se existir
progresso_antigo = {}
if os.path.exists(progresso_path):
    try:
        df_antigo = pd.read_excel(progresso_path)
        for _, row in df_antigo.iterrows():
            progresso_antigo[row["COD.INT"]] = row["LOCAL INFORMADO"]
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
    st.markdown(f"**🔢 Código Interno:** {row.get('COD.INT', '---')}")
    st.markdown(f"**📦 Estoque:** {row.get('ESTOQUE', '---')}")
    st.markdown(f"**📆 Dias sem movimentação:** {row.get('DIAS SEM MOVIMENTAÇÃO', '---')}")
    st.markdown(f"**🏷️ EAN:** {row.get('EAN', '---')}")
    st.markdown(f"**📍 Seção:** {row.get('SEÇÃO', '---')}")

    local_key = f"local_{idx}"
    valor_inicial = progresso_antigo.get(row.get("COD.INT", ""), "")

    local = st.selectbox(
        f"📍 Onde está o produto ({row['DESCRIÇÃO']}):",
        ["", "SEÇÃO", "DEPÓSITO", "ERRO DE ESTOQUE"],
        key=local_key,
        index=["", "SEÇÃO", "DEPÓSITO", "ERRO DE ESTOQUE"].index(valor_inicial) if valor_inicial in ["SEÇÃO", "DEPÓSITO", "ERRO DE ESTOQUE"] else 0
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

# Salva o progresso automaticamente localmente
df_temp = pd.DataFrame(respostas)
df_temp.to_excel(progresso_path, index=False)
st.toast("💾 Progresso salvo localmente (automático).", icon="💾")

# Função para salvar no Google Sheets
def salvar_google_sheets(respostas):
    try:
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds_dict = dict(st.secrets["google_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)

        planilha = client.open("Respostas Pesquisa")

        for resposta in respostas:
            nome_aba = resposta.get("LOJA", "Sem Loja")
            try:
                aba = planilha.worksheet(nome_aba)
            except gspread.exceptions.WorksheetNotFound:
                aba = planilha.add_worksheet(title=nome_aba, rows="1000", cols="20")
                aba.append_row(list(resposta.keys()))

            aba.append_row(list(resposta.values()))

        st.success("✅ Respostas enviadas para o Google Sheets com sucesso!")

    except Exception as e:
        st.error(f"Erro ao salvar no Google Sheets: {e}")

# Botão de envio final
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
