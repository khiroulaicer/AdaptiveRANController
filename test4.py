import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor

# Charger les données
data = pd.read_csv('ue.csv')

# Nettoyage des données et sélection des colonnes pertinentes
data['RF.serving.RSRP'] = data['RF.serving.RSRP'].fillna(data['RF.serving.RSRP'].median())
data['RF.serving.RSRQ'] = data['RF.serving.RSRQ'].fillna(data['RF.serving.RSRQ'].median())
data['DRB.UEThpDl'] = data['DRB.UEThpDl'].fillna(data['DRB.UEThpDl'].median())

# Sélectionner les features pour la prédiction et la cible
features = ['RF.serving.RSRP', 'RF.serving.RSRQ']
X = data[features]  # Features
y = data['DRB.UEThpDl']  # Target variable

# Diviser les données en ensembles d'entraînement et de test
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Création et entraînement du modèle de régression
model = RandomForestRegressor(n_estimators=100)
model.fit(X_train, y_train)

# Évaluation du modèle
print("Score du modèle : ", model.score(X_test, y_test))

# Fonction pour l'allocation dynamique des PRB
def allocate_prb(predicted_thp):
    threshold = 100  # Définir selon l'analyse des données
    return 'Increase PRB' if predicted_thp > threshold else 'Decrease PRB'

# Utilisation du modèle pour faire une prédiction sur une nouvelle donnée
new_data = pd.DataFrame([[-85, -12]], columns=features)
predicted_thp = model.predict(new_data)
allocation_decision = allocate_prb(predicted_thp[0])

print("Décision d'allocation des PRB : ", allocation_decision)
