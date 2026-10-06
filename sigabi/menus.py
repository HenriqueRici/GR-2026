import pandas as pd
from time import sleep
from datetime import datetime


class Menus:

    def __init__(self, cliente):
        self.cliente = cliente

    def _preparar_filtros(self, filtros):
        if not filtros:
            return filtros

        filtros_convertidos = []
        for filtro in filtros:
            if not isinstance(filtro, dict):
                raise TypeError("Cada filtro deve ser um dicionário.")

            filtro = filtro.copy()
            operador = filtro.get("operator")
            valor = filtro.get("value")

            if operador == "in":
                if isinstance(valor, (tuple, set)):
                    valor = list(valor)
                elif not isinstance(valor, list):
                    if isinstance(valor, str):
                        valor = [item.strip() for item in valor.split(",") if item.strip() != ""]
                    else:
                        valor = [valor]
                filtro["value"] = valor

            filtros_convertidos.append(filtro)

        return filtros_convertidos

    def consultar(
        self,
        nomeBase,
        menu,
        filtros=None,
        campos=None,
        ordenar=None,
        per_page=5000,
        column_data=None,
        column_int=None,
        column_str=None,
        exclude_empty=None
    ):
        url = f"{self.cliente.base_url}/menus/{menu}/execute"
        pagina = 1
        dados = []
        filtros = self._preparar_filtros(filtros)

        while True:
            body = {
                "pagination": {
                    "page": pagina,
                    "per_page": per_page
                }
            }
            if filtros:
                body["filters"] = filtros
            if campos:
                body["select_fields"] = campos
            if ordenar:
                body["order_by"] = ordenar

            r = self.cliente.session.post(
                url,
                headers=self.cliente.headers,
                json=body,
                timeout=120
            )

            if r.status_code in (401, 403):
                self.cliente.renovar_token()
                r = self.cliente.session.post(
                    url,
                    headers=self.cliente.headers,
                    json=body,
                    timeout=120
                )

            if r.status_code != 200:
                print(f"RESPOSTA DA API ({r.status_code}): {r.text}")

            r.raise_for_status()
            resposta = r.json()

            registros = resposta.get("data", [])
            if not registros:
                break

            dados.extend(registros)

            pagination = resposta.get("pagination", {})
            total_paginas = pagination.get("total_pages", pagina)

            if pagina >= total_paginas:
                break

            pagina += 1
            sleep(0.05)

        df = pd.DataFrame(dados)

        if column_data and not df.empty:
            for column in column_data:
                if column not in df.columns:
                    continue
                original = df[column].copy()
                convertido = pd.to_datetime(original, format="%d/%m/%Y", errors="coerce")

                nulos = convertido.isna()
                if nulos.any():
                    convertido.loc[nulos] = pd.to_datetime(original.loc[nulos], format="%d/%m/%Y %H:%M:%S", errors="coerce")

                nulos = convertido.isna()
                if nulos.any():
                    convertido.loc[nulos] = pd.to_datetime(original.loc[nulos], errors="coerce")

                df[column] = convertido

        if column_int and not df.empty:
            for column in column_int:
                if column not in df.columns:
                    continue
                df[column] = pd.to_numeric(df[column], errors="coerce").astype("Int64")

        if column_str and not df.empty:
            for column in column_str:
                if column not in df.columns:
                    continue
                df[column] = df[column].astype("string")

        if exclude_empty and not df.empty:
            for column in exclude_empty:
                if column in df.columns:
                    df = df[df[column].notna() & (df[column].astype(str).str.strip() != '')]

        print(f'\033[92m{nomeBase} concluído em {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}\033[0m')
        return df
