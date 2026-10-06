import gspread
import pandas as pd
from datetime import datetime
from pathlib import Path
from google.oauth2.service_account import Credentials


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


# Caminho do arquivo JSON
CAMINHO_CREDENCIAIS = Path(__file__).parent / "credenciais.json"


# Autenticação
credenciais = Credentials.from_service_account_file(
    CAMINHO_CREDENCIAIS,
    scopes=SCOPES
)

cliente = gspread.authorize(credenciais)


# Abre a planilha
planilha = cliente.open("BASES GR 2026")


def getGoogleSheets(nome_aba, column_data=None):

    aba = planilha.worksheet(nome_aba)

    # Retorna tudo como texto
    dados = aba.get_all_values()

    # Primeira linha = cabeçalho
    df = pd.DataFrame(dados[1:], columns=dados[0])

    # Define colunas como data
    if column_data:

        for column in column_data:

            if column not in df.columns:
                continue

            df[column] = pd.to_datetime(
                df[column],
                format="%d/%m/%Y %H:%M:%S",
                errors="coerce"
            )

            valores_nulos = df[column].isna()

            if valores_nulos.any():

                df.loc[valores_nulos, column] = pd.to_datetime(
                    df.loc[valores_nulos, column],
                    errors="coerce",
                    dayfirst=True
                )

    print(
        f'\033[92mBase {nome_aba} concluído em '
        f'{datetime.now().strftime("%d/%m/%Y %H:%M:%S")}\033[0m'
    )

    return df


def set_df(df, nome_aba):

    aba = planilha.worksheet(nome_aba)

    aba.clear()

    dados = [df.columns.tolist()] + df.fillna("").values.tolist()

    aba.update(dados, "A1")