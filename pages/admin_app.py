import streamlit as st
import pandas as pd
import copy
import streamlit_authenticator as stauth

# Página de autenticação
st.set_page_config(page_title="Painel Admin - Localização", layout="wide")

# ⚠️ Importa uma cópia dos dados de autenticação para evitar erro de somente leitura
credentials = copy.deepcopy(st.secrets["credentials"])
cookie = dict(st.secrets["cookie"])

# Autenticação
authenticator = stauth.Authenticate(
    credentials,
    cookie["name"],
    cookie["key"],
    cookie["expiry_days"]
)

name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status is False:
    st.error("Usuário ou senha incorretos.")
elif authentication_status is None:
    st.warning("Por favor, insira suas credenciais.")
elif authentication_status:
    authenticator.logout("Sair", "sidebar")
    st.sidebar.success(f"Bem-vindo, {name} 👋")

    st.title("📊 Painel de Administração")

    RESP_ARQ = "respostas.xlsx"

    if not st.secrets.get("google_service_account"):
        st.error("⚠️ Credenciais do Google Sheets não encontradas.")
        st.stop()

    # Exemplo de carregamento local (você pode trocar por conexão Google Sheets)
    try:
        df = pd.read_excel(RESP_ARQ)
        st.dataframe(df)
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
