import networkx as nx

import random
import matplotlib.pyplot as plt


from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize

def create_full_graph(cm, coords, edge_weights):
    # Create a graph for qubits
    # G = nx.path_graph(15)  # Create a line graph with 14 qubits (0 to 13)
    G = nx.Graph()
    pos = {}

    for i,j in cm:
        #print(i, j, )
        G.add_edge(i, j, weight = edge_weights[(i,j)])
        
        
    #G.add_edges_from(cm)
        
    for idx, coord in enumerate(coords):
        i,j = coord
        #print(idx, i, j)
        pos[idx] = (i,j * -1)
        # pos[idx] = (i,j * 1)
        
    
    return G, pos
    


def generate_figures(G, pos, node_errors, edge_errors, title="", edge_colors = "navy", show_bar = False):

     
    # Normalize the error rates for color mapping
    norm_node = Normalize(vmin=0, vmax=1)
    norm_edge = Normalize(vmin=0, vmax=1)
    
    # Create color maps
    node_cmap = plt.get_cmap('winter')
    edge_cmap = plt.get_cmap('winter')
    
    # Draw the graph
    fig, ax = plt.subplots(figsize=(12, 9))
    plt.title(title)
    
    # Draw nodes
    nx.draw_networkx_nodes(G, pos, node_color=node_errors, cmap=node_cmap, node_size=500, edgecolors=edge_colors, ax=ax, linewidths=2)
    
    # Draw edges
    nx.draw_networkx_edges(G, pos, edge_color=edge_errors, edge_cmap=edge_cmap, width=6, ax=ax)
    #nx.draw_networkx_edges(G, pos, edge_cmap=edge_cmap, width=6, ax=ax)
    
    # Draw labels
    nx.draw_networkx_labels(G, pos, font_color='white', font_size=10, font_family='sans-serif', ax=ax)

    if show_bar:
        # Create a divider for the existing axes instance
        divider = make_axes_locatable(ax)
        
        # Append axes to the right of the main axes for colorbars
        cax_node = divider.append_axes("right", size="5%", pad=0.25)
        
        
        # Add colorbars for node and edge errors
        #sm_node = ScalarMappable(cmap=node_cmap, norm=norm_node)
        sm_node = ScalarMappable(cmap=node_cmap)
        sm_node.set_array([])
        cbar_node = plt.colorbar(sm_node, cax=cax_node)
        cbar_node.set_label('Readout assignment error', fontsize=10)

        cbar_node.ax.yaxis.set_label_position('left')
        cbar_node.ax.yaxis.label.set_verticalalignment('center')
        cbar_node.ax.yaxis.label.set_horizontalalignment('right')
        cbar_node.ax.yaxis.label.set_position((-1.0, 0.6))  # Adjust x position to move label left

        
        cbar_node.ax.tick_params(labelsize=7)
        
        ## Set the ticks and labels for the node colorbar
        cbar_node.set_ticks([0, 1])
        cbar_node.set_ticklabels(["{:.3e}".format(min(node_errors)), "{:.3e}".format(max(node_errors))])
        #cbar_node.set_ticklabels(["{:.3e}".format(0), "{:.3e}".format(1)])
    
        cax_edge = divider.append_axes("right", size="5%", pad=0.75)
        
        #sm_edge = ScalarMappable(cmap=edge_cmap, norm=norm_edge)
        sm_edge = ScalarMappable(cmap=edge_cmap)
        sm_edge.set_array([])
        cbar_edge = plt.colorbar(sm_edge, cax=cax_edge)
        cbar_edge.set_label('ECR error', fontsize=10)
        
        cbar_edge.ax.yaxis.set_label_position('left')
        cbar_edge.ax.yaxis.label.set_verticalalignment('center')
        cbar_edge.ax.yaxis.label.set_horizontalalignment('right')
        cbar_edge.ax.yaxis.label.set_position((-1.0, 0.6))  # Adjust x position to move label left
        
        cbar_edge.ax.tick_params(labelsize=7)
        
        # Set the ticks and labels for the edge colorbar
        cbar_edge.set_ticks([0, 1])
        cbar_edge.set_ticklabels(["{:.3e}".format(min(edge_errors)), "{:.3e}".format(max(edge_errors))])
        #cbar_edge.set_ticklabels(["{:.3e}".format(0), "{:.3e}".format(1)])
    
    return plt
    
def get_cal_edge_errors(cal_id, conn):
    # # Connect to the MySQL database
    # conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor()
    
    sql = '''
    SELECT qubit_control, qubit_target, CASE WHEN ecr_error = 0 THEN cz_error ELSE ecr_error END 
    FROM calibration_data.ibm_two_qubit_gate_spec 
    WHERE calibration_id = {};
    '''.format(cal_id)
    
    # insert to circuit
    cursor.execute(sql)
    
    results = cursor.fetchall()
    
    cursor.close()
    # conn.close()

    cal_edge_errors = {}

    for res in results:
        c, t, e = res
        cal_edge_errors[(c,t)] = e
        cal_edge_errors[(t,c)] = e

    return cal_edge_errors
    
def get_cal_node_errors(cal_id, conn):
    # # Connect to the MySQL database
    # conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor()
    
    sql = '''
    SELECT qubit, readout_error
    FROM calibration_data.ibm_qubit_spec 
    WHERE calibration_id = {};
    '''.format(cal_id)
    
    # insert to circuit
    cursor.execute(sql)
    
    results = cursor.fetchall()
    
    cursor.close()
    # conn.close()

    cal_node_errors = {}

    for res in results:
        q, e = res
        cal_node_errors[q] = e

    return cal_node_errors
    
def generate_node_errors(G, conn, cal_id = None):
    node_errors = []


    if cal_id == None:
        node_errors = [random.uniform(0, 0.4) for _ in range(len(G.nodes()))]
        #for e in G.nodes():
        #    node_errors.append(0.001 * e)
    else:
        cal_node_errors = get_cal_node_errors(cal_id, conn)
        #print(cal_node_errors)
        for e in G.nodes():
            node_errors.append(float(cal_node_errors[e]))
    
    return node_errors

def generate_edge_errors(G, conn, cal_id = None):
    edge_errors = []
    
    #for e in G.edges():
    #    edge_errors.append(0.001 * e[0] * e[1])

    if cal_id == None:
        edge_errors = [random.uniform(0, 0.4) for _ in range(len(G.edges()))]
    else:
        cal_edge_errors = get_cal_edge_errors(cal_id, conn)
        
        for e in G.edges():
            edge_errors.append(float(cal_edge_errors[e]))
    
    return edge_errors
    
def get_latest_calibration_id(hw_name, conn):
    # conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor()

    sql = """
    SELECT calibration_id, calibration_datetime FROM calibration_data.ibm 
WHERE hw_name = "{}" 
ORDER BY calibration_datetime DESC LIMIT 1
""".format(hw_name)

    cursor.execute(sql)

    results = cursor.fetchall()
    
    cursor.close()
    # conn.close()

    for res in results:
        cal_id, cal_datetime = res
        

    return cal_id, cal_datetime
    
def get_edges_threshold(hw_name, threshold, conn, cal_id = None):
    # conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor()

    edges_list = []
    nodes_list = []

    if cal_id is None:
        sql = """
        SELECT qubit_control, qubit_target FROM (
    SELECT qubit_control, qubit_target, AVG(ecr_error) AS avg_ecr_error
    FROM (
    SELECT DISTINCT qubit_control, qubit_target, ecr_error, ecr_date
    FROM calibration_data.ibm_two_qubit_gate_spec q
    WHERE q.hw_name = "{}" AND ecr_error != 1
    ) X GROUP BY qubit_control, qubit_target) Y
    WHERE avg_ecr_error > {}
    """.format(hw_name, threshold)
    else:
        sql = """
    SELECT qubit_control, qubit_target
    FROM calibration_data.ibm_two_qubit_gate_spec q
    WHERE q.hw_name = "{}" AND CASE WHEN ecr_error = 0 THEN cz_error ELSE ecr_error END > {} AND calibration_id = {}
    """.format(hw_name, threshold, cal_id)

    cursor.execute(sql)

    results = cursor.fetchall()
    
    cursor.close()
    # conn.close()

    for res in results:
        c, t = res
        edges_list.append((c, t))
        edges_list.append((t, c))

        nodes_list.append(c)
        nodes_list.append(t)

    return list(set(nodes_list))
    
def get_readout_threshold(hw_name, threshold, conn, cal_id = None):
    # conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor()

    edges_list = []
    nodes_list = []

    if cal_id is None:
        sql = """
    SELECT qubit, avg_readout_error FROM (
    SELECT qubit, AVG(readout_error) as avg_readout_error
    FROM (
    SELECT DISTINCT qubit, readout_error, readout_error_date
    FROM calibration_data.ibm_qubit_spec q
    INNER JOIN calibration_data.ibm i ON q.calibration_id = i.calibration_id 
    WHERE i.hw_name = "{}" AND readout_error != 1
    ) X GROUP BY qubit) Y
    WHERE avg_readout_error > {};
    """.format(hw_name, threshold)
    else:
        sql = """
    SELECT qubit, readout_error
    FROM calibration_data.ibm_qubit_spec q
    INNER JOIN calibration_data.ibm i ON q.calibration_id = i.calibration_id 
    WHERE i.hw_name = "{}" AND readout_error > {} AND i.calibration_id = {}

    """.format(hw_name, threshold, cal_id)

    cursor.execute(sql)

    results = cursor.fetchall()
    
    cursor.close()
    # conn.close()

    for res in results:
        q, er = res

        nodes_list.append(q)

    return list(set(nodes_list))

def get_LF_qubits(hw_name, num_qubits, conn):
    # conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor()

    sql = """
    SELECT DISTINCT q.name, g.value, q.qubits FROM calibration_data.ibm_qlist_spec q
INNER JOIN calibration_data.ibm_general_spec g ON q.calibration_id = g.calibration_id AND q.name = g.name
INNER JOIN calibration_data.ibm i ON q.calibration_id = i.calibration_id
WHERE i.hw_name = "{}" AND q.name = "lf_{}" ORDER BY i.calibration_datetime DESC limit 1;

    """.format(hw_name, num_qubits)

    cursor.execute(sql)

    results = cursor.fetchall()
    
    cursor.close()
    # conn.close()

    for res in results:
        prop_name, val, qubits = res

    return [int(x) for x in qubits[1:-1].split(", ")]

