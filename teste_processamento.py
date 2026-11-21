
# ============================================================
# TESTE DO PROCESSAMENTO
# ============================================================

from processamento import obter_dados


# Executa as análises do primeiro turno.

print("Iniciando processamento eleitoral...")

resultados = obter_dados(
    turno=1,
    excluir_exterior=False
)

print("\nProcessamento concluído!")


# Exibe cada resultado.

for nome, tabela in resultados.items():

    print(f"\n{'=' * 50}")
    print(nome.upper())
    print("=" * 50)

    if tabela.empty:
        print("Nenhum dado disponível.")
    else:
        print(tabela.head(10))


print("\nTodos os testes foram executados!")
