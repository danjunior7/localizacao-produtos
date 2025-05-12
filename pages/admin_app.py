import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import gspread
from google.oauth2 import service_account
import os
import glob

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

    # 🗂️ Seleção de Loja (aba da planilha)
    abas_lojas = ["LISBOA", "JOQUEI", "MPE 1", "MPE 2", "PAN", "MARACANAU"]
    loja = st.selectbox("Selecione a loja", abas_lojas)

    try:
        # 📎 Conectar ao Google Sheets
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        credentials_google = service_account.Credentials.from_service_account_info(
            st.secrets["google_service_account"],
            scopes=scope
        )
        client = gspread.authorize(credentials_google)

        # 📄 Abrir planilha e aba correspondente
        sheet = client.open("Respostas Pesquisa").worksheet(loja)
        data = sheet.get_all_records()
        df = pd.DataFrame(data)

        st.subheader(f"📄 Respostas da loja: {loja}")
        st.dataframe(df, use_container_width=True)

        # ⬇️ Download dos dados
        st.download_button(
            label="📥 Baixar respostas",
            data=df.to_csv(index=False).encode('utf-8'),
            file_name=f"respostas_{loja.lower()}.csv",
            mime="text/csv"
        )

    except Exception as e:
        st.error(f"Erro ao carregar os dados da aba '{loja}': {e}")

    # ✅ GERENCIAR PROGRESSO LOCAL SALVO
    st.markdown("---")
    st.subheader("🧹 Gerenciar Progresso")

    if st.button("🧼 Limpar todos os arquivos de progresso salvos (localmente)"):
        try:
            arquivos = glob.glob("/tmp/progresso_*.xlsx")
            for arq in arquivos:
                os.remove(arq)
            st.success(f"✅ {len(arquivos)} arquivos de progresso removidos.")
        except Exception as e:
            st.error(f"Erro ao remover arquivos: {e}")
