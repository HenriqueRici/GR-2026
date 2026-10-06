import pandas as pd


def formacaoObrigatoria(vinculos, formacao, inicioGR, colFormacao=None):
    if formacao.empty or colFormacao not in formacao.columns:
        vinculos = vinculos.copy()
        vinculos[colFormacao] = 0
        return vinculos

    formacao = formacao.copy()
    formacao['InicioPeriodo'] = formacao['InicioPeriodo'].clip(lower=inicioGR)
    formacao['FimPeriodo'] = formacao['FimPeriodo'].clip(lower=inicioGR)

    vinculosRegencia = vinculos[vinculos["CargoGR"] == "PROFESSOR EM REGÊNCIA"].copy()
    if vinculosRegencia.empty:
        vinculos = vinculos.copy()
        vinculos[colFormacao] = 0
        return vinculos

    formacao["CPF"] = formacao["CPF"].astype("int64")
    vinculosRegencia["CPF"] = vinculosRegencia["CPF"].astype("int64")

    col_val = colFormacao + '_f' if colFormacao in vinculosRegencia.columns else colFormacao

    merged = pd.merge(formacao, vinculosRegencia, on='CPF', suffixes=('_f', '_v'))
    validos = merged[
        (merged['DataInicio'] <= merged['FimPeriodo']) &
        (merged['DataFinal'] >= merged['InicioPeriodo'])
    ].copy()

    if validos.empty:
        vinculos = vinculos.copy()
        vinculos[colFormacao] = 0
        return vinculos

    soma_ch = validos.groupby(['CPF', 'InicioPeriodo', 'FimPeriodo'])['CH'].transform('sum')
    validos['proporcao'] = pd.Series(0.0, index=validos.index)
    mask = soma_ch > 0
    validos.loc[mask, 'proporcao'] = validos.loc[mask, 'CH'] / soma_ch[mask]
    validos[colFormacao] = validos[col_val] * validos['proporcao']

    df_resultados = validos.groupby(['CPF', 'NumVinc'], as_index=False)[colFormacao].sum()

    df_final = pd.merge(vinculos, df_resultados, how='left', on=['CPF', 'NumVinc'])
    df_final.loc[df_final['CargoGR'] != 'PROFESSOR EM REGÊNCIA', colFormacao] = 0
    df_final[colFormacao] = df_final[colFormacao].fillna(0)

    return df_final


def formacaoEletivaRealizada(vinculos, formacaoEletiva):
    vinculos = vinculos.copy()
    if formacaoEletiva.empty:
        vinculos["CHEletiva"] = 0
        return vinculos

    formacaoEletiva = formacaoEletiva.copy()
    formacaoEletiva["CPF"] = formacaoEletiva["CPF"].astype("int64")
    agrupado = formacaoEletiva.groupby(['CPF'], as_index=False)['CHEletiva'].sum()

    vinculos["CPF"] = vinculos["CPF"].astype("int64")
    vinculos = pd.merge(vinculos, agrupado, how='left', on='CPF')
    vinculos["CHEletiva"] = vinculos["CHEletiva"].fillna(0)
    return vinculos


def pontuacaoFormacao(row):
    ch_realizada = row.get('CHObrigatoriaRealizada', 0)
    ch_obrigatoria = row.get('CHObrigatoria', 0)
    ch_eletiva = row.get('CHEletiva', 0)

    if ch_realizada >= ch_obrigatoria:
        if 100 <= ch_eletiva <= 130:
            return 54
        elif 131 <= ch_eletiva <= 180:
            return 90
        elif 181 <= ch_eletiva <= 199:
            return 126
        elif ch_eletiva >= 200:
            return 150

    return 0
