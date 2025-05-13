import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import os
import streamlit_authenticator as stauth
from google.oauth2.service_account import Credentials
import gspread

# ----------- CONFIGURAÇÃO INICIAL ----------
st.set_page_config(page_title="Painel Administrativo", layout="wide")

# CSS para manter o menu visível no PC e esconder no celular
st.markdown("""
    <style>
    @media (max-width: 768px) {
        section[data-testid="stSidebar"] {
            transform: translateX(-100%);
            transition: all 0.3s ease-in-out;
            position: fixed;
            z-index: 1000;
            height: 100%;
        }
        section[data-testid="stSidebar"][aria-expanded="true"] {
            transform: translateX(0%);
        }
    }
    </style>
""", unsafe_allow_html=True)

# ----------- AUTENTICAÇÃO ----------
hashed_passwords = stauth.Hasher(['123', '321']).generate()

credentials = {
    "usernames": {
        "robson": {
            "name": "Robson",
            "password": hashed_passwords[0]
        },
        "erica": {
            "name": "Erica",
            "password": hashed_passwords[1]
        }
    }
}

authenticator = stauth.Authenticate(
    credentials,
    "painel_admin", "abcdef", cookie_expiry_days=30
)

nome, autenticado, nome_usuario = authenticator.login('Login', 'main')

if autenticado:
    authenticator.logout("Logout", "sidebar")
    st.sidebar.write(f"Bem-vindo, {nome} 👋")

    # ----------- MENU LATERAL -----------
    st.sidebar.title("Painel Administrativo")
    opcao = st.sidebar.radio("Navegação", ["Painel de Controle", "📊 Dashboard"])

    # ----------- LEITURA DE TODAS AS ABAS DO GOOGLE SHEETS -----------
    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    credentials = Credentials.from_service_account_info(
        st.secrets["google_service_account"],
        scopes=scopes
    )

    gc = gspread.authorize(credentials)
    SHEET_ID = "1Zl6JTKgfjwLI0JNyz5CFIhgx8nbshTk8TicFcv8h7mU"

    try:
        planilha = gc.open_by_key(SHEET_ID)
        abas = planilha.worksheets()

        df_lista = []
        for aba in abas:
            dados = aba.get_all_records()
            if dados:
                df_temp = pd.DataFrame(dados)
                df_temp['LOJA'] = aba.title

                if 'DATA' not in df_temp.columns:
                    st.warning(f"A aba '{aba.title}' não possui a coluna 'DATA'. Ela foi ignorada.")
                    continue

                df_lista.append(df_temp)

        if not df_lista:
            st.error("Nenhuma aba válida com a coluna 'DATA' foi encontrada.")
            st.stop()

        df = pd.concat(df_lista, ignore_index=True)
        df['DATA'] = pd.to_datetime(df['DATA'], errors='coerce')
    except Exception as e:
        st.error(f"Erro ao carregar os dados do Google Sheets: {e}")
        st.stop()

    # ----------- PAINEL DE CONTROLE -----------
    if opcao == "Painel de Controle":
        st.title("🛠️ Painel de Controle")
        st.dataframe(df)

    # ----------- DASHBOARD DE GRÁFICOS -----------
    elif opcao == "📊 Dashboard":
        st.title("📊 Dashboard de Localização de Produtos")

        # Filtros
        st.sidebar.subheader("🔎 Filtros do Dashboard")
        lojas = st.sidebar.multiselect("Filtrar por loja", df['LOJA'].dropna().unique(), default=df['LOJA'].dropna().unique())
        df = df[df['LOJA'].isin(lojas)]

        # Gráfico 1 – Itens mais buscados (DESCRIÇÃO)
        top_produtos = df['DESCRIÇÃO'].value_counts().head(10).reset_index()
        top_produtos.columns = ['DESCRIÇÃO', 'TOTAL']
        fig1 = px.bar(top_produtos, x='TOTAL', y='DESCRIÇÃO', orientation='h', title='🔝 Produtos mais Buscados')
        st.plotly_chart(fig1, use_container_width=True)

        # Gráfico 2 – Lojas com mais registros
        top_lojas = df['LOJA'].value_counts().reset_index()
        top_lojas.columns = ['LOJA', 'TOTAL']
        fig2 = px.pie(top_lojas, names='LOJA', values='TOTAL', title='🏪 Lojas com Mais Registros')
        st.plotly_chart(fig2, use_container_width=True)

        # Gráfico 3 – Tendência de registros por data
        tendencia = df.groupby(df['DATA'].dt.date).size().reset_index(name='TOTAL')
        fig3 = px.line(tendencia, x='DATA', y='TOTAL', title='📅 Tendência de Registros por Data')
        st.plotly_chart(fig3, use_container_width=True)

        # Alerta de produtos sem localização
        sem_localizacao = df[df['LOCAL INFORMADO'].isna()]
        st.warning(f"⚠️ {len(sem_localizacao)} produtos sem localização preenchida.")
        if not sem_localizacao.empty:
            st.dataframe(sem_localizacao[['DESCRIÇÃO', 'LOJA', 'USUÁRIO', 'DATA']])

else:
    st.warning("Por favor, faça login para acessar o painel.")
