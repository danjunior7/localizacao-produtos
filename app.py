# Esse trecho deve estar dentro do loop for idx, row in df_pagina.iterrows():

for idx, row in df_pagina.iterrows():
    cod_int = row.get("COD.INT", "")
    valor_inicial = progresso_antigo.get(cod_int, {}).get("LOCAL INFORMADO", "")
    validade_raw = progresso_antigo.get(cod_int, {}).get("VALIDADE", "")
    validade_inicial = "" if pd.isna(validade_raw) else str(validade_raw)

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
