import itertools
import logging
import random
from concurrent.futures import ProcessPoolExecutor
from wrappers.polar_wrapper import (
    polar_code_p2, get_logical_error_on_accepted_states, divide_half_list,
    get_q1prep_accepted_states, get_logical_error_on_accepted_states_SCL,
)
from wrappers.stim_wrapper import (
    simulate_stim_polar_code_normal,
    simulate_stim_polar_code_normal_from_qiskit_circuit,
    calculate_logical_error_result_polar_normal,
    simulate_batch_and_save_result_polar_normal,
    generate_qiskit_polar_code, compiled_to_qiskit_hardware,
    find_and_delete_files
)

import pandas as pd
import os
import glob
import sys

from qiskit_ibm_runtime import QiskitRuntimeService

import collections
import numpy as np

# Import your compiled Cython wrappers
from Encoders.polar import PyEncoderPolar
# Adjust the import below if your Decoder wrapper class is named differently
from Decoders.SCL import PyDecoderPolarSCL 

# --- Your Setup ---
# n = 5
# lstate = "z"
# sim_type = "m1"
# i = 2
# # i = 7
# p_error = 0.001
# shots = 1e1
# seed = 1234
# K = 1
# L = 4

token = "9zsMDJr2D381yK6A2fmx2Aqq4mnVaD9RA0Uh49It39UF"
QiskitRuntimeService.save_account(channel="ibm_quantum_platform", token=token, instance="free", overwrite=True)
service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token, instance="free")



def call_experiment(n, lstate, sim_type, i, p_error, shots, seed, K, L, hw_name, comp_type = "na"):

    backend = service.backend(hw_name)

    N = 2**n  

    zpos_list = [-1, -1, 1, 3, 6, 7, 22, 15, 90, 31, 362]
    zpos_list[n] = i-1

    # if p_zpos == None:
    if lstate.upper() == "Z":
        zpos = zpos_list[n]
    elif lstate.upper() == "X":
        zpos = zpos_list[n]
    # else:
    #     zpos = p_zpos

    # 2. Create a mask of ALL Trues (all frozen)
    frozen_bits_mask = np.ones(N, dtype=np.int32)

    # 3. Punch a hole EXACTLY at zpos for the info bit
    frozen_bits_mask[zpos] = 0
    # frozen_bits_mask[zpos:] = 0
    frozen_bits_mask = list(frozen_bits_mask)
    # frozen_bits_mask[N-1-zpos] = 1

    print(frozen_bits_mask)

    

    
    # accepted_states, data_qubit_states = get_q1prep_accepted_states(n, lstate, results, zpos_list)

    # Initialize the decoder
    decoder = PyDecoderPolarSCL(K, N, L, frozen_bits_mask)

    results = simulate_stim_polar_code_normal_from_qiskit_circuit(n, lstate, sim_type, i, p_error, shots, seed, backend, comp_type)
    count_accept, count_logerror, count_undecided, ler, _, _ = get_logical_error_on_accepted_states(n, lstate.upper(), results, zpos_list)
    count_accept_m1, count_logerror_m1, count_undecided_m1, ler_m1, _, _ = get_logical_error_on_accepted_states_SCL(n, lstate.upper(), results, decoder, p_error, zpos_list)

    print(count_accept, count_logerror, count_undecided, 1-ler)
    print(count_accept_m1, count_logerror_m1, count_undecided_m1, 1-ler_m1)

n = 4
lstate = 'x'
i = 3
# i = 7
# i = 15
p_error = 1
shots = 50000
# seed = 10000
seed = random.randint(1, 99999999)
K = 1
L = 1

sim_type = "normal"
print("Normal")
call_experiment(n, lstate, sim_type, i, p_error, shots, seed, K, L, "ibm_marrakesh")

sim_type = "m1"
print("M1")
call_experiment(n, lstate, sim_type, i, p_error, shots, seed, K, L, "ibm_marrakesh")