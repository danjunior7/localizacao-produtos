import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import gspread
from google.oauth2 import service_account

st.set_page_config(page_title="Painel Admin", layout="wide")

# 🔐 Credenciais
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

# 🔑 Autenticação
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

    # ✅ Conectar ao Google Sheets
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        credentials_google = service_account.Credentials.from_service_account_info(
            st.secrets["google_service_account"],
            scopes=scope
        )
        client = gspread.authorize(credentials_google)

        # Substitua abaixo pelo nome da sua planilha
        sheet = client.open("Respostas Pesquisa").sheet1
        data = sheet.get_all_records()
        df = pd.DataFrame(data)

        st.subheader("📄 Respostas coletadas")
        st.dataframe(df, use_container_width=True)

        st.download_button("📥 Baixar respostas", df.to_csv(index=False).encode('utf-8'), file_name="respostas.csv", mime="text/csv")

    except Exception as e:
        st.error(f"Erro ao carregar os dados do Google Sheets: {e}")
