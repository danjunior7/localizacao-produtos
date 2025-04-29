import streamlit as st
import pandas as pd
from io import BytesIO
import os

st.set_page_config(page_title="Painel Administrativo", layout="wide")
st.title("📊 Painel Administrativo de Respostas")

ARQUIVO_XLSX = "respostas.xlsx"
ABA_STATUS = "Status_Pesquisas"

if not os.path.exists(ARQUIVO_XLSX):
    st.warning("⚠️ Nenhuma resposta registrada ainda.")
    st.stop()

try:
    excel_file = pd.ExcelFile(ARQUIVO_XLSX)
    abas = [a for a in excel_file.sheet_names if a != ABA_STATUS]
except Exception as e:
    st.error(f"⚠️ Erro ao ler o arquivo Excel: {e}")
    st.stop()

# Seleciona aba
aba_escolhida = st.selectbox("🗂️ Selecione a pesquisa para visualizar:", abas)
df_respostas = pd.read_excel(ARQUIVO_XLSX, sheet_name=aba_escolhida)

# Filtros
with st.expander("🔍 Filtros"):
    col1, col2, col3 = st.columns(3)

    if 'USUÁRIO' in df_respostas.columns:
        usuarios = df_respostas['USUÁRIO'].dropna().unique()
        usuario_filtrado = col1.selectbox("Usuário", options=['Todos'] + list(usuarios))
        if usuario_filtrado != 'Todos':
            df_respostas = df_respostas[df_respostas['USUÁRIO'] == usuario_filtrado]

    if 'DATA' in df_respostas.columns:
        datas = pd.to_datetime(df_respostas['DATA'], errors='coerce')
        data_min = datas.min()
        data_max = datas.max()
        data_inicial, data_final = col2.date_input("Intervalo de datas", value=[data_min, data_max])
        df_respostas['DATA'] = pd.to_datetime(df_respostas['DATA'], errors='coerce')
        df_respostas = df_respostas[(df_respostas['DATA'] >= pd.to_datetime(data_inicial)) & (df_respostas['DATA'] <= pd.to_datetime(data_final))]

    if 'DESCRIÇÃO' in df_respostas.columns:
        texto_busca = col3.text_input("Pesquisar por descrição")
        if texto_busca:
            df_respostas = df_respostas[df_respostas['DESCRIÇÃO'].str.contains(texto_busca, case=False, na=False)]

st.subheader("📋 Respostas Registradas")
st.dataframe(df_respostas, use_container_width=True)

# Download da aba filtrada
buffer = BytesIO()
with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
    df_respostas.to_excel(writer, index=False, sheet_name=aba_escolhida)
buffer.seek(0)
st.download_button(
    label="📥 Baixar esta aba em Excel (com filtro aplicado)",
    data=buffer,
    file_name=f"{aba_escolhida.replace(' ', '_')}_respostas_filtradas.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.markdown("---")
st.subheader("📈 Status Geral das Pesquisas")

# Mostra aba de status
try:
    df_status = pd.read_excel(ARQUIVO_XLSX, sheet_name=ABA_STATUS)
    df_status = df_status.dropna(subset=["PESQUISA"])
    
    def cor_status(val):
        if val == "CONCLUÍDO":
            return "background-color: lightgreen"
        elif val == "PARCIAL":
            return "background-color: orange"
        return ""

    st.dataframe(
        df_status.style.applymap(cor_status, subset=["STATUS"]),
        use_container_width=True
    )

    # Download do resumo
    buf_resumo = BytesIO()
    with pd.ExcelWriter(buf_resumo, engine="openpyxl") as writer:
        df_status.to_excel(writer, index=False, sheet_name=ABA_STATUS)
    buf_resumo.seek(0)
    st.download_button(
        label="📥 Baixar resumo geral em Excel",
        data=buf_resumo,
        file_name="resumo_status_pesquisas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

except Exception as e:
    st.error(f"Erro ao carregar status geral: {e}")
