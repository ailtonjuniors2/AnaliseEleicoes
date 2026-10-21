import pandas as pd

df = pd.read_csv('detalhe_votacao_munzona_2026_BRASIL.csv', encoding="latin1", sep=';')
print(df.info())