import pandas as pd
from modelos.metaAdm import (
    metaAdministrativa,
    pontosEixoPatrimonio,
    pontosEixoInfraestruturaEscolar,
    pontosEixoLimpeza,
    pontosEixoAlimentacao,
    pontosEixoResultados,
    pontosEixoGestao
)

def test_meta_adm():
    base = pd.DataFrame({'LotacaoGR': ['101']})
    base_adm = pd.DataFrame({'LotacaoGR': ['101'], 'Meta administrativa - Gestão': [50.0]})
    res = metaAdministrativa(base, base_adm)
    assert 'Meta administrativa - Gestão' in res.columns

def test_pontos_eixos():
    row_gestor = {
        'CargoGR': 'GESTOR',
        'Meta administrativa - Patrimônio Mobiliário e Imobiliário Escolar': 37.5,
        'Meta administrativa - Manutenção e Conservação da Infraestrutura Escolar': 37.5,
        'Meta administrativa - Limpeza e Organização dos Ambientes Escolares': 37.5,
        'Meta administrativa - Alimentação Escolar': 37.5,
        'Meta administrativa - Resultados': 150.0,
        'Meta administrativa - Gestão': 25.0
    }
    # 37.5 // (0.25*75 = 18.75) = 2. faixas_completas = 2. 2 * 9.375 / 2 = 9.375
    assert pontosEixoPatrimonio(row_gestor) == 9.375
    assert pontosEixoInfraestruturaEscolar(row_gestor) == 9.375
    assert pontosEixoLimpeza(row_gestor) == 2 * 9.375
    assert pontosEixoAlimentacao(row_gestor) == 2 * 9.375
    # Resultados: 150.0 // (0.125*600 = 75) = 2. faixas_completas = 2. 2 * 7.031 = 14.062
    assert pontosEixoResultados(row_gestor) == 2 * 7.031
    # Gestao: 25.0 // (0.125*100 = 12.5) = 2. faixas_completas = 2. 2 * 7.031 = 14.062
    assert pontosEixoGestao(row_gestor) == 2 * 7.031
