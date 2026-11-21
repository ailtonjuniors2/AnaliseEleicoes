from comparativoanos import executar_analises


def obter_dados(
    turno=1,
    excluir_exterior=False,
    min_aptos=5000
):

    resultados = executar_analises(
        turno=turno,
        excluir_exterior=excluir_exterior,
        min_aptos=min_aptos
    )

    return resultados