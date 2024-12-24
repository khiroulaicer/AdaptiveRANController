import pandas as pd

# Charger les données
data = pd.read_csv('ue.csv')

# Définir la plage acceptable de RSRP
MIN_RSRP = -140
MAX_RSRP = -50

# Identifier les valeurs hors plage
invalid_rsrp = data[(data['RF.serving.RSRP'] < MIN_RSRP) | (data['RF.serving.RSRP'] > MAX_RSRP)]
print(f"Nombre de valeurs hors plage : {len(invalid_rsrp)}")

# Filtrer les valeurs hors plage
filtered_data = data[(data['RF.serving.RSRP'] >= MIN_RSRP) & (data['RF.serving.RSRP'] <= MAX_RSRP)]

# Sauvegarder les données corrigées
filtered_data.to_csv('ue.csv', index=False)
