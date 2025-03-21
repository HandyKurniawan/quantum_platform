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

shots = 10000

from qEmQUIP import QEM, conf
import mysql.connector

mysql_config = {
    'user': 'handy',
    'password': 'handy',
    'host': 'localhost',
    'database': 'framework'
}

token = "9e068d694502429634a4706a9f08781beac043c44af9642dfe89757093b049ba266b0ce9f488d4220d386114b5f785a518827881e0645b530203026ad7ab9d7e"
q = QEM(runs=conf.runs, user_id=conf.user_id, token=token, skip_db=False)

# prepare the circuit
qasm_files = q.get_qasm_files_from_path("./circuits/polar_sim/n3/x")
print(qasm_files)

# select compilation techniques
compilations = ["qiskit_3"]

q.set_backend(program_type="sampler")

#q.compile_multiprogramming(qasm_files*3, compilations)
q.send_to_real_backend("sampler", qasm_files*2, compilations, enable_mp=True, mp_execution_type="final")