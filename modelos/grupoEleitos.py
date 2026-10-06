import pandas as pd
import numpy as np


def trataAtribuicao(baseAtribuicao, baseHoraAtividade, baseVacancia, dataInicioGR, dataFimGR):
    baseAtribuicao = baseAtribuicao.copy()
    baseAtribuicao['E_GESTOR'] = baseAtribuicao['Funcao'].isin([
        'PROFESSOR/DRE', 'COORDENADOR PEDAGÓGICO', 'COORDENADOR PEDAGÓGICO - SALA ANEXA',
        'COORDENADOR PEDAGÓGICO - 2º VÍNCULO', 'DIRETOR', 'DIRETOR - 2º VÍNCULO'
    ])

    duplicados = (
        baseAtribuicao.groupby(['NumFunc', 'NumVinc', 'DataInicio', 'DataFinal'])
        .filter(lambda g: any(g['E_GESTOR']) and any(g['Funcao'] == 'PROFESSOR'))
    )

    if not duplicados.empty:
        duplicados_tuples = set(duplicados[['NumFunc', 'NumVinc', 'DataInicio', 'DataFinal']].itertuples(index=False, name=None))
        cond_remover = (
            (baseAtribuicao['Funcao'] == 'PROFESSOR') &
            baseAtribuicao[['NumFunc', 'NumVinc', 'DataInicio', 'DataFinal']].apply(tuple, axis=1).isin(duplicados_tuples)
        )
        baseAtribuicao = baseAtribuicao[~cond_remover].copy()

    str_cols = baseAtribuicao.select_dtypes(include='object').columns
    for c in str_cols:
        baseAtribuicao[c] = baseAtribuicao[c].str.strip()

    baseAtribuicao.loc[baseAtribuicao['DataFinal'] == pd.Timestamp('1753-01-01'), 'DataFinal'] = dataFimGR

    baseHoraAtividade = baseHoraAtividade.drop_duplicates(subset=['Func', 'Vinc'])[['Func', 'Vinc', 'Tipo']].rename(
        columns={'Func': 'NumFunc', 'Vinc': 'NumVinc', 'Tipo': 'HoraAtividade'}
    )

    baseAtribuicao['TotalCH'] = pd.to_numeric(baseAtribuicao['TotalCH'], errors='coerce').astype('Int64')
    baseAtribuicao['AdmCH'] = pd.to_numeric(baseAtribuicao['AdmCH'], errors='coerce').astype('Int64')
    baseAtribuicao['AtividadeSeap'] = pd.to_numeric(baseAtribuicao['AtividadeSeap'], errors='coerce').astype('Int64')

    baseAtribuicao = pd.merge(baseAtribuicao, baseHoraAtividade, on=['NumFunc', 'NumVinc'], how='left')

    baseAtribuicao['CH'] = np.where(
        baseAtribuicao['HoraAtividade'] == '2002 - HORA ATIVIDADE',
        (baseAtribuicao['TotalCH'] + baseAtribuicao['AdmCH']) * 1.5,
        (baseAtribuicao['TotalCH'] + baseAtribuicao['AdmCH'])
    )

    baseAtribuicao.loc[baseAtribuicao['TipoVinculo'] == 'EFETIVO', 'AtividadeSeap'] = 60
    baseAtribuicao['CH'] = (baseAtribuicao['CH']) / 60.0 * baseAtribuicao['AtividadeSeap']

    m_20 = baseAtribuicao['CargoCarreira'] == 'PROFESSOR EDUC. BASICA/20 HORAS'
    m_30 = baseAtribuicao['CargoCarreira'].isin(['PROFESSOR EDUC. BASICA/30 HORAS', 'PROF. 30 HORAS ANEXO VI LC50/98'])
    m_40 = baseAtribuicao['CargoCarreira'] == 'PROFESSOR EDUC. BASICA/40 HORAS'

    baseAtribuicao.loc[m_20, 'CH'] = 20
    baseAtribuicao.loc[m_30, 'CH'] = 30
    baseAtribuicao.loc[m_40, 'CH'] = 40

    baseAtribuicao = baseAtribuicao[baseAtribuicao['CargoCarreira'] != 'PERMUTADOS'].copy()
    baseAtribuicao = baseAtribuicao[baseAtribuicao['DataFinal'] >= dataInicioGR].copy()

    baseAtribuicao['DataInicio'] = baseAtribuicao['DataInicio'].clip(lower=dataInicioGR)
    baseAtribuicao['DataFinal'] = baseAtribuicao['DataFinal'].clip(upper=dataFimGR)

    vacancia = trataVacancia(baseVacancia, dataInicioGR, dataFimGR)
    baseAtribuicao = pd.merge(baseAtribuicao, vacancia, on=['NumFunc', 'NumVinc'], how='left')

    baseAtribuicao['DiasVinculo'] = (baseAtribuicao['DataFinal'] - baseAtribuicao['DataInicio']).dt.days + 1

    for tipo_vinc, col_dias in [('EFETIVO', 'DiasVinculoEfetivo'), ('TEMPORÁRIO', 'DiasVinculoContrato')]:
        sub_vinc = baseAtribuicao[baseAtribuicao['TipoVinculo'] == tipo_vinc]
        if not sub_vinc.empty:
            agg_vinc = sub_vinc.groupby(['NumFunc', 'NumVinc'], as_index=False).agg(
                DataInicio=('DataInicio', 'min'), DataFinal=('DataFinal', 'max')
            )
            agg_vinc[col_dias] = (agg_vinc['DataFinal'] - agg_vinc['DataInicio']).dt.days + 1
            agg_vinc = agg_vinc[agg_vinc[col_dias] >= 15][['NumFunc', 'NumVinc', col_dias]]
            baseAtribuicao = pd.merge(baseAtribuicao, agg_vinc, on=['NumFunc', 'NumVinc'], how='left')
        else:
            baseAtribuicao[col_dias] = np.nan

    filtro = (
        ((baseAtribuicao['TipoVinculo'] == 'EFETIVO') & (baseAtribuicao['DiasVinculoEfetivo'].notnull())) |
        ((baseAtribuicao['TipoVinculo'] == 'TEMPORÁRIO') & (baseAtribuicao['DiasVinculoContrato'].notnull()))
    )

    baseAtribuicao = baseAtribuicao[filtro]
    baseAtribuicao = baseAtribuicao[baseAtribuicao['DiasVinculo'] > 0].copy()

    baseAtribuicao = ajustar_periodos(baseAtribuicao, vacancia)
    baseAtribuicao = baseAtribuicao.drop_duplicates(subset=['NumFunc', 'NumVinc', 'DataInicio', 'DataFinal'])

    cols_select = [
        'DRE', 'Municipio', 'SerieLotacao', 'Lotacao', 'TipoLotacao', 'Nome', 'CPF',
        'CodFunc', 'Funcao', 'TipoProcesso', 'Processo', 'TipoServidor', 'TipoVinculo',
        'NumFunc', 'NumVinc', 'CargoCarreira', 'CH', 'DataInicio', 'DataFinal'
    ]
    baseAtribuicao = baseAtribuicao[[c for c in cols_select if c in baseAtribuicao.columns]]
    baseAtribuicao['DiasVinculo'] = (baseAtribuicao['DataFinal'] - baseAtribuicao['DataInicio']).dt.days + 1

    vinc15Dias = (
        baseAtribuicao.groupby(['NumFunc', 'NumVinc'])
        .apply(dias_unicos)
        .rename('DiasVinculoManter')
        .reset_index()
    )
    vinc15Dias = vinc15Dias[vinc15Dias['DiasVinculoManter'] >= 15].copy()
    vinc15Dias['MANTER'] = 'SIM'

    baseAtribuicao = pd.merge(baseAtribuicao, vinc15Dias, how='left', on=['NumFunc', 'NumVinc'])
    baseAtribuicao = baseAtribuicao[baseAtribuicao['MANTER'] == 'SIM']
    baseAtribuicao = baseAtribuicao[baseAtribuicao['CargoCarreira'] != 'MEMBRO DE CONSELHO']

    return baseAtribuicao


def dias_unicos(grupo):
    periodos = (
        grupo[['DataInicio', 'DataFinal']]
        .dropna()
        .sort_values('DataInicio')
        .itertuples(index=False, name=None)
    )

    total = 0
    inicio_atual = None
    fim_atual = None

    for inicio, fim in periodos:
        if inicio_atual is None:
            inicio_atual = inicio
            fim_atual = fim
        elif inicio <= fim_atual + pd.Timedelta(days=1):
            fim_atual = max(fim_atual, fim)
        else:
            total += (fim_atual - inicio_atual).days + 1
            inicio_atual = inicio
            fim_atual = fim

    if inicio_atual is not None:
        total += (fim_atual - inicio_atual).days + 1

    return total


def ajustar_periodos(df_periodos, df_vacancias):
    if df_vacancias.empty:
        return df_periodos.copy()

    linhas = []
    for _, row in df_periodos.iterrows():
        numfunc = row['NumFunc']
        numvinc = row['NumVinc']
        inicio = row['DataInicio']
        fim = row['DataFinal']

        vacs = df_vacancias[
            (df_vacancias['NumFunc'] == numfunc) &
            (df_vacancias['NumVinc'] == numvinc) &
            (df_vacancias['DataInicioVacancia'] <= fim) &
            (df_vacancias['DataFinalVacancia'] >= inicio)
        ].sort_values('DataInicioVacancia')

        if vacs.empty:
            linhas.append(row.copy())
            continue

        atual_inicio = inicio
        for _, v in vacs.iterrows():
            v_ini = v['DataInicioVacancia']
            v_fim = v['DataFinalVacancia']

            if v_ini <= inicio and v_fim >= fim:
                atual_inicio = None
                break

            if v_ini > atual_inicio:
                novo_fim = min(v_ini - pd.Timedelta(days=1), fim)
                if novo_fim >= atual_inicio:
                    nova_linha = row.copy()
                    nova_linha['DataInicio'] = atual_inicio
                    nova_linha['DataFinal'] = novo_fim
                    linhas.append(nova_linha)

            if v_fim + pd.Timedelta(days=1) <= fim:
                atual_inicio = v_fim + pd.Timedelta(days=1)
            else:
                atual_inicio = None
                break

        if atual_inicio is not None and atual_inicio <= fim:
            nova_linha = row.copy()
            nova_linha['DataInicio'] = atual_inicio
            nova_linha['DataFinal'] = fim
            linhas.append(nova_linha)

    return pd.DataFrame(linhas).reset_index(drop=True)


def trataVacancia(baseVacancia, dataInicioGR, dataFimGR):
    if baseVacancia.empty:
        return pd.DataFrame(columns=['NumFunc', 'NumVinc', 'Tipo', 'DataInicioVacancia', 'DataFinalVacancia', 'DiasVacancia'])

    vacancia = baseVacancia.copy()
    vacancia.loc[vacancia['DataFinal'] == pd.Timestamp('1753-01-01'), 'DataFinal'] = dataFimGR
    vacancia = vacancia[vacancia['DataFinal'] >= dataInicioGR].copy()

    vacancia['DataInicial'] = vacancia['DataInicial'].clip(lower=dataInicioGR)
    vacancia['DataFinal'] = vacancia['DataFinal'].clip(upper=dataFimGR)

    resultado = vacancia.rename(
        columns={'Func': 'NumFunc', 'Vinc': 'NumVinc', 'DataInicial': 'DataInicioVacancia', 'DataFinal': 'DataFinalVacancia'}
    )[['NumFunc', 'NumVinc', 'DataInicioVacancia', 'DataFinalVacancia', 'Tipo']]

    def unir_periodos(grupo):
        grupo = grupo.sort_values('DataInicioVacancia').reset_index(drop=True)
        grupos_unidos = []
        inicio = grupo.loc[0, 'DataInicioVacancia']
        fim = grupo.loc[0, 'DataFinalVacancia']

        for _, linha in grupo.iloc[1:].iterrows():
            if (linha['DataInicioVacancia'] - fim).days <= 1:
                fim = max(fim, linha['DataFinalVacancia'])
            else:
                grupos_unidos.append([inicio, fim])
                inicio = linha['DataInicioVacancia']
                fim = linha['DataFinalVacancia']

        grupos_unidos.append([inicio, fim])
        return pd.DataFrame(grupos_unidos, columns=['DataInicioVacancia', 'DataFinalVacancia'])

    res_list = []
    for (numfunc, numvinc, tipo), g in resultado.groupby(['NumFunc', 'NumVinc', 'Tipo']):
        unidos = unir_periodos(g)
        unidos['NumFunc'] = numfunc
        unidos['NumVinc'] = numvinc
        unidos['Tipo'] = tipo
        res_list.append(unidos)

    if res_list:
        resultado = pd.concat(res_list, ignore_index=True)
    else:
        resultado = pd.DataFrame(columns=['NumFunc', 'NumVinc', 'Tipo', 'DataInicioVacancia', 'DataFinalVacancia'])

    resultado['DiasVacancia'] = (resultado['DataFinalVacancia'] - resultado['DataInicioVacancia']).dt.days + 1
    return resultado


def tetoGr(baseAtribuicao):
    if baseAtribuicao.empty:
        return pd.DataFrame(columns=['CPF', 'PercentualGRServidor'])

    contratos_cpf = {}
    for _, row in baseAtribuicao.iterrows():
        cpf = str(row["CPF"])
        if cpf not in contratos_cpf:
            contratos_cpf[cpf] = []
        contratos_cpf[cpf].append((row["DataInicio"], row["DataFinal"], row["CH"]))

    resultados_cpf = []

    for cpf, contratos in contratos_cpf.items():
        datas_unicas = sorted(set([ini for ini, _, _ in contratos] + [fim + pd.Timedelta(days=1) for _, fim, _ in contratos]))
        periodos = [(datas_unicas[i], datas_unicas[i+1] - pd.Timedelta(days=1)) for i in range(len(datas_unicas)-1)]

        for inicio, fim in periodos:
            carga_total = sum(ch for ini, f, ch in contratos if ini <= inicio and f >= fim)
            resultados_cpf.append((cpf, inicio, fim, carga_total))

    df_resultado = pd.DataFrame(resultados_cpf, columns=["CPF", "DataInicio", "DataFinal", "CH"])
    df_resultado['Dias'] = (df_resultado['DataFinal'] - df_resultado['DataInicio']).dt.days + 1
    df_resultado["CH"] = df_resultado["CH"].clip(upper=30)
    df_resultado['Percentual'] = (df_resultado['Dias'] / 302.0) * (df_resultado['CH'] / 30.0)

    df_resultado = df_resultado.groupby(['CPF'], as_index=False)['Percentual'].sum().rename(
        columns={'Percentual': 'PercentualGRServidor'}
    )
    df_resultado['CPF'] = df_resultado['CPF'].astype(float)
    return df_resultado


def proporcaoVinculo(grupo):
    grupo = grupo.copy()
    grupo['Peso'] = grupo['DiasVinculo'] * grupo['CH']
    somaPeso = grupo.groupby(['NumFunc'], as_index=False)['Peso'].sum().rename(columns={'Peso': 'PesoTotal'})

    grupo = pd.merge(grupo, somaPeso, how='left', on='NumFunc')
    mask = grupo['PesoTotal'] > 0
    grupo['PercentualGRVinculo'] = 0.0
    grupo.loc[mask, 'PercentualGRVinculo'] = (grupo.loc[mask, 'Peso'] / grupo.loc[mask, 'PesoTotal']) * grupo.loc[mask, 'PercentualGRServidor']

    cols_sel = [
        'DRE', 'Municipio', 'SerieLotacao', 'Lotacao', 'TipoLotacao', 'Nome', 'CPF',
        'TipoVinculo', 'DataInicio', 'DataFinal', 'NumFunc', 'NumVinc', 'CargoCarreira',
        'CH', 'DiasVinculo', 'CargoGR', 'PercentualGRVinculo'
    ]
    grupo = grupo[[c for c in cols_sel if c in grupo.columns]]

    grupo['LotacaoGR'] = np.select(
        [grupo['TipoLotacao'] == 'ÓRGÃO CENTRAL', grupo['TipoLotacao'] == 'DRE'],
        ['ÓRGÃO CENTRAL', grupo['DRE']],
        default=grupo['SerieLotacao'].astype(str)
    )

    replacements = {
        'DRE TANGARA DA SERRA': 'DRE TANGARÁ DA SERRA',
        'DRE JUINA': 'DRE JUÍNA',
        'DRE CACERES': 'DRE CÁCERES',
        'DRE BARRA DO GARCAS': 'DRE BARRA DO GARÇAS'
    }
    grupo['LotacaoGR'] = grupo['LotacaoGR'].replace(replacements)

    grupo['DescricaoLotacaoGR'] = np.select(
        [grupo['TipoLotacao'] == 'ÓRGÃO CENTRAL', grupo['TipoLotacao'] == 'DRE', grupo['TipoLotacao'].isin(['EDUCAÇÃO ESPECIAL', 'ESCOLA INDÍGENA'])],
        ['ÓRGÃO CENTRAL', grupo['DRE'], grupo['DRE']],
        default=grupo['Lotacao'].astype(str)
    )

    cols_group = [
        'LotacaoGR', 'DescricaoLotacaoGR', 'Nome', 'CPF', 'NumFunc', 'NumVinc',
        'TipoVinculo', 'CargoCarreira', 'CargoGR', 'DataInicio', 'DataFinal', 'CH'
    ]

    return grupo.groupby(cols_group, as_index=False)['PercentualGRVinculo'].sum()


def calcular_periodo_unico(df, col_data_ini=None, col_data_fim=None):
    if df.empty:
        return 0

    grupo = df.sort_values(by=col_data_ini).reset_index(drop=True)
    intervalos = []

    for _, linha in grupo.iterrows():
        ini, fim = linha[col_data_ini], linha[col_data_fim]
        if pd.isna(ini) or pd.isna(fim):
            continue

        if not intervalos:
            intervalos.append([ini, fim])
        else:
            ult_ini, ult_fim = intervalos[-1]
            if ini <= ult_fim:
                intervalos[-1][1] = max(ult_fim, fim)
            else:
                intervalos.append([ini, fim])

    return sum((fim - ini).days + 1 for ini, fim in intervalos)


def definirCargoGR(baseAtribuicao, aula, baseDE, baseSEAP, dataInicioGR, dataFimGR):
    baseAtribuicao = baseAtribuicao.copy()
    baseDE = baseDE.copy()
    baseSEAP = baseSEAP.copy()
    aula = aula.copy()

    baseDE.loc[baseDE['DataFinal'] == pd.Timestamp('1753-01-01'), 'DataFinal'] = dataFimGR
    baseDE['DataInicial'] = baseDE['DataInicial'].clip(lower=dataInicioGR)
    baseDE['DataFinal'] = baseDE['DataFinal'].clip(upper=dataFimGR)
    baseDE = baseDE[baseDE['DataFinal'] >= dataInicioGR].copy()

    res_de_list = []
    for func, g in baseDE.groupby('Func'):
        dias = calcular_periodo_unico(g, col_data_ini='DataInicial', col_data_fim='DataFinal')
        res_de_list.append({'Func': func, 'DiasGestao': dias})
    resultadoDE = pd.DataFrame(res_de_list) if res_de_list else pd.DataFrame(columns=['Func', 'DiasGestao'])

    baseSEAP = baseSEAP[baseSEAP['descr_cargo'].str.contains('DGA', na=False)].copy()
    baseSEAP.loc[baseSEAP['dtfim'].isna(), 'dtfim'] = dataFimGR
    baseSEAP['dtini'] = baseSEAP['dtini'].clip(lower=dataInicioGR)
    baseSEAP['dtfim'] = baseSEAP['dtfim'].clip(upper=dataFimGR)
    baseSEAP = baseSEAP[baseSEAP['dtfim'] >= dataInicioGR].copy()

    res_seap_list = []
    for numfunc, g in baseSEAP.groupby('numfunc'):
        dias = calcular_periodo_unico(g, col_data_ini='dtini', col_data_fim='dtfim')
        res_seap_list.append({'Func': numfunc, 'DiasGestao': dias})
    resultadoSEAP = pd.DataFrame(res_seap_list) if res_seap_list else pd.DataFrame(columns=['Func', 'DiasGestao'])

    gestaoContrato = baseAtribuicao[baseAtribuicao['Funcao'].isin(['COORDENADOR/DESIGNADO', 'DIRETOR DESIGNADO/PROFESSOR', 'SECRETÁRIO/DESIGNADO'])].copy()
    res_gc_list = []
    for numfunc, g in gestaoContrato.groupby('NumFunc'):
        dias = calcular_periodo_unico(g, col_data_ini='DataInicio', col_data_fim='DataFinal')
        res_gc_list.append({'Func': numfunc, 'DiasGestao': dias})
    gestaoContratoRes = pd.DataFrame(res_gc_list) if res_gc_list else pd.DataFrame(columns=['Func', 'DiasGestao'])

    resultadoGestao = pd.concat([resultadoDE, resultadoSEAP, gestaoContratoRes], ignore_index=True)
    if not resultadoGestao.empty:
        resultadoGestao = resultadoGestao.groupby('Func', as_index=False)['DiasGestao'].sum()
        resultadoGestao = resultadoGestao[resultadoGestao['DiasGestao'] >= 180]

    baseAtribuicao = pd.merge(baseAtribuicao, resultadoGestao, how='left', left_on='NumFunc', right_on='Func')

    substituicoes = {
        'DGA-1': 'CIVIS E MILITARES LOTADOS NA SEDUC', 'DGA-2': 'CIVIS E MILITARES LOTADOS NA SEDUC',
        'DGA-3': 'CIVIS E MILITARES LOTADOS NA SEDUC', 'DGA-4': 'CIVIS E MILITARES LOTADOS NA SEDUC',
        'DGA-5': 'CIVIS E MILITARES LOTADOS NA SEDUC', 'DGA-6': 'CIVIS E MILITARES LOTADOS NA SEDUC',
        'PRESIDENTE CONSELHO ESTADUAL DE EDUCAÇÃO': 'GESTOR',
        '15019 - APOIO TECNICO ESP CIVICO MILITAR 01': 'CIVIS E MILITARES LOTADOS NA SEDUC',
        '15020 - APOIO TECNICO ESP CIVICO MILITAR 02': 'CIVIS E MILITARES LOTADOS NA SEDUC',
        '15021 - INSPETOR TECNICO CIVICO MILITAR': 'CIVIS E MILITARES LOTADOS NA SEDUC',
        'AGENTE UNIVERSITARIO LC 321/2008 - UNEMAT': 'CIVIS E MILITARES LOTADOS NA SEDUC',
        'AGES - AGENTE DESENVOLV. ECON. E SOCIAL': 'CIVIS E MILITARES LOTADOS NA SEDUC',
        'ANALISTA ADMINISTRATIVO': 'CIVIS E MILITARES LOTADOS NA SEDUC',
        'ANALISTA DE DESENVOLVIMENTO ECONÔMICO E SOCIAL': 'CIVIS E MILITARES LOTADOS NA SEDUC',
        'APOIO TÉCNICO ESP CÍVICO MILITAR 01': 'CIVIS E MILITARES LOTADOS NA SEDUC',
        'APOIO TÉCNICO ESP CÍVICO MILITAR 02': 'CIVIS E MILITARES LOTADOS NA SEDUC',
        'FUNCAO DGA 5 LC/266': 'CIVIS E MILITARES LOTADOS NA SEDUC',
        'GESTOR GOVERNAMENTAL': 'CIVIS E MILITARES LOTADOS NA SEDUC',
        'PROC. DO ESTADO EM ESTAGIO PROBAT': 'CIVIS E MILITARES LOTADOS NA SEDUC',
        'INSPETOR CIVICO MILITAR - NÍVEL SUPORTE E APOIO': 'CIVIS E MILITARES LOTADOS NA SEDUC',
        'MEMBRO DE CONSELHO': 'CIVIS E MILITARES LOTADOS NA SEDUC',
        'PERMUTADOS': 'CIVIS E MILITARES LOTADOS NA SEDUC',
        'PROFESSOR UNEMAT LC 534/2014': 'CIVIS E MILITARES LOTADOS NA SEDUC',
        'TEC. DESENVOL. ECON. SOCIAL  40 HRS': 'CIVIS E MILITARES LOTADOS NA SEDUC',
        'TECNICO AREA INSTR. - 40H': 'CIVIS E MILITARES LOTADOS NA SEDUC',
        'TÉCNICO ADMINISTRATIVO L 10052': 'CIVIS E MILITARES LOTADOS NA SEDUC',
        'TÉCNICO DESENV.ECO.SOC L 10177/14': 'CIVIS E MILITARES LOTADOS NA SEDUC',
        'ANALISTA FUNDIARIO E AGRARIO L 10042': 'CIVIS E MILITARES LOTADOS NA SEDUC',
        'ANALISTA DE TECNOLOGIA DA INFORMACAO JUNIOR': 'CIVIS E MILITARES LOTADOS NA SEDUC',
        'ASSESSOR JURIDICO(A)': 'CIVIS E MILITARES LOTADOS NA SEDUC',
        'CONTR.TEMP.FUNCAO PROF. HABILITADO': 'PROFESSOR',
        'CONTR.TEMP.FUNCAO PROF. NAO HABILIT': 'PROFESSOR',
        'ESPECIALISTA': 'PROFESSOR',
        'PROF. 30 HORAS ANEXO VI LC50/98': 'PROFESSOR',
        'PROFESSOR EDUC. BASICA/20 HORAS': 'PROFESSOR',
        'PROFESSOR EDUC. BASICA/30 HORAS': 'PROFESSOR',
        'PROFESSOR EDUC. BASICA/40 HORAS': 'PROFESSOR',
        'APOIO ADM. EDUCACIONAL-ELEMENTAR': 'TAE/AAE',
        'APOIO ADMIN PROFISSIONALIZADO': 'TAE/AAE',
        'AUXILIAR DE ADMINISTRAÇÃO': 'TAE/AAE',
        'AUXILIAR DE SERVIÇOS GERAIS I': 'TAE/AAE',
        'PORTEIRO': 'TAE/AAE',
        'VIGIA': 'TAE/AAE',
        'TECNICO ADMIN PROFISSIONALIZADO': 'TAE/AAE',
        'TECNICO ADMINISTRATIVO EDUCACIONAL': 'TAE/AAE',
        'AGENTE ADMINISTRAÇÃO': 'TAE/AAE',
        'OFICIAL DE GESTAO CIVICO-MILITAR': 'CIVIS E MILITARES LOTADOS NA SEDUC',
        'OFICIAL DE GESTAO EDUCACIONAL MILITAR': 'CIVIS E MILITARES LOTADOS NA SEDUC',
        'MOTORISTA': 'CIVIS E MILITARES LOTADOS NA SEDUC',
        'ANALISTA DE TECNOLOGIA DA INFORMAÇÃO SENIOR - INTERINO': 'CIVIS E MILITARES LOTADOS NA SEDUC',
        'MONITOR': 'CIVIS E MILITARES LOTADOS NA SEDUC',
        'TENENTE CORONEL LC 541/2014': 'CIVIS E MILITARES LOTADOS NA SEDUC',
    }

    baseAtribuicao['CargoGR'] = np.where(
        baseAtribuicao['DiasGestao'].notna(),
        'GESTOR',
        baseAtribuicao['CargoCarreira'].map(substituicoes)
    )

    professorEmAula = baseAtribuicao[baseAtribuicao['CargoGR'] == 'PROFESSOR'].copy()

    aula = aula[aula['DataFinal'] >= dataInicioGR].copy()
    aula['DataInicial'] = aula['DataInicial'].clip(lower=dataInicioGR)
    aula['DataFinal'] = aula['DataFinal'].clip(upper=dataFimGR)

    emAula = aula.drop_duplicates(subset=['CodigoSEAP', 'VinculoSEAP', 'DataInicial', 'DataFinal'])[
        ['CodigoSEAP', 'VinculoSEAP', 'DataInicial', 'DataFinal']
    ].rename(columns={'DataInicial': 'DataInicialAula', 'DataFinal': 'DataFinalAula'})

    professorEmAula = pd.merge(professorEmAula, emAula, how='left', left_on=['NumFunc', 'NumVinc'], right_on=['CodigoSEAP', 'VinculoSEAP'])
    professorEmAula.loc[
        (professorEmAula['DataInicialAula'] <= professorEmAula['DataInicio']) &
        (professorEmAula['DataFinalAula'] >= professorEmAula['DataFinal']),
        'Em Sala'
    ] = 'SIM'

    professorEmAula = professorEmAula[['NumFunc', 'NumVinc', 'DataInicio', 'DataFinal', 'Em Sala']].drop_duplicates(
        subset=['NumFunc', 'NumVinc', 'DataInicio', 'DataFinal']
    )

    baseAtribuicao = pd.merge(baseAtribuicao, professorEmAula, how='left', on=['NumFunc', 'NumVinc', 'DataInicio', 'DataFinal'])

    baseAtribuicao.loc[(baseAtribuicao['CargoGR'] == 'PROFESSOR') & (baseAtribuicao['Em Sala'] == 'SIM'), 'CargoGR'] = 'PROFESSOR EM REGÊNCIA'
    baseAtribuicao.loc[(baseAtribuicao['CargoGR'] == 'PROFESSOR') & (baseAtribuicao['Em Sala'].isna()), 'CargoGR'] = 'PROFESSOR FORA DE REGÊNCIA'

    cols_final = [
        'DRE', 'Municipio', 'SerieLotacao', 'Lotacao', 'TipoLotacao', 'Nome', 'CPF',
        'TipoVinculo', 'DataInicio', 'DataFinal', 'NumFunc', 'NumVinc', 'CargoCarreira', 'CH', 'DiasVinculo', 'CargoGR'
    ]
    baseAtribuicao = baseAtribuicao[[c for c in cols_final if c in baseAtribuicao.columns]]
    baseAtribuicao["CH"] = baseAtribuicao["CH"].clip(upper=30)
    baseAtribuicao['CPF'] = baseAtribuicao['CPF'].astype(float)

    return baseAtribuicao


def valorGRBase(row):
    cargo_gr = row.get('CargoGR')
    percentual = row.get('PercentualGRVinculo', 0)
    cargo_carreira = row.get('CargoCarreira')

    FATOR = 1.054

    if cargo_gr in ['PROFESSOR EM REGÊNCIA', 'GESTOR', 'PROFESSOR FORA DE REGÊNCIA']:
        return 11015.44 * percentual * FATOR
    elif cargo_gr == 'TAE/AAE':
        return 5507.72 * percentual * FATOR
    elif cargo_gr == 'CIVIS E MILITARES LOTADOS NA SEDUC':
        VALORES_CARREIRA = {
            'ANALISTA DE DESENVOLVIMENTO ECONÔMICO E SOCIAL': 7845.50,
            'TEC. DESENVOL. ECON. SOCIAL  40 HRS': 4134.55,
            'TÉCNICO DESENV.ECO.SOC L 10177/14': 4134.55,
            '15021 - INSPETOR TECNICO CIVICO MILITAR': 6421.62,
            'INSPETOR CIVICO MILITAR - NÍVEL SUPORTE E APOIO': 3944.05,
            '15019 - APOIO TECNICO ESP CIVICO MILITAR 01': 8934.43,
            'APOIO TÉCNICO ESP CÍVICO MILITAR 01': 8934.43,
            '15020 - APOIO TECNICO ESP CIVICO MILITAR 02': 8934.43,
            'APOIO TÉCNICO ESP CÍVICO MILITAR 02': 8934.43,
            'AGENTE UNIVERSITARIO LC 321/2008 - UNEMAT': 8388.38,
            'ANALISTA ADMINISTRATIVO': 7845.50,
            'ANALISTA FUNDIARIO E AGRARIO L 10042': 9956.16,
            'ANALISTA DE TECNOLOGIA DA INFORMACAO JUNIOR': 7845.50,
            'ASSESSOR JURIDICO(A)': 8934.44,
            'DGA-1': 29118.13,
            'DGA-2': 14957.21,
            'DGA-3': 10948.67,
            'DGA-4': 8934.44,
            'DGA-5': 6421.63,
            'DGA-6': 4957.81,
            'PROC. DO ESTADO EM ESTAGIO PROBAT': 37745.52,
        }
        val_base = VALORES_CARREIRA.get(cargo_carreira, 0)
        return (val_base / 2.0) * percentual * FATOR

    return 0
