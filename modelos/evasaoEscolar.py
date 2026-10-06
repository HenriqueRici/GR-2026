import pandas as pd


def evasao(base, baseEvasao):
    base["LotacaoGR"] = base["LotacaoGR"].astype(str).str.strip()
    baseEvasao["LotacaoGR"] = baseEvasao["LotacaoGR"].astype(str).str.strip()
    base = pd.merge(base, baseEvasao, on=['LotacaoGR'], how='left')

    return base

def pontuacaoEvasao(row):    
    if row['CargoGR'] in ['PROFESSOR EM REGÊNCIA', 'GESTOR']:
        if row['Frequencia'] > 0.9:
            return 100
        elif  0.8 <= row['Frequencia'] <= 0.9:
            return 30
        else: 0
    else:
        if row['Frequencia'] > 0.85:
            return 100
        elif  0.8 <= row['Frequencia'] <= 0.85:
            return 30
        else: 0

    return 0
