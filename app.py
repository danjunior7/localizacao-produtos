# ... (importações continuam iguais)
import streamlit as st
import pandas as pd
import datetime
import os
from openpyxl import load_workbook

import gspread
from google.oauth2.service_account import Credentials

# Configuração da página
st.set_page_config(page_title="Localização de Produtos", layout="centered")
st.title("📦 Localização de Produtos nas Lojas")

# 🔍 TESTE: Confirma se os secrets estão acessíveis
st.subheader("🔍 Teste de leitura de secrets")
try:
    email_bot = st.secrets["google_service_account"]["client_email"]
    st.success(f"✅ Secrets carregados com sucesso!\nBot: {email_bot}")
except Exception as e:
    st.error(f"❌ Erro ao acessar secrets: {e}")

# Continuação normal do app
st.subheader("👤 Identificação")
nome_usuario = st.text_input("Digite seu nome:")
data_preenchimento = st.date_input("Data de preenchimento:", value=datetime.date.today())

st.markdown("---")
