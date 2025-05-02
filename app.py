import streamlit as st
import pandas as pd

st.set_page_config(page_title="DEBUG - Planilha Local", layout="wide")
st.title("🧪 Modo DEBUG: Visualização da Planilha Feedback_Localizacao.xlsx")

# Tenta carregar a planilha
try:
    df = pd.read_excel("Feedback_Localizacao.xlsx")
    st.success(f"✅ Planilha carregada com sucesso! Total de linhas: {len(df)}")
    st.dataframe(df, use_container_width=True)
except FileNotFoundError:
    st.error("❌ Arquivo 'Feedback_Localizacao.xlsx' não foi encontrado no diretório do app.")
except Exception as e:
    st.error(f"❌ Erro ao carregar a planilha: {e}")
