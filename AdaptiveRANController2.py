import os
import asyncio
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from influxdb_client import InfluxDBClient
import mlflow
import mlflow.sklearn
from datetime import datetime


# Configuration InfluxDB
INFLUXDB_URL = "http://10.180.113.115:32086"
INFLUXDB_TOKEN = "FUexw0jlTRCJ6pp861SW6dW_dsa1mctRcqr4DRune7L9_ThhUpEq9DA0KyD-LaGJOg32_e4oOhnz_ff-7xaNxg=="
INFLUXDB_ORG = "oran-lab"
INFLUXDB_BUCKET = "e2data_laicer"
os.environ['MLFLOW_TRACKING_USERNAME'] = 'user'
os.environ['MLFLOW_TRACKING_PASSWORD'] = 'sr9TvkIjaj'

# Récupération des informations d'authentification à partir des variables d'environnement
# mlflow_username = os.environ.get('MLFLOW_TRACKING_USERNAME')
# mlflow_password = os.environ.get('MLFLOW_TRACKING_PASSWORD')
# print(mlflow_password, mlflow_username)
# exit()
# Configuration MLflow
mlflow.set_tracking_uri("http://10.180.113.115:32256/")
mlflow.set_experiment("AdaptiveRAN_Optimization")


# Fonction pour lire les données d'InfluxDB
async def fetch_data_from_influx():
    client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
    query_api = client.query_api()

    query = f'''
    from(bucket: "{INFLUXDB_BUCKET}")
    |> range(start: -1h)
    |> filter(fn: (r) => r._measurement == "ue_metrics")
    |> filter(fn: (r) => r._field == "RSRP" or r._field == "TargetTput" or r._field == "RSSINR")
    |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
    |> keep(columns: ["RSRP", "TargetTput", "RSSINR"])
    '''
    tables = query_api.query(query)
    data = []

    for table in tables:
        for record in table.records:
            data.append([record["RSRP"], record["TargetTput"], record["RSSINR"]])

    client.close()
    return np.array(data)

# Fonction principale
async def main():
    # Charger les données
    print("Lecture des données depuis InfluxDB...")
    data = await fetch_data_from_influx()

    if data.size == 0:
        print("Aucune donnée trouvée dans InfluxDB.")
        return

    # Préparer les données pour le modèle
    print("Préparation des données et entraînement du modèle...")
    X = data[:, :-1]  # Variables indépendantes (RSRP et TargetTput)
    y = (data[:, -1] > 0.5).astype(int)  # Label binaire basé sur une condition

    # Vérification de la distribution des classes
    unique, counts = np.unique(y, return_counts=True)
    class_distribution = dict(zip(unique, counts))
    print(f"Distribution des classes : {class_distribution}")

    # Ajouter des échantillons synthétiques si une seule classe est présente
    if len(unique) == 1:
        print("Une seule classe détectée, ajout d'échantillons synthétiques...")
        X_synthetic = np.random.uniform(X.min(axis=0), X.max(axis=0), size=(10, X.shape[1]))
        y_synthetic = 1 - unique[0]
        X = np.vstack([X, X_synthetic])
        y = np.hstack([y, [y_synthetic] * len(X_synthetic)])

    # Séparer les données en ensembles d'entraînement et de test
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Entraîner le modèle
    model = LogisticRegression()
    model.fit(X_train, y_train)

    # Évaluer le modèle
    accuracy = accuracy_score(y_test, model.predict(X_test))
    print(f"Précision du modèle : {accuracy * 100:.2f}%")

    # Enregistrement dans MLflow
    with mlflow.start_run():
        mlflow.log_metric("accuracy", accuracy)
        mlflow.log_param("model_type", "LogisticRegression")
        mlflow.sklearn.log_model(
            sk_model=model,
            artifact_path="AdaptiveRANController",
            registered_model_name="AdaptiveRANController"
        )
    print(f"Modèle enregistré sous le nom 'AdaptiveRANController' dans MLflow.")

    # Prise de décision
    print("Prise de décision sur la base des prédictions...")
    for i, prediction in enumerate(model.predict(X_test)):
        if prediction == 0:
            print(f"Décision pour l'utilisateur {i}: Désactiver le nœud ou ajuster les ressources.")
        elif prediction == 1:
            print(f"Décision pour l'utilisateur {i}: Maintenir ou améliorer les allocations.")

# Exécuter la fonction principale
if __name__ == "__main__":
    asyncio.run(main())
