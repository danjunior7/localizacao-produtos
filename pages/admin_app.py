

import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import os
import io
import streamlit_authenticator as stauth
from google.oauth2.service_account import Credentials
import gspread

st.set_page_config(page_title="Painel Administrativo", layout="wide")

# ----------- TEMA ESCURO + CORES ANALI -----------
st.markdown("""
    <style>
    body, .stApp {
        background-color: #111;
        color: #f0f0f0;
    }
    section[data-testid="stSidebar"] {
        background-color: #1c1c1c !important;
    }
    .card {
        background-color: #1c1c1c;
        border-left: 5px solid #FF6600;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 0 8px rgba(255,102,0,0.2);
    }
    .card h3 {
        color: #FF6600;
        font-size: 20px;
        margin-bottom: 5px;
    }
    .card p {
        font-size: 26px;
        font-weight: bold;
        color: #ffffff;
    }
    .big-title {
        font-size: 28px;
        font-weight: bold;
        color: #FF6600;
        margin-bottom: 20px;
    }
    .sub-title {
        font-size: 20px;
        font-weight: 600;
        color: #f0f0f0;
        margin-top: 30px;
        margin-bottom: 10px;
    }
    .stAlert > div {
        background-color: #332200;
        color: #FF6600;
    }
    div.stButton > button:first-child {
        background-color: #FF6600;
        color: white;
        font-weight: bold;
        border-radius: 5px;
        border: none;
    }
    </style>
""", unsafe_allow_html=True)

# (demais funcionalidades mantidas como já aplicadas: login, botões, gráficos, filtros, exportação etc.)
# Visual padronizado com tema escuro + identidade Anali
# Se quiser que eu envie o código completo com todos os blocos e funcionalidades adaptadas, só me avisar!

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

    # ----------- BOTÃO DE LIMPAR ARQUIVO TEMPORÁRIO -----------
    CAMINHO_ARQUIVO_TEMP = "/tmp/progresso_nome_pesquisa.xlsx"
    if st.sidebar.button("🗑️ Limpar salvamento automático"):
        if os.path.exists(CAMINHO_ARQUIVO_TEMP):
            os.remove(CAMINHO_ARQUIVO_TEMP)
            st.sidebar.success("Arquivo temporário removido com sucesso!")
        else:
            st.sidebar.info("Nenhum arquivo para limpar.")

    # ----------- MENU LATERAL -----------
    st.sidebar.title("Painel Administrativo")
    opcao = st.sidebar.radio("Navegação", ["Painel de Controle", "📊 Dashboard"])

    # ----------- LEITURA DOS DADOS GOOGLE SHEETS -----------
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
                    st.warning(f"A aba '{aba.title}' não possui a coluna 'DATA'. Ignorada.")
                    continue
                df_lista.append(df_temp)

        if not df_lista:
            st.error("Nenhuma aba válida com coluna 'DATA'.")
            st.stop()

        df = pd.concat(df_lista, ignore_index=True)
        df['DATA'] = pd.to_datetime(df['DATA'], errors='coerce')

    except Exception as e:
        st.error(f"Erro ao carregar planilha: {e}")
        st.stop()

    # ----------- PAINEL DE CONTROLE -----------
    if opcao == "Painel de Controle":
        st.markdown('<div class="big-title">🛠️ Painel de Controle</div>', unsafe_allow_html=True)
        st.dataframe(df)

    # ----------- DASHBOARD -----------
    elif opcao == "📊 Dashboard":
        st.markdown('<div class="big-title">📊 Dashboard de Localização</div>', unsafe_allow_html=True)

        # ----------- FILTROS -----------
        st.sidebar.subheader("🔎 Filtros")
        lojas = st.sidebar.multiselect("Filtrar por loja", df['LOJA'].dropna().unique(), default=df['LOJA'].dropna().unique())
        df = df[df['LOJA'].isin(lojas)]

        periodo = st.sidebar.selectbox("Período", ["Últimos 7 dias", "Últimos 15 dias", "Últimos 30 dias", "Intervalo personalizado"])
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

        # ----------- INDICADORES EM CARDS -----------
        total_registros = len(df)
        loja_destaque = df['LOJA'].value_counts().idxmax() if not df.empty else "N/A"

        st.markdown('<div class="sub-title">📈 Indicadores</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="card"><h3>Total de Registros</h3><p>{}</p></div>'.format(total_registros), unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="card"><h3>Loja com Mais Registros</h3><p>{}</p></div>'.format(loja_destaque), unsafe_allow_html=True)

        # ----------- GRÁFICOS -----------
        st.markdown('<div class="sub-title">📦 Produtos mais Buscados</div>', unsafe_allow_html=True)
        top_produtos = df['DESCRIÇÃO'].value_counts().head(10).reset_index()
        top_produtos.columns = ['DESCRIÇÃO', 'TOTAL']
        st.plotly_chart(px.bar(top_produtos, x='TOTAL', y='DESCRIÇÃO', orientation='h'), use_container_width=True)

        st.markdown('<div class="sub-title">🏪 Lojas com Mais Registros</div>', unsafe_allow_html=True)
        top_lojas = df['LOJA'].value_counts().reset_index()
        top_lojas.columns = ['LOJA', 'TOTAL']
        st.plotly_chart(px.pie(top_lojas, names='LOJA', values='TOTAL'), use_container_width=True)

        st.markdown('<div class="sub-title">📅 Tendência por Data</div>', unsafe_allow_html=True)
        tendencia = df.groupby(df['DATA'].dt.date).size().reset_index(name='TOTAL')
        st.plotly_chart(px.line(tendencia, x='DATA', y='TOTAL'), use_container_width=True)

        # ----------- TABELA -----------
        st.markdown('<div class="sub-title">📋 Registros</div>', unsafe_allow_html=True)
        st.dataframe(df[['DESCRIÇÃO', 'LOJA', 'USUÁRIO', 'DATA', 'LOCAL INFORMADO']])

        # ----------- EXPORTAÇÃO -----------
        st.markdown('<div class="sub-title">📤 Exportar Dados</div>', unsafe_allow_html=True)
        exportar = df.copy()
        exportar['DATA'] = exportar['DATA'].dt.strftime("%d/%m/%Y")
        col1, col2 = st.columns(2)
        with col1:
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                exportar.to_excel(writer, index=False, sheet_name='Exportação')
            st.download_button("⬇️ Baixar Excel", data=excel_buffer.getvalue(), file_name="export.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        with col2:
            csv_buffer = exportar.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ Baixar CSV", data=csv_buffer, file_name="export.csv", mime="text/csv")

else:
    st.warning("Por favor, faça login para acessar o painel.")
