import pandas as pd
from modelos.metaAprendizagem import pontuacaoMetaAprendizagem

def test_pontuacao_meta_aprendizagem():
    row_prof = {
        'CargoGR': 'PROFESSOR EM REGÊNCIA',
        'NotaInicialAprendizagem': 5.0,
        'NotaFinalAprendizagem': 8.0,
        'MetaAprendizagem': 8.0
    }
    assert pontuacaoMetaAprendizagem(row_prof) == 360

    row_gestor = {
        'CargoGR': 'GESTOR',
        'NotaInicialAprendizagem': 5.0,
        'NotaFinalAprendizagem': 10.0,
        'MetaAprendizagem': 8.0
    }
    # 10.0 > 8.0 * 1.2 (9.6) -> 225
    assert pontuacaoMetaAprendizagem(row_gestor) == 225
