""""
Coletor automático de itens de contratações PNCP (Lei 14.133/2021)
Versão 4.0 – Com Inteligência de Extração de Texto
"""
import requests
import pandas as pd
import re # Biblioteca para buscar padrões de texto
from datetime import date, timedelta

# ============================================================
# 🧠 NOVA FUNÇÃO: EXTRAÇÃO AUTOMÁTICA DE ÁREA
# ============================================================
def extrair_area_da_descricao(texto):
    """
    Lê um texto e tenta encontrar padrões como '100m²', '1.000,00 m2', etc.
    Retorna o maior valor encontrado (assumindo que seja a área total) ou 0.
    """
    if not isinstance(texto, str):
        return 0.0
    
    # Padrão Regex: Procura números seguidos de m2, m² ou metros quadrados
    # Explicando o padrão: (números com ponto ou virgula) + espaço opcional + (unidade)
    padrao = r'([\d\.,]+)\s*(?:m²|m2|metros\s*quadrados)'
    
    matches = re.findall(padrao, texto, re.IGNORECASE)
    
    valores_encontrados = []
    for valor_str in matches:
        try:
            # Limpa o número: remove pontos de milhar, troca vírgula por ponto
            limpo = valor_str.replace('.', '').replace(',', '.')
            valor_float = float(limpo)
            # Filtra valores absurdos (ex: ano 2024 interpretado como m²)
            if 10 < valor_float < 1000000: 
                valores_encontrados.append(valor_float)
        except:
            continue
            
    if valores_encontrados:
        return max(valores_encontrados) # Retorna o maior valor achado
    return 0.0

# ============================================================
# 🌐 CHAMADA À API (MANTIDA E OTIMIZADA)
# ============================================================
def buscar_itens_pncp(cod_item_catalogo=None, data_inicial=None, data_final=None,
                      filtros_opcionais=None, tamanho_pagina=100):
    
    base_url = "https://dadosabertos.compras.gov.br/modulo-contratacoes/2_consultarItensContratacoes_PNCP_14133"

    params = {
        "pagina": 1,
        "tamanhoPagina": tamanho_pagina,
        "dataInclusaoPncpInicial": data_inicial,
        "dataInclusaoPncpFinal": data_final,
    }
    
    if filtros_opcionais:
        params.update(filtros_opcionais)

    try:
        resp = requests.get(base_url, params=params, timeout=30)
        if resp.status_code == 200:
            dados = resp.json()
            return dados.get("resultado", [])
        else:
            return []
    except Exception as e:
        print(f"Erro na conexão: {e}")
        return []

# As funções de Excel/HTML anteriores continuam existindo aqui se você precisar, 
# mas para o App de Benchmarking, só precisamos dessas acima.
