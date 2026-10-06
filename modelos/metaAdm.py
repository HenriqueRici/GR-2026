import pandas as pd


def metaAdministrativa(base, baseAdm):
    base = base.copy()
    base["LotacaoGR"] = base["LotacaoGR"].astype(str).str.strip()
    baseAdm = baseAdm.copy()
    baseAdm["LotacaoGR"] = baseAdm["LotacaoGR"].astype(str).str.strip()
    return pd.merge(base, baseAdm, on=['LotacaoGR'], how='left')


def _calcular_pontos_faixa(row, col_name, nota_maxima, percentual_faixa, valor_gestor, valor_tae, metade=False):
    val = row.get(col_name)
    if pd.isna(val) or val is None:
        return 0.0

    cargo = row.get('CargoGR')
    tamanho_faixa = percentual_faixa * nota_maxima
    if tamanho_faixa <= 0:
        return 0.0

    faixas_completas = int(val // tamanho_faixa)

    if cargo == 'GESTOR':
        res = faixas_completas * valor_gestor
        return res / 2.0 if metade else res
    elif cargo == 'TAE/AAE':
        res = faixas_completas * valor_tae
        return res / 2.0 if metade else res
    else:
        return 0.0


def pontosEixoPatrimonio(row):
    return _calcular_pontos_faixa(
        row,
        'Meta administrativa - Patrimônio Mobiliário e Imobiliário Escolar',
        nota_maxima=75,
        percentual_faixa=0.25,
        valor_gestor=9.375,
        valor_tae=15.625,
        metade=True
    )


def pontosEixoInfraestruturaEscolar(row):
    return _calcular_pontos_faixa(
        row,
        'Meta administrativa - Manutenção e Conservação da Infraestrutura Escolar',
        nota_maxima=75,
        percentual_faixa=0.25,
        valor_gestor=9.375,
        valor_tae=15.625,
        metade=True
    )


def pontosEixoLimpeza(row):
    return _calcular_pontos_faixa(
        row,
        'Meta administrativa - Limpeza e Organização dos Ambientes Escolares',
        nota_maxima=75,
        percentual_faixa=0.25,
        valor_gestor=9.375,
        valor_tae=15.625,
        metade=False
    )


def pontosEixoAlimentacao(row):
    return _calcular_pontos_faixa(
        row,
        'Meta administrativa - Alimentação Escolar',
        nota_maxima=75,
        percentual_faixa=0.25,
        valor_gestor=9.375,
        valor_tae=15.625,
        metade=False
    )


def pontosEixoResultados(row):
    return _calcular_pontos_faixa(
        row,
        'Meta administrativa - Resultados',
        nota_maxima=600,
        percentual_faixa=0.125 if row.get('CargoGR') == 'GESTOR' else 0.0625,
        valor_gestor=7.031,
        valor_tae=3.90625,
        metade=False
    )


def pontosEixoGestao(row):
    return _calcular_pontos_faixa(
        row,
        'Meta administrativa - Gestão',
        nota_maxima=100,
        percentual_faixa=0.125,
        valor_gestor=7.031,
        valor_tae=0.0,
        metade=False
    )
