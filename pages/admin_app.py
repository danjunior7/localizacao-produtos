import streamlit as st
import pandas as pd
import os
import copy
import streamlit_authenticator as stauth

# Carregar secrets com autenticação
credentials = copy.deepcopy(st.secrets["credentials"])
cookie = dict(st.secrets["cookie"])

# Setup do autenticador
authenticator = stauth.Authenticate(
    credentials,
    cookie["name"],
    cookie["key"],
    cookie["expiry_days"]
)

# Login
name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status is False:
    st.error("Usuário ou senha incorretos.")
elif authentication_status is None:
    st.warning("Por favor, preencha as credenciais.")
elif authentication_status:
    st.sidebar.success(f"Bem-vindo, {name}! ")
    authenticator.logout("Sair", "sidebar")

    st.set_page_config(page_title="Painel Admin - Localização", layout="wide")
    st.title("🛠  Painel de Administração")

    RESP_ARQ = "respostas.xlsx"

    # Carregar respostas
    if not os.path.exists(RESP_ARQ):
        st.warning("⚠️ Nenhum dado encontrado ainda.")
        st.stop()

    df = pd.read_excel(RESP_ARQ)

    # Filtros
    st.sidebar.header("🔍 Filtros")
    lojas = sorted(df["LOJA"].dropna().unique())
    loja_sel = st.sidebar.selectbox("Loja:", options=["Todas"] + lojas)

    pesquisa_sel = st.sidebar.selectbox("Pesquisa:", options=["Todas"] + sorted(df["PESQUISA"].dropna().unique()))

    if loja_sel != "Todas":
        df = df[df["LOJA"] == loja_sel]
    if pesquisa_sel != "Todas":
        df = df[df["PESQUISA"] == pesquisa_sel]

    st.subheader("📊 Respostas Registradas")
    st.dataframe(df, use_container_width=True)

    st.download_button(
        label="⬇️ Baixar como Excel",
        data=df.to_excel(index=False, engine="openpyxl"),
        file_name="respostas_filtradas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
