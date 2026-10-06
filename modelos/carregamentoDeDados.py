import pandas as pd
from pathlib import Path
import requests


def carregarArquivo(file_path, selected_columns=None, filters=None, drop_duplicates_by=None, exclude_empty=None, column_data=None):
    file_path_str = str(file_path)

    if file_path_str.endswith(('.xlsx', '.xls')):
        df = pd.read_excel(file_path_str, usecols=selected_columns)
    elif file_path_str.endswith('.csv'):
        df = pd.read_csv(file_path_str, sep=';', usecols=selected_columns)
    else:
        raise ValueError("O arquivo precisa ser no formato CSV ou Excel.")

    if column_data:
        for column in column_data:
            if column in df.columns:
                df[column] = pd.to_datetime(df[column], format='%d/%m/%Y %H:%M:%S', errors='coerce')
                nulos = df[column].isna()
                if nulos.any():
                    df.loc[nulos, column] = pd.to_datetime(df.loc[nulos, column], errors='coerce', dayfirst=True)

    if filters:
        for column, filter_values in filters.items():
            if column in df.columns:
                df = df[df[column].isin(filter_values)]

    if exclude_empty:
        for column in exclude_empty:
            if column in df.columns:
                df = df[df[column].notna() & (df[column].astype(str).str.strip() != '')]

    if drop_duplicates_by:
        df = df.drop_duplicates(subset=drop_duplicates_by)

    return df


def carregarPastaArquivos(file_path, selected_columns=None, column_data=None):
    arquivos_excel = list(Path(file_path).glob('*.xlsx*'))
    dfs = []

    for arquivo in arquivos_excel:
        df = pd.read_excel(arquivo, usecols=selected_columns)
        if column_data and column_data in df.columns:
            df[column_data] = pd.to_datetime(df[column_data], errors='coerce')
        dfs.append(df)

    if not dfs:
        return pd.DataFrame()

    return pd.concat(dfs, ignore_index=True)


def carregaAPIFormacaoObrigatoria(url):
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    if not data or len(data) < 2:
        return pd.DataFrame()

    header = data[0]
    rows = data[1:]

    df = pd.DataFrame(rows, columns=header)

    df['InicioExclusivo'] = pd.to_datetime(df['InicioExclusivo'], errors='coerce')
    df['FimInclusivo'] = pd.to_datetime(df['FimInclusivo'], errors='coerce')
    df['CHNecessaria'] = pd.to_numeric(df['CHNecessaria'], errors='coerce')
    df['CHCumprida'] = pd.to_numeric(df['CHCumprida'], errors='coerce')
    df['CPF'] = pd.to_numeric(df['CPF'], errors='coerce').astype('Int64')

    resultado = df.rename(columns={
        'InicioExclusivo': 'InicioPeriodo',
        'FimInclusivo': 'FimPeriodo',
        'CHNecessaria': 'CHObrigatoria',
        'CHCumprida': 'CHObrigatoriaRealizada'
    })

    for col in resultado.select_dtypes(include=["datetimetz"]).columns:
        resultado[col] = (
            resultado[col]
            .dt.tz_convert('America/Sao_Paulo')
            .dt.tz_localize(None)
            .dt.normalize()
        )
    return resultado


def carregaAPIFormacaoEletiva(url):
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    if not data or len(data) < 2:
        return pd.DataFrame()

    header = data[0]
    rows = data[1:]

    df = pd.DataFrame(rows, columns=header)
    df['CH'] = pd.to_numeric(df['CH'], errors='coerce')
    df['CPF'] = pd.to_numeric(df['CPF'], errors='coerce').astype('Int64')

    return df.rename(columns={'CH': 'CHEletiva'})
