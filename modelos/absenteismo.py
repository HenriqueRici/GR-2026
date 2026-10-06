import pandas as pd
import json


def absenteismoWebPonto(basePessoal, baseWebPonto):
    if baseWebPonto.empty:
        return pd.DataFrame(columns=['Func', 'Vinc', 'DataInicial', 'DataFinal', 'Tipo'])

    baseWebPontoFrequencia = baseWebPonto[
        baseWebPonto['MF'].isin([
            '01 - ATESTADO DE COMPARECIMENTO CONSULTA OU AFASTAMENTO MÉDICO ATÉ 03 DIAS',
            '14 - DOAÇÃO DE SANGUE'
        ])
    ][['LOGIN', 'DataFrequencia', 'MF']].copy()

    cols_horarios = ['EntradaManha', 'SaidaManha', 'EntradaTarde', 'SaidaTarde', 'EntradaNoite', 'SaidaNoite']
    for col in cols_horarios:
        if col in baseWebPonto.columns:
            baseWebPonto[col] = pd.to_datetime(baseWebPonto[col], format='%H:%M:%S', errors='coerce')

    baseWebPonto['HorasManha'] = (baseWebPonto['SaidaManha'] - baseWebPonto['EntradaManha']).dt.total_seconds() / 3600.0
    baseWebPonto['HorasTarde'] = (baseWebPonto['SaidaTarde'] - baseWebPonto['EntradaTarde']).dt.total_seconds() / 3600.0
    baseWebPonto['HorasNoite'] = (baseWebPonto['SaidaNoite'] - baseWebPonto['EntradaNoite']).dt.total_seconds() / 3600.0

    baseWebPonto['TotalHorasDia'] = baseWebPonto[['HorasManha', 'HorasTarde', 'HorasNoite']].sum(axis=1, skipna=True)
    baseWebPontoHoras = baseWebPonto.groupby(['LOGIN', 'DataFrequencia'], as_index=False)['TotalHorasDia'].sum()

    baseWebPonto = pd.merge(baseWebPontoFrequencia, baseWebPontoHoras, on=['LOGIN', 'DataFrequencia'], how='left')
    baseWebPonto = baseWebPonto[baseWebPonto['TotalHorasDia'] == 0].rename(
        columns={'LOGIN': 'CPF', 'MF': 'TIPO'}
    )[['CPF', 'DataFrequencia', 'TIPO']]

    baseWebPonto = pd.merge(baseWebPonto, basePessoal, on=['CPF'], how='left')
    baseWebPonto = baseWebPonto[
        (baseWebPonto['DataFrequencia'] >= baseWebPonto['DataInicio']) &
        (baseWebPonto['DataFrequencia'] <= baseWebPonto['DataFinal'])
    ].copy()

    baseWebPonto = baseWebPonto[['NumFunc', 'NumVinc', 'DataFrequencia', 'TIPO']].rename(
        columns={'NumFunc': 'Func', 'NumVinc': 'Vinc', 'DataFrequencia': 'DataInicial', 'TIPO': 'Tipo'}
    )
    baseWebPonto['DataFinal'] = baseWebPonto['DataInicial']

    return baseWebPonto


def absenteismoLicencasAfastamentos(baseLicencasAfastamentos, dataInicioGR, dataFimGR):
    if baseLicencasAfastamentos.empty:
        return pd.DataFrame(columns=['Func', 'Vinc', 'DataInicial', 'DataFinal', 'Tipo'])

    baseLicencasAfastamentos = baseLicencasAfastamentos.copy()
    baseLicencasAfastamentos.loc[baseLicencasAfastamentos['DataFinal'] == pd.Timestamp('1753-01-01'), 'DataFinal'] = dataFimGR

    baseLicencasAfastamentos = baseLicencasAfastamentos[baseLicencasAfastamentos['DataFinal'] >= dataInicioGR].copy()
    baseLicencasAfastamentos['DataInicial'] = baseLicencasAfastamentos['DataInicial'].clip(lower=dataInicioGR)
    baseLicencasAfastamentos['DataFinal'] = baseLicencasAfastamentos['DataFinal'].clip(upper=dataFimGR)

    baseLicencasAfastamentos['DiasAfastamentoGR'] = (baseLicencasAfastamentos['DataFinal'] - baseLicencasAfastamentos['DataInicial']).dt.days + 1
    baseLicencasAfastamentos = baseLicencasAfastamentos[baseLicencasAfastamentos['DiasAfastamentoGR'] > 0]

    return baseLicencasAfastamentos[['Func', 'Vinc', 'DataInicial', 'DataFinal', 'Tipo']]


def absenteismoFrequencias(baseWebPonto, baseFrequencias):
    if baseWebPonto.empty or baseFrequencias.empty:
        return pd.DataFrame(columns=['Func', 'Vinc', 'DataInicial', 'DataFinal', 'Tipo'])

    cols_horarios = ['EntradaManha', 'SaidaManha', 'EntradaTarde', 'SaidaTarde', 'EntradaNoite', 'SaidaNoite']
    for col in cols_horarios:
        if col in baseWebPonto.columns:
            baseWebPonto[col] = pd.to_datetime(baseWebPonto[col], format='%H:%M:%S', errors='coerce')

    baseWebPonto['HorasManha'] = (baseWebPonto['SaidaManha'] - baseWebPonto['EntradaManha']).dt.total_seconds() / 3600.0
    baseWebPonto['HorasTarde'] = (baseWebPonto['SaidaTarde'] - baseWebPonto['EntradaTarde']).dt.total_seconds() / 3600.0
    baseWebPonto['HorasNoite'] = (baseWebPonto['SaidaNoite'] - baseWebPonto['EntradaNoite']).dt.total_seconds() / 3600.0

    baseWebPonto['TotalHorasDia'] = baseWebPonto[['HorasManha', 'HorasTarde', 'HorasNoite']].sum(axis=1, skipna=True)
    baseWebPontoHoras = baseWebPonto.groupby(['LOGIN', 'DataFrequencia'], as_index=False)['TotalHorasDia'].sum()

    baseWebPonto = pd.merge(baseWebPontoHoras, baseFrequencias, left_on=['LOGIN', 'DataFrequencia'], right_on=['CPF', 'DataInicial'], how='left')

    baseWebPonto = baseWebPonto[(baseWebPonto['TotalHorasDia'] == 0) & (baseWebPonto['Tipo'].notna())].copy()
    return baseWebPonto[['Func', 'Vinc', 'DataInicial', 'DataFinal', 'Tipo']]


def absenteismoGeral(grupoEleitos, absenteismoWebPonto, baseLicencas, baseFrequencia):
    baseAbs = pd.concat([absenteismoWebPonto, baseLicencas, baseFrequencia], ignore_index=True)
    if baseAbs.empty:
        eleitos = grupoEleitos.rename(columns={'NumFunc': 'Func', 'NumVinc': 'Vinc'}).copy()
        eleitos['DiasAbsenteismo'] = 0
        eleitos['ListaAbsenteismo'] = "[]"
        return eleitos

    baseAbs = baseAbs.drop_duplicates(subset=['Func', 'Vinc', 'Tipo', 'DataInicial', 'DataFinal']).copy()
    baseAbs['Tipo'] = baseAbs['Tipo'].str.replace(r'^\d+\s*-\s*', '', regex=True)

    def manter_licencas_validas(df):
        resultado = []
        for _, group in df.groupby(['Func', 'Vinc']):
            licencas_tipo_01 = group[group['Tipo'].isin([
                'ATESTADO DE COMPARECIMENTO CONSULTA OU AFASTAMENTO MÉDICO ATÉ 03 DIAS', 'DOAÇÃO DE SANGUE'
            ])]
            licencas_outras = group[~group['Tipo'].isin([
                'ATESTADO DE COMPARECIMENTO CONSULTA OU AFASTAMENTO MÉDICO ATÉ 03 DIAS', 'DOAÇÃO DE SANGUE'
            ])]

            resultado.extend(licencas_outras.to_dict(orient='records'))

            for _, row in licencas_tipo_01.iterrows():
                if not any((row['DataInicial'] >= l['DataInicial']) and (row['DataFinal'] <= l['DataFinal']) for _, l in licencas_outras.iterrows()):
                    resultado.append(row.to_dict())

        return pd.DataFrame(resultado) if resultado else pd.DataFrame(columns=df.columns)

    baseAbs = manter_licencas_validas(baseAbs)
    eleitos = grupoEleitos.rename(columns={'NumFunc': 'Func', 'NumVinc': 'Vinc'}).copy()

    eleitosParaAbs = eleitos[['Func', 'Vinc', 'DataInicio', 'DataFinal']].rename(
        columns={'DataInicio': 'DataInicioAtribuicao', 'DataFinal': 'DataFinalAtribuicao'}
    )

    baseAbs = pd.merge(baseAbs, eleitosParaAbs, on=['Func', 'Vinc'], how='left')
    baseAbs = baseAbs[
        ((baseAbs['Tipo'] == 'ARC - AGUARDANDO REGULARIZAÇÃO DO CARGO') &
         (baseAbs['DataInicial'] >= baseAbs['DataInicioAtribuicao']) &
         (baseAbs['DataFinal'] <= baseAbs['DataFinalAtribuicao'])) |
        (baseAbs['Tipo'] != 'ARC - AGUARDANDO REGULARIZAÇÃO DO CARGO')
    ]

    baseAbs = baseAbs[['Func', 'Vinc', 'Tipo', 'DataInicial', 'DataFinal']].drop_duplicates(
        subset=['Func', 'Vinc', 'Tipo', 'DataInicial', 'DataFinal']
    )

    def calcular_dias_ausentes(df):
        if df.empty:
            return 0
        df = df.sort_values(by=['DataInicial', 'DataInicial'])
        periodos_consolidados = []
        inicio_periodo = None
        fim_periodo = None

        for _, row in df.iterrows():
            if inicio_periodo is None:
                inicio_periodo = row['DataInicial']
                fim_periodo = row['DataFinal']
            else:
                if row['DataInicial'] <= fim_periodo:
                    fim_periodo = max(fim_periodo, row['DataFinal'])
                else:
                    periodos_consolidados.append((inicio_periodo, fim_periodo))
                    inicio_periodo = row['DataInicial']
                    fim_periodo = row['DataFinal']

        if inicio_periodo is not None:
            periodos_consolidados.append((inicio_periodo, fim_periodo))

        dias_unicos = set()
        for inicio, fim in periodos_consolidados:
            dias_unicos.update(pd.date_range(inicio, fim))

        return len(dias_unicos)

    res_abs_dias = []
    for (f, v), g in baseAbs.groupby(['Func', 'Vinc']):
        dias = calcular_dias_ausentes(g)
        res_abs_dias.append({'Func': f, 'Vinc': v, 'DiasAbsenteismo': dias})

    absenteismoCompilado = pd.DataFrame(res_abs_dias) if res_abs_dias else pd.DataFrame(columns=['Func', 'Vinc', 'DiasAbsenteismo'])

    eleitos = pd.merge(eleitos, absenteismoCompilado, on=['Func', 'Vinc'], how='left')
    eleitos['DiasAbsenteismo'] = eleitos['DiasAbsenteismo'].fillna(0)

    # Dicionário otimizado de lista de absenteísmo por (Func, Vinc)
    abs_map = {}
    for item in baseAbs.to_dict(orient='records'):
        k = (item['Func'], item['Vinc'])
        if k not in abs_map:
            abs_map[k] = []
        abs_map[k].append({
            'Tipo': item['Tipo'],
            'DataInicial': item['DataInicial'].strftime("%Y-%m-%d %H:%M:%S") if isinstance(item['DataInicial'], (pd.Timestamp, pd.DatetimeIndex)) else str(item['DataInicial']),
            'DataFinal': item['DataFinal'].strftime("%Y-%m-%d %H:%M:%S") if isinstance(item['DataFinal'], (pd.Timestamp, pd.DatetimeIndex)) else str(item['DataFinal'])
        })

    def get_json_abs(row):
        k = (row['Func'], row['Vinc'])
        lst = abs_map.get(k, [])
        return json.dumps(lst, ensure_ascii=False)

    eleitos['ListaAbsenteismo'] = eleitos.apply(get_json_abs, axis=1)

    return eleitos


def pontuacaoAbsenteismo(row):
    dias = row.get('DiasAbsenteismo', 0)
    cargo = row.get('CargoGR')

    is_docente_ou_gestor = cargo in ['PROFESSOR EM REGÊNCIA', 'GESTOR', 'PROFESSOR FORA DE REGÊNCIA']

    if is_docente_ou_gestor:
        if dias == 0:
            return 300
        elif 1 <= dias <= 20:
            # Tabela decrescente de 30 em 30 a cada 2 dias
            p = 300 - ((dias + 1) // 2) * 30
            return p
        elif 21 <= dias <= 30:
            p = -30 - ((dias - 21) // 2) * 30
            return p
        else:
            return -150
    else:
        if dias == 0:
            return 450
        elif 1 <= dias <= 20:
            p = 450 - ((dias + 1) // 2) * 45
            return p
        elif 21 <= dias <= 30:
            p = -30 - ((dias - 21) // 2) * 30
            return p
        else:
            return -150


def maxAbsenteismo(row):
    if row.get('CargoGR') in ['PROFESSOR EM REGÊNCIA', 'GESTOR', 'PROFESSOR FORA DE REGÊNCIA']:
        return 300
    else:
        return 450
