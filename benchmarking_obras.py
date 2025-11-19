import streamlit as st
import pandas as pd
import pncp_backend
from datetime import date

# ============================================================
# 🎨 CONFIGURAÇÃO VISUAL
# ============================================================
st.set_page_config(page_title="Benchmarking Inteligente de Obras", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    .stApp { background-color: #f0f2f6; }
    .big-font { font-size: 18px !important; color: #333; }
    .destaque { background-color: #d1e7dd; padding: 10px; border-radius: 10px; border: 1px solid #badbcc; }
</style>
""", unsafe_allow_html=True)

st.title("🏗️ Benchmarking Inteligente: Obras e Engenharia")
st.markdown("""
**Automação:** O sistema tentará ler a descrição e **sugerir a Área (m²)** automaticamente.
**Fontes:** Além do PNCP, use os links rápidos para buscar o edital no Google (Diários Oficiais).
""")

# ============================================================
# 🔍 FILTROS LATERAIS
# ============================================================
with st.sidebar:
    st.header("⚙️ Configuração da Busca")
    termo_busca = st.text_input("O que você procura?", placeholder="Ex: Construção escola 12 salas")
    
    c1, c2 = st.columns(2)
    ano_ini = c1.number_input("De", 2023, 2025, 2024)
    ano_fim = c2.number_input("Até", 2023, 2025, 2025)
    
    st.markdown("---")
    st.caption("Filtros Avançados")
    apenas_servicos = st.checkbox("Apenas Serviços", True)
    usar_google = st.checkbox("Gerar Links do Google", True)
    
    btn_buscar = st.button("🔎 Rastrear Preços", type="primary")

# ============================================================
# 🧠 LÓGICA
# ============================================================
if btn_buscar and termo_busca:
    with st.spinner("🤖 O robô está lendo o PNCP e analisando descrições..."):
        resultados = pncp_backend.buscar_itens_pncp(
            data_inicial=f"{ano_ini}-01-01",
            data_final=f"{ano_fim}-12-31",
            filtros_opcionais={"q": termo_busca, "materialOuServico": "S" if apenas_servicos else ""},
            tamanho_pagina=100
        )

    if not resultados:
        st.warning("Nenhum contrato encontrado. Tente termos mais genéricos.")
    else:
        df = pd.DataFrame(resultados)
        
        # 1. Tratamento Básico
        df['Órgão'] = df['orgaoEntidade'].apply(lambda x: x.get('razaoSocial', ''))
        df['Valor'] = pd.to_numeric(df['valorUnitarioResultado'], errors='coerce').fillna(0)
        df = df[df['Valor'] > 0] # Remove zerados
        
        # 2. AUTOMAÇÃO: Extrair Área da Descrição
        # Aqui chamamos a nova função do backend
        df['Área Sugerida'] = df['descricaoResumida'].apply(pncp_backend.extrair_area_da_descricao)
        
        # 3. Criação de Links Externos (Google Hacking)
        def gerar_google_link(row):
            # Cria uma busca específica no Google por PDFs em sites do governo
            query = f'site:gov.br filetype:pdf "{row["descricaoResumida"][:50]}"'
            return f"https://www.google.com/search?q={query}"

        df['Link PNCP'] = df['numeroControlePncp'].apply(lambda x: f"https://pncp.gov.br/app/contratacoes/{x}")
        df['Link Google'] = df.apply(gerar_google_link, axis=1)
        
        # 4. Preparar Tabela para o Usuário
        df_show = df[['dataResultado', 'Órgão', 'descricaoResumida', 'Valor', 'Link PNCP', 'Link Google', 'Área Sugerida']].copy()
        
        # Adiciona colunas de controle
        df_show.insert(0, "Usar", False)
        
        # Renomeia
        df_show.rename(columns={
            'dataResultado': 'Data',
            'descricaoResumida': 'Descrição',
            'Área Sugerida': 'Área (m²)' # O usuário pode corrigir esse valor
        }, inplace=True)

        # Formata Data
        df_show['Data'] = pd.to_datetime(df_show['Data']).dt.strftime('%d/%m/%Y')
        
        st.session_state['df_obras'] = df_show

# ============================================================
# 📝 TABELA INTERATIVA E RESULTADOS
# ============================================================
if 'df_obras' in st.session_state:
    
    st.divider()
    st.subheader("Analise os Contratos Encontrados")
    st.info("💡 Dica: Se a coluna **'Área (m²)'** veio preenchida, o robô achou esse número no texto. **Verifique se está correto!**")

    # Editor de Dados Poderoso
    df_editado = st.data_editor(
        st.session_state['df_obras'],
        column_config={
            "Link PNCP": st.column_config.LinkColumn("📄 PNCP", display_text="Abrir"),
            "Link Google": st.column_config.LinkColumn("🌍 Google", display_text="Buscar PDF"),
            "Valor": st.column_config.NumberColumn(format="R$ %.2f"),
            "Área (m²)": st.column_config.NumberColumn(format="%.2f", help="Edite se o robô errou"),
            "Descrição": st.column_config.TextColumn(width="medium"),
        },
        hide_index=True,
        use_container_width=True
    )

    # Lógica de Cálculo (Índice R$/m²)
    selecionados = df_editado[df_editado['Usar'] == True].copy()
    
    if not selecionados.empty:
        # Calcula o índice apenas para as linhas selecionadas e com área > 0
        selecionados['Indice'] = selecionados.apply(
            lambda x: x['Valor'] / x['Área (m²)'] if x['Área (m²)'] > 0 else 0, axis=1
        )
        
        # Remove erros de divisão por zero
        validos = selecionados[selecionados['Indice'] > 0]
        
        st.divider()
        st.markdown('<div class="destaque">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        
        media = validos['Indice'].mean()
        mediana = validos['Indice'].median()
        
        col1.metric("Média do Mercado", f"R$ {media:,.2f}/m²")
        col2.metric("Mediana (Mais Seguro)", f"R$ {mediana:,.2f}/m²")
        col3.metric("Amostras Utilizadas", f"{len(validos)} contratos")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Botão de Exportar
        csv = validos.to_csv(sep=";", decimal=",", index=False)
        st.download_button("💾 Baixar Memória de Cálculo (Excel)", csv, "memoria_calculo.csv", "text/csv")
        
        # Detalhe dos itens usados
        with st.expander("Ver itens considerados no cálculo"):
            st.dataframe(validos[['Órgão', 'Descrição', 'Valor', 'Área (m²)', 'Indice']])
            
    elif df_editado['Usar'].any():
        st.warning("Você selecionou itens, mas a Área (m²) está zerada. Preencha a área para calcular.")
