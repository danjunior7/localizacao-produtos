import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth

# Configurações da página
st.set_page_config(page_title="Painel Administrativo", layout="wide")

# Pega as credenciais do secrets.toml
credentials = {
    "usernames": {
        "admin": {
            "name": st.secrets["credentials"]["usernames"]["admin"]["name"],
            "password": st.secrets["credentials"]["usernames"]["admin"]["password"]
        }
    }
}

cookie_name = st.secrets["cookie"]["name"]
cookie_key = st.secrets["cookie"]["key"]
expiry_days = st.secrets["cookie"]["expiry_days"]

# Inicializa autenticação
authenticator = stauth.Authenticate(
    credentials,
    cookie_name,
    cookie_key,
    expiry_days
)

# Interface de login
name, authentication_status, username = authenticator.login("Login", location="main")

if authentication_status is False:
    st.error("Usuário ou senha incorretos.")

elif authentication_status is None:
    st.warning("Por favor, insira suas credenciais.")

elif authentication_status:
    authenticator.logout("Sair", "sidebar")
    st.sidebar.success(f"Bem-vindo, {name} 👋")

    st.title("📊 Painel de Administração")

    try:
        df = pd.read_excel("respostas.xlsx")
        st.dataframe(df)
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
