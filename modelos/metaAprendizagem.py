import pandas as pd


def metaAprendizagem(base, baseTurmas, baseMetaAprendizagemUnidades, baseMetaAprendizagemTurmas):
    base = base.copy()
    baseTurmas = baseTurmas.copy()
    baseMetaAprendizagemUnidades = baseMetaAprendizagemUnidades.copy()
    baseMetaAprendizagemTurmas = baseMetaAprendizagemTurmas.copy()

    profRegencia = base[base["CargoGR"] == "PROFESSOR EM REGÊNCIA"][['LotacaoGR', 'Func', 'Vinc']].copy()
    demaisCargos = base[base["CargoGR"] != "PROFESSOR EM REGÊNCIA"][['LotacaoGR', 'Func', 'Vinc']].copy()

    baseTurmas = baseTurmas[baseTurmas['CodigoSEAP'].notna()]
    baseTurmas = baseTurmas[['CodigoSEAP', 'VinculoSEAP', 'ChaveTurma', 'CH', 'DataInicial', 'DataFinal']].rename(
        columns={'CodigoSEAP': 'Func', 'VinculoSEAP': 'Vinc'}
    )

    baseTurmas = baseTurmas.groupby(['Func', 'Vinc', 'ChaveTurma', 'DataInicial', 'DataFinal'], as_index=False)['CH'].sum()
    baseTurmas['Dias'] = (baseTurmas['DataFinal'] - baseTurmas['DataInicial']).dt.days + 1
    baseTurmas['Peso'] = baseTurmas['Dias'] * baseTurmas['CH']

    somaPeso = baseTurmas.groupby(['Func', 'Vinc'], as_index=False)['Peso'].sum().rename(columns={'Peso': 'PesoTotal'})
    baseTurmas = pd.merge(baseTurmas, somaPeso, how='left', on=['Func', 'Vinc'])

    mask = baseTurmas['PesoTotal'] > 0
    baseTurmas['PercentualMetaAprendizagem'] = 0.0
    baseTurmas.loc[mask, 'PercentualMetaAprendizagem'] = baseTurmas.loc[mask, 'Peso'] / baseTurmas.loc[mask, 'PesoTotal']

    baseTurmas = baseTurmas.groupby(['Func', 'Vinc', 'ChaveTurma'], as_index=False)['PercentualMetaAprendizagem'].sum()
    baseTurmas = pd.merge(baseTurmas, baseMetaAprendizagemTurmas, how='left', on='ChaveTurma')

    baseTurmas['NotaInicialAprendizagem'] = baseTurmas['NotaInicialAprendizagem'] * baseTurmas['PercentualMetaAprendizagem']
    baseTurmas['MetaAprendizagem'] = baseTurmas['MetaAprendizagem'] * baseTurmas['PercentualMetaAprendizagem']
    baseTurmas['NotaFinalAprendizagem'] = baseTurmas['NotaFinalAprendizagem'] * baseTurmas['PercentualMetaAprendizagem']

    baseTurmas = baseTurmas.groupby(['Func', 'Vinc'], as_index=False).agg(
        NotaInicialAprendizagem=('NotaInicialAprendizagem', 'sum'),
        MetaAprendizagem=('MetaAprendizagem', 'sum'),
        NotaFinalAprendizagem=('NotaFinalAprendizagem', 'sum')
    )

    baseTurmas['NotaInicialAprendizagem'] = baseTurmas['NotaInicialAprendizagem'].round(2)
    baseTurmas['MetaAprendizagem'] = baseTurmas['MetaAprendizagem'].round(2)
    baseTurmas['NotaFinalAprendizagem'] = baseTurmas['NotaFinalAprendizagem'].round(2)

    profRegencia = pd.merge(profRegencia, baseTurmas, how='left', on=['Func', 'Vinc'])

    demaisCargos["LotacaoGR"] = demaisCargos["LotacaoGR"].astype(str)
    baseMetaAprendizagemUnidades["LotacaoGR"] = baseMetaAprendizagemUnidades["LotacaoGR"].astype(str)

    demaisCargos = pd.merge(demaisCargos, baseMetaAprendizagemUnidades, how='left', on=['LotacaoGR'])
    metaPronta = pd.concat([demaisCargos, profRegencia], ignore_index=True)
    metaPronta = metaPronta.drop_duplicates(subset=['LotacaoGR', 'Func', 'Vinc'])

    return pd.merge(base, metaPronta, how='left', on=['LotacaoGR', 'Func', 'Vinc'])


def pontuacaoMetaAprendizagem(row):
    cargo = row.get('CargoGR')
    nota_ini = row.get('NotaInicialAprendizagem')
    nota_fim = row.get('NotaFinalAprendizagem')
    meta = row.get('MetaAprendizagem')

    if pd.isna(nota_ini) or pd.isna(nota_fim) or pd.isna(meta) or meta is None or meta == 0:
        return 0

    TABELA_PONTUACAO = {
        "TAE/AAE": (15, 30, 40, 50),
        "PROFESSOR EM REGÊNCIA": (180, 360, 405, 450),
        "GESTOR": (90, 180, 200, 225),
        "PROFESSOR FORA DE REGÊNCIA": (180, 360, 405, 450),
        "CIVIS E MILITARES LOTADOS NA SEDUC": (100, 200, 225, 300),
    }

    pontos = TABELA_PONTUACAO.get(cargo)
    if not pontos:
        return 0

    p_ini, p_meta, p_mid, p_high = pontos

    if nota_ini <= nota_fim < meta:
        return p_ini
    elif nota_fim == meta:
        return p_meta
    elif meta < nota_fim <= meta * 1.2:
        return p_mid
    elif nota_fim > meta * 1.2:
        return p_high
    else:
        return 0
