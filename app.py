# CÓDIGO CORRIGIDO ABAIXO (sem emojis inválidos no Python)

# Para evitar o erro StreamlitDuplicateElementKey, usamos cod_int + idx como chave única

local = st.selectbox(
    f"Onde está o produto ({row['DESCRIÇÃO']}):",
    ["", "SEÇÃO", "DEPÓSITO", "ERRO DE ESTOQUE"],
    key=f"local_{cod_int}_{idx}",
    index=["", "SEÇÃO", "DEPÓSITO", "ERRO DE ESTOQUE"].index(valor_inicial)
    if valor_inicial in ["SEÇÃO", "DEPÓSITO", "ERRO DE ESTOQUE"] else 0
)

validade = st.text_input(
    f"Validade ({row['DESCRIÇÃO']}):",
    value=validade_inicial,
    key=f"validade_{cod_int}_{idx}"
)

# Isso garante que mesmo que 'COD.INT' esteja repetido ou vazio,
# cada 'key' será única por conta do 'idx' (índice da linha)
