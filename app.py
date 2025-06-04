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
mapa = {str(p): p for p in pesquisas}

st.subheader("🔍 Selecione a pesquisa")
opcoes_selectbox = [""] + list(mapa.keys())
selecionado = st.selectbox("Escolha a pesquisa:", opcoes_selectbox)
if not selecionado:
    st.warning("⚠️ Por favor, selecione uma pesquisa.")
    st.stop()

pesquisa_selecionada = mapa[selecionado]
nome_limpo = re.sub(r'\W+', '_', nome_usuario.strip())
pesquisa_limpa = re.sub(r'\W+', '_', pesquisa_selecionada.strip())
progresso_path = f"/tmp/progresso_{nome_limpo}_{pesquisa_limpa}.xlsx"

# Inicializa progresso em memória
if "respostas_salvas" not in st.session_state:
    st.session_state.respostas_salvas = {}

# Carrega progresso salvo do arquivo
if os.path.exists(progresso_path) and not st.session_state.respostas_salvas:
    try:
        df_antigo = pd.read_excel(progresso_path)
        for _, row in df_antigo.iterrows():
            chave = f"{row['COD.INT']}|{row['DESCRIÇÃO']}"
            st.session_state.respostas_salvas[chave] = {
                "LOCAL INFORMADO": row.get("LOCAL INFORMADO", ""),
                "VALIDADE": row.get("VALIDADE", "")
            }
        st.info("🔄 Progresso anterior carregado automaticamente.")
    except:
        st.warning("⚠️ Não foi possível carregar progresso anterior.")

# Filtro da pesquisa
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

for idx, row in df_pagina.iterrows():
    st.markdown("---")
    st.markdown(f"**🛍️ Produto:** {row['DESCRIÇÃO']}")
    st.markdown(f"**🏷️ EAN:** {row.get('EAN', '---')}")
    st.markdown(f"**🔢 Código Interno:** {row.get('COD.INT', '---')}")
    st.markdown(f"**📦 Estoque:** {row.get('ESTOQUE', '---')}")
    st.markdown(f"**🗖️ Dias sem movimentação:** {row.get('DIAS SEM MOVIMENTAÇÃO', '---')}")
    st.markdown(f"**📍 Seção:** {row.get('SEÇÃO', '---')}")

    chave = f"{row.get('COD.INT', idx)}|{row.get('DESCRIÇÃO', '')}"
    progresso = st.session_state.respostas_salvas.get(chave, {"LOCAL INFORMADO": "", "VALIDADE": ""})

    local = st.selectbox(
        f"📍 Onde está o produto ({row['DESCRIÇÃO']}):",
        ["", "SEÇÃO", "DEPÓSITO", "ERRO DE ESTOQUE"],
        index=["", "SEÇÃO", "DEPÓSITO", "ERRO DE ESTOQUE"].index(progresso["LOCAL INFORMADO"]) if progresso["LOCAL INFORMADO"] in ["SEÇÃO", "DEPÓSITO", "ERRO DE ESTOQUE"] else 0,
        key=f"local_{chave}_{pagina}"
    )

    validade = st.text_input(
        f"🗓️ Validade ({row['DESCRIÇÃO']}):",
        value=progresso["VALIDADE"],
        key=f"validade_{chave}_{pagina}"
    )

    st.session_state.respostas_salvas[chave] = {
        "LOCAL INFORMADO": local,
        "VALIDADE": validade
    }

# Constrói dataframe consolidado
respostas = []
for _, row in df_filtrado.iterrows():
    chave = f"{row.get('COD.INT', '')}|{row.get('DESCRIÇÃO', '')}"
    progresso = st.session_state.respostas_salvas.get(chave, {"LOCAL INFORMADO": "", "VALIDADE": ""})
    respostas.append({
        "USUÁRIO": nome_usuario,
        "DATA": data_preenchimento.strftime('%d/%m/%Y'),
        "PESQUISA": pesquisa_selecionada,
        "LOJA": row.get("LOJA", ""),
        "DESCRIÇÃO": row.get("DESCRIÇÃO", ""),
        "COD.INT": row.get("COD.INT", ""),
        "EAN": row.get("EAN", ""),
        "ESTOQUE": row.get("ESTOQUE", ""),
        "DIAS SEM MOVIMENTAÇÃO": row.get("DIAS SEM MOVIMENTAÇÃO", ""),
        "SEÇÃO": row.get("SEÇÃO", ""),
        "LOCAL INFORMADO": progresso["LOCAL INFORMADO"],
        "VALIDADE": progresso["VALIDADE"]
    })

# Salva localmente
pd.DataFrame(respostas).to_excel(progresso_path, index=False)
st.toast("📅 Progresso salvo localmente.", icon="📅")
