from pathlib import Path
import io
from datetime import datetime
import pandas as pd

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload


def lerDadoWebPonto(column_data=None, campos=None):
  
    # ==========================================================
    # LOCALIZA O ARQUIVO DE CREDENCIAL
    # ==========================================================

    pasta_script = Path(__file__).resolve().parent

    arquivo_credencial = pasta_script / "credenciais.json"


    # ==========================================================
    # AUTENTICAÇÃO
    # ==========================================================

    scopes = [
        "https://www.googleapis.com/auth/drive.readonly"
    ]

    credenciais = service_account.Credentials.from_service_account_file(
        arquivo_credencial,
        scopes=scopes
    )

    drive = build(
        "drive",
        "v3",
        credentials=credenciais
    )


    # ==========================================================
    # PROCURA OS ARQUIVOS EXCEL
    # ==========================================================

    id_pasta = "1EUfbEuEpEQb6fEdmSpzpT6s_Ql4-SMGE"

    query = f"""
        '{id_pasta}' in parents
        and trashed = false
        and (
            mimeType = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            or mimeType = 'application/vnd.ms-excel'
        )
    """

    resultado = drive.files().list(
        q=query,
        fields="files(id, name, mimeType)",
        pageSize=1000
    ).execute()

    arquivos = resultado.get("files", [])


    print(f"\tArquivos WebPonto encontrados: {len(arquivos)}")


    # ==========================================================
    # LER OS ARQUIVOS
    # ==========================================================

    dataframes = []

    for arquivo in arquivos:

        print(f"\tLendo: {arquivo['name']}")

        try:

            request = drive.files().get_media(
                fileId=arquivo["id"]
            )

            arquivo_bytes = io.BytesIO()

            downloader = MediaIoBaseDownload(
                arquivo_bytes,
                request
            )

            concluido = False

            while not concluido:

                status, concluido = downloader.next_chunk()

            arquivo_bytes.seek(0)


            # Lê o Excel
            df = pd.read_excel(arquivo_bytes)


            # Guarda o nome do arquivo
            df["Arquivo_Origem"] = arquivo["name"]


            dataframes.append(df)


        except Exception as erro:

            print(
                f"ERRO ao ler {arquivo['name']}: {erro}"
            )


    # ==========================================================
    # JUNTA TODOS OS ARQUIVOS
    # ==========================================================

    if not dataframes:

        print("Nenhum arquivo Excel foi lido.")

        return pd.DataFrame()


    df_final = pd.concat(
        dataframes,
        ignore_index=True
    )

    print(f"\tArquivos lidos: {len(dataframes)}")
    print(f"\tRegistros: {len(df_final)}")

    if column_data:

        for column in column_data:

            if column not in df.columns:
                continue

            # Primeiro tenta o formato completo
            df[column] = pd.to_datetime(
                df[column],
                format="%d/%m/%Y %H:%M:%S",
                errors="coerce"
            )

            # Para valores que não entraram no formato acima,
            # tenta novamente de forma genérica.
            valores_nulos = df[column].isna()

            if valores_nulos.any():

                df.loc[valores_nulos, column] = pd.to_datetime(
                    df.loc[valores_nulos, column],
                    errors="coerce",
                    dayfirst=True
                ) 

    df_final = df_final[campos]
    print(f'\033[92mBase WebPonto concluído em {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}\033[0m')
    return df_final