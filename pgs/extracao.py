import pandas as pd
import streamlit as st
import io
from sqlalchemy import create_engine, MetaData, select, func, desc
from sqlalchemy.orm import Session
from pgs.db import engine, tables


def exportar_para_excel(df):
    """Gera um arquivo Excel em memória"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Relatório")
    return output.getvalue()


def gerar_relatorio(tipo_relatorio):

    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return None

    with Session(engine) as session:
        if tipo_relatorio == "Fluxo de Caixa":
            caixa = tables.get("caixa")
            if not caixa:
                st.error("❌ Tabela 'caixa' não encontrada.")
                return None

            query = select(caixa.c.data, caixa.c.tipo, caixa.c.descricao, caixa.c.valor, caixa.c.id_evento).order_by(
                caixa.c.data.desc()
            )

        elif tipo_relatorio == "Patrimônio":
            patrimonio = tables.get("patrimonio")
            if not patrimonio:
                st.error("❌ Tabela 'patrimonio' não encontrada.")
                return None

            query = select(patrimonio.c.item_nome, patrimonio.c.quantidade, patrimonio.c.categoria)

        elif tipo_relatorio == "Livro Ata e Atos":
            ata = tables.get("ata")
            reunioes = tables.get("reunioes")
            atos = tables.get("ato")
            unidades = tables.get("unidades")

            if not ata or not reunioes or not atos or not unidades:
                st.error("❌ Algumas tabelas necessárias não foram encontradas.")
                return None

            query = select(
                reunioes.c.Nome.label("reuniao"),
                ata.c.titulo.label("ata_titulo"),
                ata.c.descricao.label("ata_descricao"),
                unidades.c.Nome.label("unidade"),
                atos.c.titulo.label("ato_titulo"),
                atos.c.descricao.label("ato_descricao")
            ).join(reunioes, ata.c.reuniao_id == reunioes.c.ID) \
                .outerjoin(atos, ata.c.id == atos.c.ata_id) \
                .outerjoin(unidades, atos.c.unidade_id == unidades.c.ID) \
                .order_by(reunioes.c.Nome, unidades.c.Nome)

        elif tipo_relatorio == "Mensalidade":
            user_mensalidades = tables.get("user_mensalidades")
            membros = tables.get("membros")
            mensalidades = tables.get("mensalidades")

            if not user_mensalidades or not membros or not mensalidades:
                st.error("❌ Algumas tabelas necessárias não foram encontradas.")
                return None

            query = select(
                membros.c.Nome.label("membro"),
                func.count().label("total_mensalidades"),
                func.sum(func.case([(user_mensalidades.c.status == 'Pago', mensalidades.c.valor)], else_=0)).label("total_pago"),
                func.sum(func.case([(user_mensalidades.c.status == 'Pendente', mensalidades.c.valor)], else_=0)).label("total_pendente"),
                func.sum(func.case([(user_mensalidades.c.status == 'Isento', mensalidades.c.valor)], else_=0)).label("total_isento"),
            ).join(membros, user_mensalidades.c.codigo_sgc == membros.c.codigo_sgc) \
                .join(mensalidades, user_mensalidades.c.id_mensalidade == mensalidades.c.id) \
                .group_by(membros.c.Nome) \
                .order_by(desc("total_pendente"))

        elif tipo_relatorio == "Unidades, Classes, Especialidades e Desbravadores":
            user_classes = tables.get("user_classes")
            classes = tables.get("classe")
            user_especialidades = tables.get("user_especialidades")
            especialidades = tables.get("especialidades")
            membros = tables.get("membros")
            unidades = tables.get("unidades")

            if not user_classes or not classes or not user_especialidades or not especialidades or not membros or not unidades:
                st.error("❌ Algumas tabelas necessárias não foram encontradas.")
                return None

            aba_selecionada = st.radio(
                "Selecione o tipo de relatório", ["Unidades e Classes", "Especialidades"], key="relatorio_tipo_uc"
            )

            if aba_selecionada == "Unidades e Classes":
                query = select(
                    membros.c.Nome.label("membro"),
                    unidades.c.Nome.label("unidade"),
                    classes.c.nome.label("classe")
                ).join(unidades, membros.c.id_unidade == unidades.c.ID) \
                    .outerjoin(user_classes, membros.c.codigo_sgc == user_classes.c.codigo_sgc) \
                    .outerjoin(classes, user_classes.c.codigo_classe == classes.c.codigo) \
                    .order_by(unidades.c.Nome, classes.c.nome)
            else:
                query = select(
                    membros.c.Nome.label("membro"),
                    unidades.c.Nome.label("unidade"),
                    especialidades.c.nome.label("especialidade")
                ).join(unidades, membros.c.id_unidade == unidades.c.ID) \
                    .outerjoin(user_especialidades, membros.c.codigo_sgc == user_especialidades.c.codigo_sgc) \
                    .outerjoin(especialidades, user_especialidades.c.codigo_especialidade == especialidades.c.codigo) \
                    .order_by(unidades.c.Nome, especialidades.c.nome)

        else:
            st.error("⚠️ Relatório não encontrado.")
            return None

        result = session.execute(query).fetchall()
        df = pd.DataFrame(result, columns=[col.name for col in query.selected_columns])

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

