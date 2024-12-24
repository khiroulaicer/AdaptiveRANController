import pandas as pd
import numpy as np

# Charger les données (100 premières lignes pour tester)
data = pd.read_csv('ue.csv', nrows=100)

# Nettoyer les données
data['RF.serving.RSRP'] = pd.to_numeric(data['RF.serving.RSRP'], errors='coerce').fillna(data['RF.serving.RSRP'].median())
data['RF.serving.RSRQ'] = pd.to_numeric(data['RF.serving.RSRQ'], errors='coerce').fillna(data['RF.serving.RSRQ'].median())
data['DRB.UEThpDl'] = pd.to_numeric(data['DRB.UEThpDl'], errors='coerce').fillna(data['DRB.UEThpDl'].median())

# Exemple : Positions des nœuds (x, y) et leurs capacités
nodes = pd.DataFrame({
    'node_id': ['Node1', 'Node2', 'Node3'],
    'x': [0, 500, 1000],  # Positions fictives
    'y': [0, 500, 0],
    'capacity': [50, 50, 50]  # Capacité maximale des connexions
})

# Ajouter les positions des UEs depuis le fichier CSV
ues = data[['du-id', 'x', 'y', 'RF.serving.RSRP', 'RF.serving.RSRQ']].copy()
ues.columns = ['ue_id', 'x', 'y', 'RSRP', 'RSRQ']

# Fonction pour calculer la distance entre un UE et un nœud
def calculate_distance(ue, node):
    return np.sqrt((ue['x'] - node['x'])**2 + (ue['y'] - node['y'])**2)

# Associer chaque UE au nœud ayant le meilleur signal
def connect_ues_to_nodes(ues, nodes):
    connections = []
    for _, ue in ues.iterrows():
        best_node = None
        best_signal = -np.inf
        for _, node in nodes.iterrows():
            # Distance entre le UE et le nœud
            distance = calculate_distance(ue, node)
            # Calcul simple du signal : RSRP (moins la pénalité de distance)
            signal_strength = ue['RSRP'] - 0.1 * distance
            if signal_strength > best_signal:
                best_signal = signal_strength
                best_node = node['node_id']
        connections.append((ue['ue_id'], best_node, best_signal))
    return connections

# Effectuer les connexions
connections = connect_ues_to_nodes(ues, nodes)

# Transformer les connexions en DataFrame pour analyse
connections_df = pd.DataFrame(connections, columns=['ue_id', 'connected_node', 'signal_strength'])

# Ajouter les connexions aux nœuds
node_load = connections_df.groupby('connected_node').size().reset_index(name='connected_ues')

# Fusionner avec les informations des nœuds pour vérifier les surcharges
node_status = pd.merge(nodes, node_load, left_on='node_id', right_on='connected_node', how='left').fillna(0)
node_status['connected_ues'] = node_status['connected_ues'].astype(int)
node_status['overloaded'] = node_status['connected_ues'] > node_status['capacity']

# Décisions pour chaque nœud
def node_decision(node):
    if node['overloaded']:
        return 'Add resources or offload UEs'
    elif node['connected_ues'] == 0:
        return 'Node underutilized, consider power-saving mode'
    else:
        return 'Node operating normally'

node_status['decision'] = node_status.apply(node_decision, axis=1)

# Décisions pour chaque UE
def ue_decision(ue):
    if ue['signal_strength'] < -100:
        return 'Redirect UE or increase node power'
    else:
        return 'Connection stable'

connections_df['decision'] = connections_df.apply(ue_decision, axis=1)

# Afficher les résultats
print("\nStatut des nœuds avec décisions :")
print(node_status)

print("\nConnexions des UEs avec décisions :")
print(connections_df)

# Identifier les UEs ayant un signal faible
low_signal_ues = connections_df[connections_df['signal_strength'] < -100]
print("\nUEs avec un signal faible :")
print(low_signal_ues)
