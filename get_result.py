# import sys, glob, os
# from commons import convert_to_json, triq_optimization, qiskit_optimization, \
#     calibration_type_enum, qiskit_compilation_enum, normalize_counts, calculate_success_rate_tvd, \
#     convert_dict_binary_to_int, convert_dict_int_to_binary, sum_last_n_digits_dict
# import wrappers.qiskit_wrapper as qiskit_wrapper
# from wrappers.qiskit_wrapper import QiskitCircuit
# import pandas as pd
# # import mthree
# import mapomatic as mm
# # import mthree

# from qiskit.quantum_info import SparsePauliOp
# from qiskit import QuantumCircuit
# from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
# from qiskit_ibm_runtime.options import SamplerOptions, EstimatorOptions, DynamicalDecouplingOptions, TwirlingOptions

# from qiskit_aer import AerSimulator, QasmSimulator, Aer
# from qiskit.qasm2 import dumps
# import matplotlib.pyplot as plt
# import numpy as np

# import mitiq
# from mitiq import zne, benchmarks

from qEmQUIP import QEM, conf
import os
import sys

module_path = os.path.abspath(os.path.join('.', 'wrappers'))
if module_path not in sys.path:
    sys.path.append(module_path)

token = "9e068d694502429634a4706a9f08781beac043c44af9642dfe89757093b049ba266b0ce9f488d4220d386114b5f785a518827881e0645b530203026ad7ab9d7e"

q = QEM(runs=conf.runs, user_id=conf.user_id, token=token)

print("Get Result Simulator...")
q.get_qiskit_result("simulator")

print("Get Result...")
q.get_qiskit_result("real")