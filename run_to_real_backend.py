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

# token = "476ea8c61cc54f36e4a21d70a8442f94203c9d87096eaad0886a3e8154d8c2e79bcad6f927c6050a76335dd68d783f478c1b828504748a4377b441c335c831aa"

def update_hardware_configs(hw_name):
    token = qiskit_wrapper.get_active_token(100, 0, 1)[0][0]
    print(token)

    conf.hardware_name = hw_name
    conf.user_id=6
    q = QEM(runs=conf.runs, user_id=conf.user_id, token=token, hw_name=hw_name)
    conf.user_id=6
    conf.hardware_name = hw_name
    conf.triq_measurement_type = "polar_meas"
    
    # update TriQ configs from calibration data
    q.update_hardware_configs(hw_name=hw_name)

    # # update IBM FakeBackend configuration
    # shots = 1000
    # q.set_backend(program_type="sampler", shots=shots)
    # qiskit_wrapper.generate_new_props(q.backend, "avg")
    # qiskit_wrapper.generate_new_props(q.backend, "mix")
    # qiskit_wrapper.generate_new_props(q.backend, "recent_15_adjust")

def run_simulation_one(hw_name, noise_levels, file_path, compilations, triq_measurement_type, repeat,
                       shots ):
    token = qiskit_wrapper.get_active_token(100, 0, 1)[0][0]
    print(token)

    conf.hardware_name = hw_name
    conf.triq_measurement_type = triq_measurement_type
    conf.user_id=6
    q = QEM(runs=conf.runs, user_id=conf.user_id, token=token, hw_name=hw_name)
    conf.user_id=6
    conf.triq_measurement_type = triq_measurement_type
    conf.hardware_name = hw_name
    qasm_files = q.get_qasm_files_from_path(file_path)
    qasm_files = qasm_files*repeat
    print(qasm_files)
    
    q.set_backend(program_type="sampler", shots=shots)
    # q.run_simulator("sampler", qasm_files, compilations, noise_levels, shots, hardware_name=hw_name, send_to_db=True)
    
    dd_options: DynamicalDecouplingOptions = {
    'enable':True, 
#    'sequence_type':'XpXm',
    'sequence_type':'XY4',
    'scheduling_method': 'alap'
} 

    # q.send_to_real_backend("sampler", qasm_files, compilations, hardware_name=hw_name, shots=shots, dd_options = dd_options)

    q.send_to_real_backend("sampler", qasm_files, compilations, hardware_name=hw_name, shots=shots)

    qiskit_wrapper.update_qiskit_usage_info(token)



def run_simulation_all(hw_name, shots = 200):
    

    update_hardware_configs(hw_name=hw_name)
    

    noise_levels = [0.1, 0.2, 0.4, 0.6, 0.8, 1.0]

    # # #region n2
    # Setup the object for n2_x
    run_simulation_one(hw_name, noise_levels, file_path="./circuits/polar_sim/n2/x", 
                       compilations=["qiskit_3", "triq_avg_sabre", "triq_lcd_sabre"], triq_measurement_type="polar_meas", 
                       repeat=1, shots=20000 )

    # Setup the object for n2_z
    run_simulation_one(hw_name, noise_levels, file_path="./circuits/polar_sim/n2/z", 
                       compilations=["triq_lcd_sabre", "triq_avg_sabre"], triq_measurement_type="polar_mix", 
                       repeat=1, shots=20000 )
    
    # Setup the object for n2_z_qiskit
    run_simulation_one(hw_name, noise_levels, file_path="./circuits/polar_sim/n2/z_qiskit", 
                       compilations=["qiskit_3"], triq_measurement_type="polar_meas", 
                       repeat=1, shots=20000 )

    #end region n2

    # #region n3
    # Setup the object for n3_x
    run_simulation_one(hw_name, noise_levels, file_path="./circuits/polar_sim/n3/x", 
                       compilations=["qiskit_3", "triq_avg_sabre", "triq_lcd_sabre"], triq_measurement_type="polar_meas", 
                       repeat=1, shots=10000 )

    # Setup the object for n3_z
    run_simulation_one(hw_name, noise_levels, file_path="./circuits/polar_sim/n3/z", 
                       compilations=["triq_lcd_sabre", "triq_avg_sabre"], triq_measurement_type="polar_mix", 
                       repeat=1, shots=10000 )
    
    # Setup the object for n3_z_qiskit
    run_simulation_one(hw_name, noise_levels, file_path="./circuits/polar_sim/n3/z_qiskit", 
                       compilations=["qiskit_3"], triq_measurement_type="polar_meas", 
                       repeat=1, shots=10000 )

    # #endregion n3

    # #region n4

    # # Setup the object for n4
    run_simulation_one(hw_name, noise_levels, file_path="./circuits/polar_sim/n4/x", 
                       compilations=["qiskit_3"], triq_measurement_type="polar_meas", 
                       repeat=1, shots=shots )
    
    run_simulation_one(hw_name, noise_levels, file_path="./circuits/polar_sim/n4/x", 
                       compilations=["triq_lcd_sabre"], triq_measurement_type="polar_meas", 
                       repeat=1, shots=shots )
    
    run_simulation_one(hw_name, noise_levels, file_path="./circuits/polar_sim/n4/x", 
                       compilations=["triq_avg_sabre"], triq_measurement_type="polar_meas", 
                       repeat=1, shots=shots )
    
    run_simulation_one(hw_name, noise_levels, file_path="./circuits/polar_sim/n4/z", 
                       compilations=["qiskit_3"], triq_measurement_type="polar_meas", 
                       repeat=1, shots=shots )
    
    run_simulation_one(hw_name, noise_levels, file_path="./circuits/polar_sim/n4/z", 
                       compilations=["triq_lcd_sabre"], triq_measurement_type="polar_meas", 
                       repeat=1, shots=shots )
    
    run_simulation_one(hw_name, noise_levels, file_path="./circuits/polar_sim/n4/z", 
                       compilations=["triq_avg_sabre"], triq_measurement_type="polar_meas", 
                       repeat=1, shots=shots )

    # #endregion n4

    # print("Get Result...")
    # q.get_qiskit_result()

try:
    # run_simulation_all("ibm_brisbane")
    pass

except Exception as e:
    print(f"An error occurred: {str(e)}. Will try again in 30 seconds...")

try:
    run_simulation_all("ibm_sherbrooke", 4000)
    pass

except Exception as e:
    print(f"An error occurred: {str(e)}. Will try again in 30 seconds...")


token = qiskit_wrapper.get_active_token(100, 0, 1)[0][0]
print(token)
q = QEM(runs=conf.runs, user_id=conf.user_id, token=token)

# print("Get Result...")
# q.get_qiskit_result("real")