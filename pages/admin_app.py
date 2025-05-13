import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import os
import io
import streamlit_authenticator as stauth
from google.oauth2.service_account import Credentials
import gspread

# ----------- CONFIGURAÇÃO INICIAL ----------
st.set_page_config(page_title="Painel Administrativo", layout="wide")

# CSS menu responsivo
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

    # ----------- LEITURA DAS ABAS DO GOOGLE SHEETS -----------
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

    # ----------- DASHBOARD -----------
    elif opcao == "📊 Dashboard":
        st.title("📊 Dashboard de Localização de Produtos")

        # ----------- FILTROS -----------
        st.sidebar.subheader("🔎 Filtros")

        lojas = st.sidebar.multiselect("Filtrar por loja", df['LOJA'].dropna().unique(), default=df['LOJA'].dropna().unique())
        df = df[df['LOJA'].isin(lojas)]

        periodo = st.sidebar.selectbox("Filtrar por período", ["Últimos 7 dias", "Últimos 15 dias", "Últimos 30 dias", "Intervalo personalizado"])
        hoje = datetime.date.today()

        if periodo == "Últimos 7 dias":
            df = df[df['DATA'].dt.date >= hoje - datetime.timedelta(days=7)]
        elif periodo == "Últimos 15 dias":
            df = df[df['DATA'].dt.date >= hoje - datetime.timedelta(days=15)]
        elif periodo == "Últimos 30 dias":
            df = df[df['DATA'].dt.date >= hoje - datetime.timedelta(days=30)]
        elif periodo == "Intervalo personalizado":
            inicio = st.sidebar.date_input("Início", hoje - datetime.timedelta(days=7))
            fim = st.sidebar.date_input("Fim", hoje)
            df = df[(df['DATA'].dt.date >= inicio) & (df['DATA'].dt.date <= fim)]

        # ----------- INDICADORES -----------
        total_registros = len(df)
        loja_destaque = df['LOJA'].value_counts().idxmax() if not df.empty else "N/A"

        col1, col2 = st.columns(2)
        col1.metric("📦 Total de Registros", total_registros)
        col2.metric("🏪 Loja com Mais Registros", loja_destaque)

        # ----------- GRÁFICO 1 – Produtos mais buscados -----------
        top_produtos = df['DESCRIÇÃO'].value_counts().head(10).reset_index()
        top_produtos.columns = ['DESCRIÇÃO', 'TOTAL']
        fig1 = px.bar(top_produtos, x='TOTAL', y='DESCRIÇÃO', orientation='h', title='🔝 Produtos mais Buscados')
        st.plotly_chart(fig1, use_container_width=True)

        # ----------- GRÁFICO 2 – Lojas com mais registros -----------
        top_lojas = df['LOJA'].value_counts().reset_index()
        top_lojas.columns = ['LOJA', 'TOTAL']
        fig2 = px.pie(top_lojas, names='LOJA', values='TOTAL', title='🏪 Lojas com Mais Registros')
        st.plotly_chart(fig2, use_container_width=True)

        # ----------- GRÁFICO 3 – Tendência por Data -----------
        tendencia = df.groupby(df['DATA'].dt.date).size().reset_index(name='TOTAL')
        fig3 = px.line(tendencia, x='DATA', y='TOTAL', title='📅 Tendência de Registros por Data')
        st.plotly_chart(fig3, use_container_width=True)

        # ----------- TABELA DE REGISTROS -----------
        st.subheader("📋 Registros Consolidados")
        st.dataframe(df[['DESCRIÇÃO', 'LOJA', 'USUÁRIO', 'DATA', 'LOCAL INFORMADO']])

        # ----------- EXPORTAÇÃO -----------
        st.subheader("📤 Exportar Dados")

        exportar = df.copy()
        exportar['DATA'] = exportar['DATA'].dt.strftime("%d/%m/%Y")

        col1, col2 = st.columns(2)
        with col1:
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                exportar.to_excel(writer, index=False, sheet_name='Exportação')
            st.download_button("⬇️ Baixar Excel", data=excel_buffer.getvalue(), file_name="dashboard_exportado.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        with col2:
            csv_buffer = exportar.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ Baixar CSV", data=csv_buffer, file_name="dashboard_exportado.csv", mime="text/csv")

else:
    st.warning("Por favor, faça login para acessar o painel.")
