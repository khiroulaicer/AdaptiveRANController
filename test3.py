import pandas as pd
import numpy as np

# Charger les données
data = pd.read_csv('path_to_ue.csv')

# Définir la plage acceptable de RSRP
MIN_RSRP = -140
MAX_RSRP = -50

# Remplacer les valeurs hors plage par NaN
data.loc[(data['RF.serving.RSRP'] < MIN_RSRP) | (data['RF.serving.RSRP'] > MAX_RSRP), 'RF.serving.RSRP'] = np.nan

# Interpoler les valeurs NaN
data['RF.serving.RSRP'] = data['RF.serving.RSRP'].interpolate()

# Vérifier s'il reste des NaN et les imputer avec la médiane des valeurs valides
if data['RF.serving.RSRP'].isna().any():
    median_value = data['RF.serving.RSRP'].median()
    data['RF.serving.RSRP'].fillna(median_value, inplace=True)

# Sauvegarder les données ajustées
data.to_csv('path_to_adjusted_ue.csv', index=False)
