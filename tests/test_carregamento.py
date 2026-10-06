import pandas as pd
from modelos.carregamentoDeDados import carregarArquivo

def test_carregar_arquivo_csv(tmp_path):
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("Func;Vinc;Nome\n1;2;João\n")
    df = carregarArquivo(csv_file, selected_columns=['Func', 'Vinc', 'Nome'])
    assert len(df) == 1
    assert df.iloc[0]['Nome'] == 'João'
