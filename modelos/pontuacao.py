def pontuacaoGeral(base):
    if base.get('DiasAbsenteismo', 0) > 30:
        return 0

    cargo = base.get('CargoGR')
    pontos_base = (
        base.get('PontuacaoAbsenteismo', 0)
        + base.get('PontuacaoEvasao', 0)
        + base.get('PontuacaoFormacao', 0)
        + base.get('PontuacaoMetaAprendizagem', 0)
    )

    if cargo == 'GESTOR':
        return pontos_base + 225
    elif cargo in ['PROFESSOR FORA DE REGÊNCIA', 'PROFESSOR EM REGÊNCIA', 'CIVIS E MILITARES LOTADOS NA SEDUC']:
        return pontos_base
    elif cargo == 'TAE/AAE':
        return pontos_base + 250
    else:
        return 0


def valorFinalGR(base):
    return (base.get('ValorGRBaseVinculo', 0) / 1000.0) * base.get('PontuacaoGeral', 0)
