import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth

# Configuração da página
st.set_page_config(page_title="Painel Admin", layout="wide")

# Autenticação: usa diretamente o secrets
credentials = st.secrets["credentials"]
cookie = st.secrets["cookie"]

# Inicialização da autenticação
authenticator = stauth.Authenticate(
    credentials,
    cookie.name,
    cookie.key,
    cookie.expiry_days
)

# Login
name, authentication_status, username = authenticator.login("Login", location="main")

if authentication_status is False:
    st.error("Usuário ou senha incorretos.")
elif authentication_status is None:
    st.warning("Por favor, insira suas credenciais.")
elif authentication_status:
    authenticator.logout("Sair", location="sidebar")
    st.sidebar.success(f"Bem-vindo, {name} 👋")

    st.title("📊 Painel de Administração")

    RESP_ARQ = "respostas.xlsx"

    if not st.secrets.get("google_service_account"):
        st.error("⚠️ Credenciais do Google Sheets não encontradas.")
        st.stop()

    try:
        df = pd.read_excel(RESP_ARQ)
        st.dataframe(df)
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
