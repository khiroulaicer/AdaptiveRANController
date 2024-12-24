import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def visualize_connections(df):
    """
    Visualise le nombre de UEs par identité de cellule.
    """
    connection_counts = df.groupby('nrCellIdentity')['ue-id'].count()
    connection_counts.plot(kind='bar')
    plt.xlabel('Identité de Cellule')
    plt.ylabel('Nombre de UEs')
    plt.title('UEs par Cellule')
    plt.show()
    
def load_data(filepath):
    """
    Charge les données depuis un fichier CSV.
    """
    return pd.read_csv(filepath)

def verify_data(df):
    """
    Vérifie les données pour s'assurer qu'elles sont logiques et cohérentes.
    Par exemple, vérifier si les valeurs de RSRP sont dans une plage acceptable.
    """
    # Supposons que le RSRP acceptable est entre -140 et -50 dBm
    if not df['RF.serving.RSRP'].between(-140, -50).all():
        print("Il y a des valeurs de RSRP hors plage acceptable.")
    else:
        print("Toutes les valeurs de RSRP sont dans la plage acceptable.")

def simulate_connections(df):
    """
    Simule les connexions en se basant sur les données de signalisation et les identifiants de cellule.
    """
    # Supposons une simulation simple où nous comptons les UEs par cellule
    connections = df.groupby('nrCellIdentity')['ue-id'].count()
    print("Nombre de UEs par identité de cellule :")
    print(connections)

def main():
    filepath = 'ue.csv'
    ue_data = load_data(filepath)
    verify_data(ue_data)
    simulate_connections(ue_data)
    visualize_connections(ue_data)

if __name__ == "__main__":
    main()
