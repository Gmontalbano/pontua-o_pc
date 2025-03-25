import pandas as pd
import streamlit as st
import io

from pgs.db import conect_db


def exportar_para_excel(df):
    """Gera um arquivo Excel em memória"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Relatório")
    return output.getvalue()


def gerar_relatorio(tipo_relatorio):
    conn, cursor = conect_db()
    """Gera o DataFrame com base no tipo de relatório"""

    if tipo_relatorio == "Fluxo de Caixa":
        df = pd.read_sql("""
            SELECT data, tipo, descricao, valor, id_evento 
            FROM caixa 
            ORDER BY data DESC
        """, conn)

    elif tipo_relatorio == "Patrimônio":
        df = pd.read_sql("""
            SELECT item_nome, quantidade, categoria 
            FROM patrimonio
        """, conn)

    elif tipo_relatorio == "Livro Ata e Atos":
        df = pd.read_sql("""
            SELECT r.Nome AS reuniao, a.titulo AS ata_titulo, a.descricao AS ata_descricao, 
                   u.Nome AS unidade, at.titulo AS ato_titulo, at.descricao AS ato_descricao
            FROM ata a
            JOIN reunioes r ON a.reuniao_id = r.ID
            LEFT JOIN ato at ON a.id = at.ata_id
            LEFT JOIN unidades u ON at.unidade_id = u.ID
            ORDER BY r.Nome, u.Nome
        """, conn)

    elif tipo_relatorio == "Mensalidade":
        df = pd.read_sql("""
            SELECT m.Nome AS membro, COUNT(*) AS total_mensalidades, 
                   SUM(CASE WHEN um.status = 'Pago' THEN ms.valor ELSE 0 END) AS total_pago, 
                   SUM(CASE WHEN um.status = 'Pendente' THEN ms.valor ELSE 0 END) AS total_pendente,
                   SUM(CASE WHEN um.status = 'Isento' THEN ms.valor ELSE 0 END) AS total_isento
            FROM user_mensalidades um
            JOIN membros m ON um.codigo_sgc = m.codigo_sgc
            JOIN mensalidades ms ON um.id_mensalidade = ms.id
            GROUP BY m.Nome
            ORDER BY total_pendente DESC
        """, conn)

    elif tipo_relatorio == "Unidades, Classes, Especialidades e Desbravadores":
        aba_selecionada = st.radio("Selecione o tipo de relatório", ["Unidades e Classes", "Especialidades"],
                                   key="relatorio_tipo_uc")

        if aba_selecionada == "Unidades e Classes":
            df = pd.read_sql("""
                SELECT m.Nome AS membro, u.Nome AS unidade, c.nome AS classe
                FROM membros m
                JOIN unidades u ON m.id_unidade = u.ID
                LEFT JOIN user_classes uc ON m.codigo_sgc = uc.codigo_sgc
                LEFT JOIN classe c ON uc.codigo_classe = c.codigo
                ORDER BY u.Nome, c.nome
            """, conn)

        else:  # Especialidades
            df = pd.read_sql("""
                SELECT m.Nome AS membro, u.Nome AS unidade, e.nome AS especialidade
                FROM membros m
                JOIN unidades u ON m.id_unidade = u.ID
                LEFT JOIN user_especialidades ue ON m.codigo_sgc = ue.codigo_sgc
                LEFT JOIN especialidades e ON ue.codigo_especialidade = e.codigo
                ORDER BY u.Nome, e.nome
            """, conn)

    else:
        st.error("⚠️ Relatório não encontrado.")
        return None
    cursor.close()
    conn.close()

    return df


def aba_extracao():
    """Interface da aba de extração de relatórios"""
    st.subheader("📊 Extração de Relatórios")

    # Opções de relatório
    opcoes = [
        "Fluxo de Caixa",
        "Patrimônio",
        "Livro Ata e Atos",
        "Mensalidade",
        "Unidades, Classes, Especialidades e Desbravadores"
    ]

    tipo_relatorio = st.selectbox("📁 Selecione o Relatório", opcoes, key="relatorio_tipo")

    if st.button("📊 Gerar Relatório"):
        df_relatorio = gerar_relatorio(tipo_relatorio)

        if df_relatorio is not None and not df_relatorio.empty:
            st.dataframe(df_relatorio)

            # Criar o arquivo Excel em memória
            excel_data = exportar_para_excel(df_relatorio)

            st.download_button(
                label="📥 Baixar Relatório",
                data=excel_data,
                file_name=f"{tipo_relatorio.replace(' ', '_')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("⚠️ Nenhum dado encontrado para este relatório.")
