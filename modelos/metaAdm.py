import pandas as pd

def metaAdministrativa(base, baseAdm):
    base["LotacaoGR"] = base["LotacaoGR"].astype(str).str.strip()
    baseAdm["LotacaoGR"] = baseAdm["LotacaoGR"].astype(str).str.strip()
    base = pd.merge(base, baseAdm, on=['LotacaoGR'], how='left')
    return base


def pontosEixoPatrimonio(row):
    nota_maxima = 75
    tamanho_faixa = 0.25 * nota_maxima  
    if row['CargoGR'] == 'GESTOR':
        valor_faixa = 9.375
        faixas_completas = int(row['Meta administrativa - Patrimônio Mobiliário e Imobiliário Escolar'] // tamanho_faixa)
        return (faixas_completas * valor_faixa)/2
    elif row['CargoGR'] == 'TAE/AAE':
        valor_faixa = 15.625
        faixas_completas = int(row['Meta administrativa - Patrimônio Mobiliário e Imobiliário Escolar' \
        ''] // tamanho_faixa)
        return (faixas_completas * valor_faixa)/2
    else:
        return 0



def pontosEixoInfraestruturaEscolar(row):
    nota_maxima = 75
    tamanho_faixa = 0.25 * nota_maxima  
    if row['CargoGR'] == 'GESTOR':
        valor_faixa = 9.375
        faixas_completas = int(row['Meta administrativa - Manutenção e Conservação da Infraestrutura Escolar'] // tamanho_faixa)
        return (faixas_completas * valor_faixa)/2
    elif row['CargoGR'] == 'TAE/AAE':
        valor_faixa = 15.625
        faixas_completas = int(row['Meta administrativa - Manutenção e Conservação da Infraestrutura Escolar' \
        ''] // tamanho_faixa)
        return (faixas_completas * valor_faixa)/2
    else:
        return 0

def pontosEixoLimpeza(row):
    nota_maxima = 75
    tamanho_faixa = 0.25 * nota_maxima 
    if row['CargoGR'] == 'GESTOR':
        valor_faixa = 9.375
        faixas_completas = int(row['Meta administrativa - Limpeza e Organização dos Ambientes Escolares'] // tamanho_faixa)
        return faixas_completas * valor_faixa
    elif row['CargoGR'] == 'TAE/AAE':
        valor_faixa = 15.625
        faixas_completas = int(row['Meta administrativa - Limpeza e Organização dos Ambientes Escolares'] // tamanho_faixa)
        return faixas_completas * valor_faixa
    else:
        return 0
    
def pontosEixoAlimentacao(row):
    nota_maxima = 75
    tamanho_faixa = 0.25 * nota_maxima  
    if row['CargoGR'] == 'GESTOR':
        valor_faixa = 9.375
        faixas_completas = int(row['Meta administrativa - Alimentação Escolar'] // tamanho_faixa)
        return faixas_completas * valor_faixa
    elif row['CargoGR'] == 'TAE/AAE':
        valor_faixa = 15.625
        faixas_completas = int(row['Meta administrativa - Alimentação Escolar'] // tamanho_faixa)
        return faixas_completas * valor_faixa
    else:
        return 0


def pontosEixoResultados(row):
    nota_maxima = 600
     
    if row['CargoGR'] == 'GESTOR':
        tamanho_faixa = 0.125 * nota_maxima 
        valor_faixa = 7.031
        faixas_completas = int(row['Meta administrativa - Resultados'] // tamanho_faixa)
        return faixas_completas * valor_faixa
    elif row['CargoGR'] == 'TAE/AAE':
        tamanho_faixa = 0.0625 * nota_maxima  
        valor_faixa = 3.90625
        faixas_completas = int(row['Meta administrativa - Resultados'] // tamanho_faixa)
        return faixas_completas * valor_faixa
    else:
        return 0
    

def pontosEixoGestao(row):
    nota_maxima = 100
    if row['CargoGR'] == 'GESTOR':
        tamanho_faixa = 0.125 * nota_maxima 
        valor_faixa = 7.031
        faixas_completas = int(row['Meta administrativa - Gestão'] // tamanho_faixa)
        return faixas_completas * valor_faixa
    else:
        return 0