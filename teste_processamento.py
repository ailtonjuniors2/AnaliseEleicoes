import pandas as pd
from processamento import obter_dados

print("Iniciando processamento eleitoral...")

resultados = obter_dados(
    turno=1,
    excluir_exterior=False,
    min_aptos=5000
)

print("\nProcessamento concluído!")

for nome, resultado in resultados.items():

    print(f"\n{'=' * 50}")
    print(nome.upper())
    print("=" * 50)

    if isinstance(resultado, pd.DataFrame):
        print(resultado.head(5))
        print(f"Total de registros: {len(resultado)}")

    else:
        print(resultado)
