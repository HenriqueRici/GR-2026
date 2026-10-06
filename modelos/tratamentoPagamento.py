from pathlib import Path
import pandas as pd
import os

MAPA_STATUS = {
    '4025 - DESIGNAÇÃO/REGIME DE COLABORAÇÃO (ESTADO/MUNICIPIO)': 'CONTRATO-EFETIVO ATIVO',
    '5019 - FALECIMENTO': 'FALECIDO',
    '5017 - APOSENTADORIA': 'APOSENTADO',
    '4032 - POSSE EM OUTRO CARGO INACUMULAVEL': 'POSSE EM OUTRO CARGO',
    '5018 - EXONERACAO': 'EXONERADO',
    '4028 - PERMUTA (ESTADO/ESTADO)': 'CONTRATO-EFETIVO ATIVO',
    '4029 - CEDENCIA PARA OUTRO ORGAO OU PODER - COM ONUS C/ RESSARC': 'CONTRATO-EFETIVO ATIVO',
    '4035 - CEDÊNCIA PARA OUTRO ÓRGÃO OU PODER - SEM ONUS': 'CEDIDO',
    '4026 - CEDÊNCIA PARA OUTRO ÓRGÃO OU PODER - COM ONUS S/ RESSARC': 'CEDIDO',
    '4010 - LICENCA PARA TRATAMENTO DE INTERESSE PARTICULAR': 'LIP/LAC',
    '4011 - LICENCA PARA ACOMPANHAMENTO DO CONJUGE': 'LIP/LAC',
}


def defineVinc(base, baseContrato, baseVacancia, licencasCalcVacancia, dtPagamento):
    desktop_path = Path.home() / 'Desktop' / 'GR 2025'

    baseEfetivo = base.drop_duplicates(subset=['Func', 'Vinc', 'TipoVinculo'])
    baseEfetivo = baseEfetivo[baseEfetivo['TipoVinculo'] == 'EFETIVO'].copy()

    valorGRTotal = base.groupby(['Func', 'TipoVinculo'], as_index=False)['EstimativaValorGR'].sum().rename(columns={'EstimativaValorGR': 'ValorGR'})
    valorGRTotal = valorGRTotal[valorGRTotal['ValorGR'] > 0].copy()

    contratos = valorGRTotal[valorGRTotal['TipoVinculo'] == 'TEMPORÁRIO'].copy()

    if not baseContrato.empty:
        baseContrato = baseContrato[baseContrato['TipoServidor'] != "PROFESSOR"].copy()
        baseContrato = baseContrato.groupby(['Func', 'Vinc'], as_index=False).agg(
            DataInicioVinculo=('DataInicial', 'min'),
            DataFinalVinculo=('DataFinal', 'max')
        )
        baseContrato = baseContrato[baseContrato['DataFinalVinculo'] >= pd.to_datetime('2025-01-01')].copy()

        ativos = baseContrato[(baseContrato['DataInicioVinculo'] <= dtPagamento) & (baseContrato['DataFinalVinculo'] >= dtPagamento)].copy()
        ativos['STATUS'] = 'CONTRATO-EFETIVO ATIVO'
        melhor_vinc_ativos = ativos.sort_values(['Func', 'DataInicioVinculo'], ascending=[True, False]).drop_duplicates('Func', keep='first')

        nao_ativos = baseContrato[~baseContrato['Func'].isin(melhor_vinc_ativos['Func'])]
        antes = nao_ativos[nao_ativos['DataFinalVinculo'] <= dtPagamento].copy()
        antes['STATUS'] = 'CONTRATO INATIVO'
        melhor_vinc_nao_ativo = antes.sort_values(['Func', 'DataFinalVinculo'], ascending=[True, False]).drop_duplicates('Func', keep='first')

        melhorVincContrato = pd.concat([melhor_vinc_ativos, melhor_vinc_nao_ativo], ignore_index=True)[['Func', 'Vinc', 'STATUS']]
        contratos = pd.merge(contratos, melhorVincContrato, on=['Func'], how='left')
    else:
        contratos['Vinc'] = None
        contratos['STATUS'] = None

    contratos = contratos[['Func', 'Vinc', 'ValorGR', 'STATUS']]

    lipLac = licencasCalcVacancia[licencasCalcVacancia['Tipo'].isin([
        '4010 - LICENCA PARA TRATAMENTO DE INTERESSE PARTICULAR',
        '4011 - LICENCA PARA ACOMPANHAMENTO DO CONJUGE'
    ])] if not licencasCalcVacancia.empty else pd.DataFrame(columns=['Tipo'])

    baseVacancia = pd.concat([baseVacancia, lipLac], ignore_index=True)
    if not baseVacancia.empty:
        baseVacancia.loc[baseVacancia['DataFinal'] == pd.Timestamp('1753-01-01'), 'DataFinal'] = dtPagamento
        baseVacancia = baseVacancia[baseVacancia['DataFinal'] >= dtPagamento][['Func', 'Vinc', 'Tipo']].drop_duplicates()

    efetivos = pd.merge(baseEfetivo, baseVacancia, on=['Func', 'Vinc'], how='left')
    efetivos['STATUS'] = efetivos['Tipo'].map(MAPA_STATUS).fillna('CONTRATO-EFETIVO ATIVO')

    efetivos = pd.merge(efetivos, valorGRTotal, on=['Func'], how='left')[['Func', 'Vinc', 'ValorGR', 'STATUS']]

    concat = pd.concat([contratos, efetivos], ignore_index=True)
    concat = concat[concat['ValorGR'] > 0].copy()

    ordem_status = [
        'FALECIDO', 'CONTRATO-EFETIVO ATIVO', 'APOSENTADO', 'POSSE EM OUTRO CARGO',
        'LIP/LAC', 'EXONERADO', 'CEDIDO', 'CONTRATO INATIVO', 'INDEFINIDO'
    ]

    concat['STATUS'] = pd.Categorical(concat['STATUS'], categories=ordem_status, ordered=True)
    melhorVinc = concat.sort_values(['Func', 'STATUS']).groupby('Func', as_index=False).first()
    melhorVinc['STATUS'] = melhorVinc['STATUS'].fillna("INDEFINIDO")

    pasta = desktop_path / "BASE PAGAMENTO"
    pasta.mkdir(parents=True, exist_ok=True)

    melhorVinc['ValorGR'] = melhorVinc['ValorGR'].round(2)

    for status, grupo in melhorVinc.groupby('STATUS', observed=False):
        nome_arquivo = f"{status}.xlsx".replace("/", "-")
        caminho_completo = os.path.join(pasta, nome_arquivo)
        grupo_export = grupo.drop(columns=['STATUS'])
        grupo_export.to_excel(caminho_completo, index=False)

    return melhorVinc
