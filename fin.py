import asyncio
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from influxdb_client import InfluxDBClient
from datetime import datetime
import pickle
import os
from lib.e2sm_rc_module import e2sm_rc_module
from lib.xAppBase import xAppBase

# Configuration d'InfluxDB
INFLUXDB_URL = "http://10.180.113.115:32086"
INFLUXDB_TOKEN = "1HLKmioofK_8XuSBJwZBHSv8oIB9fcxmJg9s_v59aZ8N8pNeDvQS-QiVAjuGHJVoiL1FqOm7fB107t2pfP3YnA=="
INFLUXDB_ORG = "oran-lab"
INFLUXDB_BUCKET = "e2data_laicer"

# Fichier pour sauvegarder le modèle
MODEL_FILE = "model.pkl"

class AdaptiveRANController(xAppBase):
    def __init__(self, config, http_server_port, rmr_port):
        super(AdaptiveRANController, self).__init__(config, http_server_port, rmr_port)
        self.e2_module = e2sm_rc_module(self)
        self.model = None

        # Charger le modèle existant ou en créer un nouveau
        self.load_model()

    def load_model(self):
        """Charge le modèle depuis un fichier ou initialise un nouveau modèle."""
        try:
            if os.path.exists(MODEL_FILE):
                print("Chargement du modèle existant...")
                with open(MODEL_FILE, 'rb') as f:
                    self.model = pickle.load(f)
            else:
                print("Aucun modèle trouvé. Création d'un nouveau modèle.")
                self.model = LogisticRegression()
        except Exception as e:
            print(f"Erreur lors du chargement du modèle : {e}")
            self.model = LogisticRegression()

    def save_model(self):
        """Sauvegarde le modèle dans un fichier."""
        try:
            with open(MODEL_FILE, 'wb') as f:
                pickle.dump(self.model, f)
            print("Modèle sauvegardé avec succès.")
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du modèle : {e}")

    @xAppBase.start_function
    def start(self):
        """Démarre la boucle principale de la xApp."""
        while self.running:
            asyncio.run(self.main())
            print("xApp is running. Sleeping for 60 seconds...")
            asyncio.sleep(60)

    async def main(self):
        """Cycle principal : collecte, entraînement et prise de décisions."""
        try:
            # Collecte des données
            data = await self.fetch_data_from_influx()
            if data.size == 0:
                print("Aucune donnée trouvée dans InfluxDB.")
                return

            # Entraînement du modèle
            print("Préparation et entraînement du modèle...")
            self.train_model(data)

            # Prise de décision
            print("Prise de décision...")
            self.make_decisions(data)
        except Exception as e:
            print(f"Erreur dans le cycle principal : {e}")

    async def fetch_data_from_influx(self):
        """Récupère les données depuis InfluxDB."""
        try:
            print("Lecture des données depuis InfluxDB...")
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
        except Exception as e:
            print(f"Erreur lors de la collecte des données : {e}")
            return np.array([])

    def train_model(self, data):
        """Entraîne le modèle avec les données collectées."""
        try:
            X = data[:, :-1]
            y = (data[:, -1] > 0.5).astype(int)

            # Vérification des données
            if len(X) == 0 or len(y) == 0:
                print("Pas assez de données pour entraîner le modèle.")
                return

            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            self.model.fit(X_train, y_train)

            # Évaluer le modèle
            accuracy = accuracy_score(y_test, self.model.predict(X_test))
            print(f"Précision du modèle : {accuracy * 100:.2f}%")

            # Sauvegarder le modèle
            self.save_model()
        except Exception as e:
            print(f"Erreur lors de l'entraînement du modèle : {e}")

    def make_decisions(self, data):
        """Prend des décisions basées sur les prédictions du modèle."""
        try:
            X = data[:, :-1]

            for i, row in enumerate(X):
                prediction = self.model.predict([row])[0]
                rsrp, target_tput = row

                if prediction == 0:
                    print(f"Ligne {i} : Ajuster les ressources (RSRP={rsrp}, TargetTput={target_tput})")
                    try:
                        self.e2_module.control_slice_level_prb_quota(
                            e2_node_id="gnbd_001_001_00019b_0",
                            ue_id=i,
                            min_prb_ratio=10,
                            max_prb_ratio=50,
                            dedicated_prb_ratio=30
                        )
                        print(f"Commande envoyée au RIC pour l'UE {i} : Ajustement PRB (min: 10%, max: 50%, dédié: 30%)")
                    except Exception as e:
                        print(f"Erreur lors de l'envoi de la commande pour l'UE {i} : {e}")
                else:
                    print(f"Ligne {i} : Aucune action requise (RSRP={rsrp}, TargetTput={target_tput})")
        except Exception as e:
            print(f"Erreur lors de la prise de décision : {e}")

if __name__ == "__main__":
    # Configuration de l'instance xApp
    config = ""
    http_server_port = 8080
    rmr_port = 4560

    # Lancement de la xApp
    app = AdaptiveRANController(config, http_server_port, rmr_port)
    app.start()
