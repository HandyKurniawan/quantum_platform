import sys, glob, os
from commons import convert_to_json, triq_optimization, qiskit_optimization, \
    calibration_type_enum, qiskit_compilation_enum, normalize_counts, calculate_success_rate_tvd, \
    convert_dict_binary_to_int, convert_dict_int_to_binary, sum_last_n_digits_dict
import wrappers.qiskit_wrapper as qiskit_wrapper
from wrappers.qiskit_wrapper import QiskitCircuit
import pandas as pd
import mthree
import mapomatic as mm
import mthree

from qiskit.quantum_info import SparsePauliOp
from qiskit import QuantumCircuit
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime.options import SamplerOptions, EstimatorOptions, DynamicalDecouplingOptions, TwirlingOptions

from qiskit_aer import AerSimulator, QasmSimulator, Aer
from qiskit.qasm2 import dumps
import matplotlib.pyplot as plt
import numpy as np

import mitiq
from mitiq import zne, benchmarks

from qEmQUIP import QEM, conf

token = "476ea8c61cc54f36e4a21d70a8442f94203c9d87096eaad0886a3e8154d8c2e79bcad6f927c6050a76335dd68d783f478c1b828504748a4377b441c335c831aa"

# select compilation techniques
compilations = ["qiskit_3", "triq_lcd_sabre"]

# Setup the object for n3_x
conf.triq_measurement_type = "polar_meas"
q = QEM(runs=conf.runs, user_id=conf.user_id, token=token)

# # update TriQ configs from calibration data
# q.update_hardware_configs()

# # update IBM FakeBackend configuration
# shots = 1000
# q.set_backend(program_type="sampler", shots=shots)
# qiskit_wrapper.generate_new_props(q.backend, "avg")
# qiskit_wrapper.generate_new_props(q.backend, "mix")
# qiskit_wrapper.generate_new_props(q.backend, "recent_15_adjust")

# qasm_files = q.get_qasm_files_from_path("./circuits/polar_sim/n3/x")
# qasm_files = qasm_files
# print(qasm_files)
# # noise_levels = [0.1, 0.2, 0.4, 0.6, 0.8, 1.0]
# noise_levels = [0.0]
# shots = 10000
# q.set_backend(program_type="sampler", shots=shots)
# q.run_simulator("sampler", qasm_files, compilations, noise_levels, shots, send_to_db=True)

# q = None
# # Setup the object for n3_z
# conf.triq_measurement_type = "polar_mix"
# q = QEM(runs=conf.runs, user_id=conf.user_id, token=token)
# qasm_files = q.get_qasm_files_from_path("./circuits/polar_sim/n3/z")
# qasm_files = qasm_files
# print(qasm_files)
# # noise_levels = [0.1, 0.2, 0.4, 0.6, 0.8, 1.0]
# noise_levels = [0.0]
# shots = 10000
# q.set_backend(program_type="sampler", shots=shots)
# q.run_simulator("sampler", qasm_files, compilations, noise_levels, shots, send_to_db=True)

# # # Setup the object for n4
# q = None
# conf.triq_measurement_type = "polar_meas"
# q = QEM(runs=conf.runs, user_id=conf.user_id, token=token)
# qasm_files = q.get_qasm_files_from_path("./circuits/polar_sim/n4")
# qasm_files = qasm_files*4
# noise_levels = [0.1, 0.2, 0.4, 0.6, 0.8, 1.0]
# # noise_levels = [0.1]
# shots = 10
# q.set_backend(program_type="sampler", shots=shots)
# q.run_simulator("sampler", qasm_files, compilations, noise_levels, shots, send_to_db=True)

print("Get Result...")
q.get_qiskit_result()