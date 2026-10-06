import pandas as pd
from modelos.evasaoEscolar import evasao, pontuacaoEvasao

def test_evasao():
    df_base = pd.DataFrame({'LotacaoGR': [' 101 ', '102']})
    df_evasao = pd.DataFrame({'LotacaoGR': ['101', '102'], 'Frequencia': [0.95, 0.85]})
    res = evasao(df_base, df_evasao)
    assert 'Frequencia' in res.columns
    assert res.loc[0, 'Frequencia'] == 0.95

def test_pontuacao_evasao():
    row_prof = {'CargoGR': 'PROFESSOR EM REGÊNCIA', 'Frequencia': 0.95}
    assert pontuacaoEvasao(row_prof) == 100

    row_prof_mid = {'CargoGR': 'PROFESSOR EM REGÊNCIA', 'Frequencia': 0.85}
    assert pontuacaoEvasao(row_prof_mid) == 30

    row_prof_low = {'CargoGR': 'PROFESSOR EM REGÊNCIA', 'Frequencia': 0.75}
    assert pontuacaoEvasao(row_prof_low) == 0

    row_outro = {'CargoGR': 'TAE/AAE', 'Frequencia': 0.88}
    assert pontuacaoEvasao(row_outro) == 100

    row_outro_mid = {'CargoGR': 'TAE/AAE', 'Frequencia': 0.82}
    assert pontuacaoEvasao(row_outro_mid) == 30

    row_outro_low = {'CargoGR': 'TAE/AAE', 'Frequencia': 0.70}
    assert pontuacaoEvasao(row_outro_low) == 0
