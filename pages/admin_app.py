import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth

# Configuração da página
st.set_page_config(page_title="Painel Admin", layout="wide")

# Autenticação
authenticator = stauth.Authenticate(
    dict(st.secrets["credentials"]),
    st.secrets["cookie"]["name"],
    st.secrets["cookie"]["key"],
    st.secrets["cookie"]["expiry_days"],
    st.secrets["preauthorized"]
)

nome, autenticado, usuario = authenticator.login("Login", "main")

if autenticado:
    authenticator.logout("Sair", "sidebar")
    st.sidebar.success(f"Bem-vindo, {nome} 👋")

    st.title("📊 Painel de Administração")

    # Carregar e exibir arquivo Excel
    try:
        df = pd.read_excel("respostas.xlsx")
        st.subheader("📄 Respostas coletadas")
        st.dataframe(df, use_container_width=True)
    except FileNotFoundError:
        st.warning("Arquivo 'respostas.xlsx' não encontrado.")
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")

elif autenticado is False:
    st.error("Usuário ou senha incorretos.")
elif autenticado is None:
    st.warning("Por favor, insira seu usuário e senha para continuar.")
