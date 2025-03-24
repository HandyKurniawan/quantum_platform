from qiskit import QuantumCircuit
from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit.qasm2 import dumps

import mysql.connector
import networkx as nx
import os
import sys

module_path = os.path.abspath(os.path.join('.', 'wrappers'))
if module_path not in sys.path:
    sys.path.append(module_path)

from commons import (
    used_qubits, sum_middle_digits_dict
)

from wrappers.multiprogramming_wrapper import (
    avoid_simultaneous_cnot, add_zz_on_simultaneous_cnot, 
    build_idle_coupling_map, multiprogram_compilation_qiskit, merge_circuits,
    get_LF_presets_cm
)
from wrappers.polar_wrapper import (
        polar_code_p2, get_logical_error_on_accepted_states
)

from wrappers.prune_wrapper import (
    create_full_graph, generate_figures, generate_node_errors, generate_edge_errors,
    get_latest_calibration_id, get_edges_threshold, get_readout_threshold, get_LF_qubits
)


# MySQL connection parameters
mysql_config = {
    'user': 'handy',
    'password': 'handy',
    'host': 'ec2-16-171-135-24.eu-north-1.compute.amazonaws.com',
    'database': 'calibration_data'
}

# Connect to the MySQL database
conn = mysql.connector.connect(**mysql_config)

shots = 100

from qEmQUIP import QEM, conf
import mysql.connector

mysql_config = {
    'user': 'handy',
    'password': 'handy',
    'host': 'localhost',
    'database': 'framework'
}

token = "971b2597e1f28e10a7c8992657e9ecc984a65bd4a22bacc497eda4d2945bf8e501b454b9e5d2527833808ab8ec62fc5fa0df3af38dccc02b85bd83c93f2e2e31"
q = QEM(runs=conf.runs, user_id=conf.user_id, token=token, skip_db=False)

# prepare the circuit
qasm_files = q.get_qasm_files_from_path("./circuits/polar_sim/n3/x")
print(qasm_files)

# select compilation techniques
compilations = ["qiskit_3"]

q.set_backend(program_type="sampler")

mp_options = {"enable":True, "execution_type":"final"}

prune_options = {"enable":True, "type":"cal-avg", "params": (0.020,0.10)}
# prune_options = {"enable":True, "type":"lf", "params": 50}
"""
prune type:
- cal-lcd: use the threshold of the two-qubit gates and readout with last calibration data. Params: (cx,ro): tuple
- cal-avg: use the threshold of the two-qubit gates and readout with average calibration data. Params: (cx,ro): tuple
- lf: use the qubits from LF benchmark. Params: lf: int, number qubits
"""


#q.compile_multiprogramming(qasm_files*3, compilations)

# q.send_to_real_backend("sampler", qasm_files*2, compilations, 
#                        mp_options=mp_options,
#                        prune_options=prune_options)

# q.send_to_real_backend("sampler", qasm_files, compilations, 
#                        prune_options=prune_options)

noise_levels = [0, 1]

q.run_simulator("sampler", qasm_files*2, compilations,
                noise_levels, shots, send_to_db=True, 
                mp_options=mp_options)