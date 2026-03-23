import itertools
import logging
import random
from concurrent.futures import ProcessPoolExecutor
from wrappers.polar_wrapper import (
    polar_code_p2, get_logical_error_on_accepted_states, divide_half_list,
    get_q1prep_accepted_states, get_logical_error_on_accepted_states_SCL
)
from wrappers.stim_wrapper import (
    simulate_stim_polar_code_normal,
    
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

n = 3
lstate = "z"
sim_type = "normal"
i = 7
p_error = 0
shots = 1e1
seed = 12345

zpos_list = [-1, -1, 1, 3, 6, 7, 22, 15, 90, 31, 362]
zpos_list[n] = i-1

results = simulate_stim_polar_code_normal(n, lstate, sim_type, i, p_error, shots, seed)

# flipped_results = {bit_str[::-1]: count for bit_str, count in results.items()}
sum(results.values())

get_logical_error_on_accepted_states(n, lstate.upper(), results, zpos_list)