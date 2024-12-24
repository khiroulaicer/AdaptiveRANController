import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor

# Charger les 100 premières lignes du fichier CSV
data = pd.read_csv('ue.csv', nrows=100)

# Vérification des données
print("Aperçu des données :")
print(data.head())

print("\nTypes de données :")
print(data.dtypes)

print("\nValeurs manquantes :")
print(data.isnull().sum())

# Nettoyage des données
data['RF.serving.RSRP'] = pd.to_numeric(data['RF.serving.RSRP'], errors='coerce')
data['RF.serving.RSRQ'] = pd.to_numeric(data['RF.serving.RSRQ'], errors='coerce')
data['DRB.UEThpDl'] = pd.to_numeric(data['DRB.UEThpDl'], errors='coerce')

data['RF.serving.RSRP'] = data['RF.serving.RSRP'].fillna(data['RF.serving.RSRP'].median())
data['RF.serving.RSRQ'] = data['RF.serving.RSRQ'].fillna(data['RF.serving.RSRQ'].median())
data['DRB.UEThpDl'] = data['DRB.UEThpDl'].fillna(data['DRB.UEThpDl'].median())

# Vérification des statistiques descriptives
print("\nStatistiques descriptives :")
print(data[['RF.serving.RSRP', 'RF.serving.RSRQ', 'DRB.UEThpDl']].describe())

# Vérification des valeurs aberrantes
outliers_rsrp = data[(data['RF.serving.RSRP'] < -140) | (data['RF.serving.RSRP'] > -50)]
print("\nValeurs aberrantes dans RSRP :")
print(outliers_rsrp)

# Sélectionner les features et la cible
features = ['RF.serving.RSRP', 'RF.serving.RSRQ']
X = data[features]  # Features
y = data['DRB.UEThpDl']  # Target variable

# Diviser les données en ensembles d'entraînement et de test
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Création et entraînement du modèle de régression
model = RandomForestRegressor(n_estimators=100)
model.fit(X_train, y_train)

# Évaluation du modèle
print("\nScore du modèle : ", model.score(X_test, y_test))

# Fonction pour l'allocation dynamique des PRB
def allocate_prb(predicted_thp):
    threshold = 100  # Définir selon l'analyse des données
    return 'Increase PRB' if predicted_thp > threshold else 'Decrease PRB'

# Utilisation du modèle pour faire une prédiction sur une nouvelle donnée
new_data = pd.DataFrame([[-85, -12]], columns=features)
predicted_thp = model.predict(new_data)
allocation_decision = allocate_prb(predicted_thp[0])

print("\nDécision d'allocation des PRB : ", allocation_decision)
