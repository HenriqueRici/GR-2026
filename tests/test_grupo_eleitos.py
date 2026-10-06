import pandas as pd
from modelos.grupoEleitos import tetoGr, valorGRBase, trataVacancia, calcular_periodo_unico

def test_calcular_periodo_unico():
    df = pd.DataFrame({
        'dtini': [pd.to_datetime('2026-02-01'), pd.to_datetime('2026-02-10')],
        'dtfim': [pd.to_datetime('2026-02-15'), pd.to_datetime('2026-02-20')]
    })
    total = calcular_periodo_unico(df, col_data_ini='dtini', col_data_fim='dtfim')
    # 02-01 to 02-20 = 20 days
    assert total == 20

def test_valor_gr_base():
    row_prof = {'CargoGR': 'PROFESSOR EM REGÊNCIA', 'PercentualGRVinculo': 1.0}
    val = valorGRBase(row_prof)
    assert abs(val - (11015.44 * 1.054)) < 0.01

def test_teto_gr():
    df = pd.DataFrame({
        'CPF': ['12345678900'],
        'DataInicio': [pd.to_datetime('2026-02-02')],
        'DataFinal': [pd.to_datetime('2026-11-30')],
        'CH': [30]
    })
    res = tetoGr(df)
    assert 'PercentualGRServidor' in res.columns
    assert len(res) == 1
