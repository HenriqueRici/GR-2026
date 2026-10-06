import pandas as pd
from modelos.tratamentoPagamento import defineVinc

def test_define_vinc(tmp_path, monkeypatch):
    # Mock Home Desktop path to avoid filesystem issues during unit test execution
    monkeypatch.setattr('pathlib.Path.home', lambda: tmp_path)
    (tmp_path / 'Desktop' / 'GR 2025' / 'BASE PAGAMENTO').mkdir(parents=True, exist_ok=True)

    base = pd.DataFrame({
        'Func': [1],
        'Vinc': [1],
        'TipoVinculo': ['EFETIVO'],
        'EstimativaValorGR': [5000.0]
    })
    baseContrato = pd.DataFrame(columns=['TipoServidor', 'Func', 'Vinc', 'DataInicial', 'DataFinal'])
    baseVacancia = pd.DataFrame(columns=['Func', 'Vinc', 'Tipo', 'DataFinal'])
    licencasCalcVacancia = pd.DataFrame(columns=['Tipo'])

    defineVinc(base, baseContrato, baseVacancia, licencasCalcVacancia, pd.to_datetime('2026-12-18'))
    # Verify that files were created inside temp directory
    out_dir = tmp_path / 'Desktop' / 'GR 2025' / 'BASE PAGAMENTO'
    assert len(list(out_dir.glob('*.xlsx'))) > 0
