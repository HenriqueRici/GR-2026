import pandas as pd
from modelos.absenteismo import pontuacaoAbsenteismo, maxAbsenteismo, absenteismoLicencasAfastamentos

def test_pontuacao_absenteismo():
    row_prof = {'CargoGR': 'PROFESSOR EM REGÊNCIA', 'DiasAbsenteismo': 0}
    assert pontuacaoAbsenteismo(row_prof) == 300
    assert maxAbsenteismo(row_prof) == 300

    row_tae = {'CargoGR': 'TAE/AAE', 'DiasAbsenteismo': 0}
    assert pontuacaoAbsenteismo(row_tae) == 450
    assert maxAbsenteismo(row_tae) == 450

def test_absenteismo_licencas():
    base_lic = pd.DataFrame({
        'Func': [1],
        'Vinc': [1],
        'DataInicial': [pd.to_datetime('2026-01-01')],
        'DataFinal': [pd.to_datetime('2026-03-01')],
        'Tipo': ['LICENCA HEALTH']
    })
    res = absenteismoLicencasAfastamentos(base_lic, pd.to_datetime('2026-02-02'), pd.to_datetime('2026-11-30'))
    assert len(res) == 1
    assert res.iloc[0]['DataInicial'] == pd.to_datetime('2026-02-02')
