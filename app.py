# Botões de envio e exportação no final
import pandas as pd
import base64
from fpdf import FPDF

# Botões de envio e exportação no final
def exportar_pdf(respostas):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"Relatório de Pesquisa - {pesquisa_selecionada}", ln=True, align="C")

    df_respostas = pd.DataFrame(respostas)
    total = len(df_respostas)
    respondidos = df_respostas[df_respostas["LOCAL INFORMADO"] != ""].shape[0]
    nao_respondidos = total - respondidos
    por_local = df_respostas["LOCAL INFORMADO"].value_counts()

    pdf.ln(5)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, f"Total de itens: {total}", ln=True)
    pdf.cell(0, 8, f"Respondidos: {respondidos}", ln=True)
    pdf.cell(0, 8, f"Não respondidos: {nao_respondidos}", ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Resumo por Local Informado:", ln=True)
    pdf.set_font("Arial", "", 11)
    for local, qtd in por_local.items():
        nome = local if local else "Não informado"
        pdf.cell(0, 8, f"{nome}: {qtd}", ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Detalhamento por Produto", ln=True)
    pdf.set_font("Arial", "", 10)

    for r in respostas:
        pdf.ln(3)
        pdf.set_font("Arial", "B", 10)
        pdf.multi_cell(0, 6, f"{r['DESCRIÇÃO']} ({r['COD.INT']})")
        pdf.set_font("Arial", "", 9)
        pdf.multi_cell(0, 5,
            f"EAN: {r['EAN']} | Estoque: {r['ESTOQUE']} | Dias s/ mov: {r['DIAS SEM MOVIMENTAÇÃO']}"
            f"\nSeção: {r['SEÇÃO']} | Local: {r['LOCAL INFORMADO']} | Validade: {r['VALIDADE']}"
        )

    caminho_pdf = f"/tmp/relatorio_{nome_limpo}_{pesquisa_limpa}.pdf"
    pdf.output(caminho_pdf)
    with open(caminho_pdf, "rb") as f:
        pdf_data = f.read()

    b64 = base64.b64encode(pdf_data).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="relatorio_{pesquisa_limpa}.pdf">📄 Baixar Relatório em PDF</a>'
    st.markdown(href, unsafe_allow_html=True)

st.markdown("---", unsafe_allow_html=False)
if st.button("📤 Enviar respostas para planilha e baixar PDF"):
    df_final = pd.DataFrame(respostas)
    df_final.to_excel(f"respostas_{pesquisa_limpa}.xlsx", index=False)
    exportar_pdf(respostas)
    st.success("✅ Respostas salvas e PDF gerado com sucesso!")
