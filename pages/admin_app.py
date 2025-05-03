import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth

st.set_page_config(page_title="Painel Admin", layout="wide")

# Carrega credenciais direto do secrets (sem usar deepcopy)
credentials = {
    "usernames": {
        "admin": {
            "name": st.secrets["credentials"]["usernames"]["admin"]["name"],
            "password": st.secrets["credentials"]["usernames"]["admin"]["password"]
        }
    }
}

cookie = {
    "name": st.secrets["cookie"]["name"],
    "key": st.secrets["cookie"]["key"],
    "expiry_days": st.secrets["cookie"]["expiry_days"]
}

# Autenticação
authenticator = stauth.Authenticate(
    credentials,
    cookie["name"],
    cookie["key"],
    cookie["expiry_days"]
)

name, authentication_status, username = authenticator.login("Login", location="main")

if authentication_status is False:
    st.error("Usuário ou senha incorretos.")
elif authentication_status is None:
    st.warning("Por favor, insira suas credenciais.")
elif authentication_status:
    authenticator.logout("Sair", "sidebar")
    st.sidebar.success(f"Bem-vindo, {name} 👋")

    st.title("📊 Painel de Administração")

    # Exemplo: carregamento de dados
    try:
        df = pd.read_excel("respostas.xlsx")
        st.dataframe(df)
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
