import pandas as pd
from modelos.pontuacao import pontuacaoGeral, valorFinalGR

def test_pontuacao_geral():
    row_gestor = {
        'DiasAbsenteismo': 10,
        'CargoGR': 'GESTOR',
        'PontuacaoAbsenteismo': 150,
        'PontuacaoEvasao': 100,
        'PontuacaoFormacao': 90,
        'PontuacaoMetaAprendizagem': 180
    }
    assert pontuacaoGeral(row_gestor) == 150 + 100 + 90 + 180 + 225

    row_tae = {
        'DiasAbsenteismo': 5,
        'CargoGR': 'TAE/AAE',
        'PontuacaoAbsenteismo': 315,
        'PontuacaoEvasao': 100,
        'PontuacaoFormacao': 0,
        'PontuacaoMetaAprendizagem': 30
    }
    assert pontuacaoGeral(row_tae) == 315 + 100 + 0 + 30 + 250

    row_excesso_dias = {
        'DiasAbsenteismo': 31,
        'CargoGR': 'GESTOR',
        'PontuacaoAbsenteismo': 150,
        'PontuacaoEvasao': 100,
        'PontuacaoFormacao': 90,
        'PontuacaoMetaAprendizagem': 180
    }
    assert pontuacaoGeral(row_excesso_dias) == 0

def test_valor_final_gr():
    base = {
        'ValorGRBaseVinculo': 10000.0,
        'PontuacaoGeral': 500
    }
    assert valorFinalGR(base) == 5000.0
