import streamlit as st
import streamlit_authenticator as stauth

# Cria o objeto de autenticação utilizando as credenciais do secrets.toml
authenticator = stauth.Authenticate(
    dict(st.secrets["credentials"]),
    st.secrets["cookie"]["name"],
    st.secrets["cookie"]["key"],
    st.secrets["cookie"]["expiry_days"],
    st.secrets["preauthorized"]
)

# Renderiza o formulário de login no corpo principal da página
nome, autenticado, usuario = authenticator.login("Login", "main")

if autenticado:
    st.success(f"Bem-vindo, *{nome}*!")
    # (Coloque aqui o conteúdo da aplicação que deve ser exibido após login bem-sucedido)
elif autenticado is False:
    st.error("Usuário ou senha incorretos.")
elif autenticado is None:
    st.warning("Por favor, insira seu usuário e senha para continuar.")
