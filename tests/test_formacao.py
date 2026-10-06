import pandas as pd
from modelos.formacao import formacaoObrigatoria, formacaoEletivaRealizada, pontuacaoFormacao

def test_formacao_eletiva_e_pontuacao():
    vinculos = pd.DataFrame({'CPF': [12345678900]})
    eletivas = pd.DataFrame({'CPF': [12345678900], 'CHEletiva': [150]})
    res = formacaoEletivaRealizada(vinculos, eletivas)
    assert res.loc[0, 'CHEletiva'] == 150

    row_valida = {'CHObrigatoriaRealizada': 100, 'CHObrigatoria': 100, 'CHEletiva': 150}
    assert pontuacaoFormacao(row_valida) == 90

    row_invalida = {'CHObrigatoriaRealizada': 80, 'CHObrigatoria': 100, 'CHEletiva': 150}
    assert pontuacaoFormacao(row_invalida) == 0

def test_formacao_obrigatoria():
    vinculos = pd.DataFrame({
        'CPF': [123],
        'NumVinc': [1],
        'CargoGR': ['PROFESSOR EM REGÊNCIA'],
        'CH': [40],
        'DataInicio': [pd.to_datetime('2026-02-01')],
        'DataFinal': [pd.to_datetime('2026-11-30')]
    })
    formacao = pd.DataFrame({
        'CPF': [123],
        'InicioPeriodo': [pd.to_datetime('2026-03-01')],
        'FimPeriodo': [pd.to_datetime('2026-05-01')],
        'CHObrigatoria': [100]
    })
    res = formacaoObrigatoria(vinculos, formacao, pd.to_datetime('2026-02-01'), colFormacao='CHObrigatoria')
    assert 'CHObrigatoria' in res.columns
    assert res.loc[0, 'CHObrigatoria'] == 100
