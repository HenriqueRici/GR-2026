import pandas as pd


def evasao(base, baseEvasao):
    base = base.copy()
    base["LotacaoGR"] = base["LotacaoGR"].astype(str).str.strip()
    baseEvasao = baseEvasao.copy()
    baseEvasao["LotacaoGR"] = baseEvasao["LotacaoGR"].astype(str).str.strip()
    return pd.merge(base, baseEvasao, on=['LotacaoGR'], how='left')


def pontuacaoEvasao(row):
    freq = row.get('Frequencia', 0)
    cargo = row.get('CargoGR')

    if pd.isna(freq):
        return 0

    if cargo in ['PROFESSOR EM REGÊNCIA', 'GESTOR']:
        if freq > 0.9:
            return 100
        elif 0.8 <= freq <= 0.9:
            return 30
        return 0
    else:
        if freq > 0.85:
            return 100
        elif 0.8 <= freq <= 0.85:
            return 30
        return 0
