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
respostas = []
df_filtrado = df[df["PESQUISA"] == pesquisa_selecionada].reset_index(drop=True)
if df_filtrado.empty:
    st.warning("⚠️ Nenhum produto encontrado nesta pesquisa.")
    st.stop()

st.subheader(f"📝 Pesquisa: {pesquisa_selecionada}")

# Paginação
itens_por_pagina = 20
total_paginas = (len(df_filtrado) - 1) // itens_por_pagina + 1
pagina_atual = st.number_input("Página:", min_value=1, max_value=total_paginas, value=1, step=1)

inicio = (pagina_atual - 1) * itens_por_pagina
fim = inicio + itens_por_pagina
df_pagina = df_filtrado.iloc[inicio:fim]

for idx, row in df_pagina.iterrows():
    st.markdown("---")
    st.markdown(f"**🛍️ Produto:** {row['DESCRIÇÃO']}")
    st.markdown(f"**🏷️ EAN:** {row.get('EAN', '---')}")
    st.markdown(f"**🔢 Código Interno:** {row.get('COD.INT', '---')}")
    st.markdown(f"**📦 Estoque:** {row.get('ESTOQUE', '---')}")
    st.markdown(f"**📆 Dias sem movimentação:** {row.get('DIAS SEM MOVIMENTAÇÃO', '---')}")
    st.markdown(f"**📍 Seção:** {row.get('SEÇÃO', '---')}")

    cod_int = row.get("COD.INT", "")
    valor_inicial = progresso_antigo.get(cod_int, {}).get("LOCAL INFORMADO", "")
    validade_raw = progresso_antigo.get(cod_int, {}).get("VALIDADE", "")
    validade_inicial = "" if pd.isna(validade_raw) else str(validade_raw)

    local = st.selectbox(
        f"📍 Onde está o produto ({row['DESCRIÇÃO']}):",
        ["", "SEÇÃO", "DEPÓSITO", "ERRO DE ESTOQUE"],
        key=f"local_{idx}",
        index=["", "SEÇÃO", "DEPÓSITO", "ERRO DE ESTOQUE"].index(valor_inicial) if valor_inicial in ["SEÇÃO", "DEPÓSITO", "ERRO DE ESTOQUE"] else 0
    )

    validade = st.text_input(
        f"📅 Validade ({row['DESCRIÇÃO']}):",
        value=validade_inicial,
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

# Salvar localmente
df_temp = pd.DataFrame(respostas)
df_temp.to_excel(progresso_path, index=False)
st.toast("💾 Progresso salvo localmente.", icon="💾")
