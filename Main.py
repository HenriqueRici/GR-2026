import os
import time
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd

from modelos.carregamentoDeDados import (
    carregaAPIFormacaoEletiva,
    carregaAPIFormacaoObrigatoria,
)
from modelos.tratamentoPagamento import defineVinc
from modelos.grupoEleitos import (
    definirCargoGR,
    proporcaoVinculo,
    tetoGr,
    trataAtribuicao,
    valorGRBase,
)
from modelos.absenteismo import (
    absenteismoFrequencias,
    absenteismoGeral,
    absenteismoLicencasAfastamentos,
    absenteismoWebPonto,
    maxAbsenteismo,
    pontuacaoAbsenteismo,
)
from modelos.evasaoEscolar import evasao, pontuacaoEvasao
from modelos.metaAdm import (
    metaAdministrativa,
    pontosEixoAlimentacao,
    pontosEixoGestao,
    pontosEixoInfraestruturaEscolar,
    pontosEixoLimpeza,
    pontosEixoPatrimonio,
    pontosEixoResultados,
)
from modelos.formacao import (
    formacaoEletivaRealizada,
    formacaoObrigatoria,
    pontuacaoFormacao,
)
from modelos.metaAprendizagem import metaAprendizagem, pontuacaoMetaAprendizagem
from modelos.pontuacao import pontuacaoGeral, valorFinalGR

from google_sheets.cliente import getGoogleSheets
from google_drive.cliente import lerDadoWebPonto
from sigabi import Sigabi


def main():
    print(f'\033[93mInício Execução: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}\033[0m')
    inicio_tempo = time.perf_counter()

    inicioGR = pd.to_datetime('2026-02-02')
    fimGR = pd.to_datetime('2026-11-30')
    fimFormacao = pd.to_datetime('2026-11-19')
    dataPagamento = pd.to_datetime('2026-12-18')

    desktop_path = Path.home() / 'Desktop' / 'GR 2026'
    desktop_path.mkdir(parents=True, exist_ok=True)

    api = Sigabi(
        login="06465533138",
        senha="123456"
    )

    baseVacancia = api.menus().consultar(
        menu=296,
        nomeBase="Base Vacância",
        filtros=[
            {"field": "Acao_ID", "operator": "in", 'value': [1, 2, 3]},
            {"field": "Cod_Situacao", "operator": "in", 'value': [12, 18]},
            {
                "field": "Tipo",
                "operator": "in",
                'value': [
                    '5017 - APOSENTADORIA', '5018 - EXONERACAO', '5019 - FALECIMENTO',
                    '4032 - POSSE EM OUTRO CARGO INACUMULAVEL',
                    '4035 - CEDÊNCIA PARA OUTRO ÓRGÃO OU PODER - SEM ONUS',
                    '4029 - CEDENCIA PARA OUTRO ORGAO OU PODER - COM ONUS C/ RESSARC',
                    '4026 - CEDÊNCIA PARA OUTRO ÓRGÃO OU PODER - COM ONUS S/ RESSARC',
                    '4025 - DESIGNAÇÃO/REGIME DE COLABORAÇÃO (ESTADO/MUNICIPIO)',
                    '4040 - DESIGNAÇÃO/REGIME DE COLABORAÇÃO (ESTADO/ESTADO)',
                    '4028 - PERMUTA (ESTADO/ESTADO)',
                    '4023 - DESIG/REG DE COLABORACAO (ENT FILANT/OUTRAS INST)',
                    '5032 - DEMISSÃO'
                ]
            }
        ],
        exclude_empty=["Vinc"],
        campos=["Ano", "Grupo", "Tipo", "Cod_Situacao", "Servidor", "CPF", "Func", "Vinc", "DataInicial", "DataFinal", "Acao_ID"],
        column_data=["DataInicial", "DataFinal"],
        column_int=["Ano", "Cod_Situacao", "Func", "Vinc", "Acao_ID"],
        column_str=["Grupo", "Tipo", "Servidor", "CPF"]
    )

    baseAtribuicao = api.menus().consultar(
        menu=330,
        nomeBase="Base Atribuição",
        filtros=[{"field": "Ano", "operator": "in", 'value': [2024, 2025, 2026]}],
        exclude_empty=["NumVinc"],
        campos=[
            "Ano", "DRE", "Municipio", "SerieLotacao", "Lotacao", "TipoLotacao", "Nome", "CPF",
            "DataInicio", "DataFinal", "CodFunc", "Funcao", "TipoProcesso", "Processo",
            "NumFunc", "NumVinc", "CargoCarreira", "TotalCH", "AdmCH", "TipoServidor",
            "TipoVinculo", "AtividadeSeap"
        ],
        column_data=["DataInicio", "DataFinal"],
        column_int=["Ano", "SerieLotacao", "CodFunc", "Processo", "NumFunc", "NumVinc", "TotalCH", "AdmCH", "AtividadeSeap"],
        column_str=["DRE", "Municipio", "Lotacao", "TipoLotacao", "Nome", "CPF", "Funcao", "TipoProcesso", "CargoCarreira", "TipoServidor", "TipoVinculo"]
    )

    baseHoraAtividade = api.menus().consultar(
        menu=296,
        nomeBase="Base Hora Atividade",
        filtros=[
            {"field": "Ano", "operator": "in", 'value': [2024, 2025, 2026]},
            {"field": "Tipo", "operator": "eq", 'value': "2002 - HORA ATIVIDADE"},
            {"field": "Acao_ID", "operator": "in", 'value': [1, 2, 3]},
            {"field": "Cod_Situacao", "operator": "in", 'value': [12, 18]}
        ],
        exclude_empty=["Vinc"],
        campos=["Tipo", "Cod_Situacao", "Servidor", "CPF", "Func", "Vinc", "Acao_ID"],
        column_data=["DataInicial", "DataFinal"],
        column_int=["Cod_Situacao", "Func", "Vinc", "Acao_ID"],
        column_str=["Tipo", "Servidor", "CPF"]
    )

    atribuicao = trataAtribuicao(baseAtribuicao, baseHoraAtividade, baseVacancia, inicioGR, fimGR)
    atribuicao.to_excel(desktop_path / 'atribuicao.xlsx', index=False)

    fim_tempo = time.perf_counter()
    duracao = fim_tempo - inicio_tempo
    tempo_formatado = str(timedelta(seconds=int(duracao)))
    print(f'\033[93mTempo decorrido: {tempo_formatado}\033[0m')


if __name__ == '__main__':
    main()
