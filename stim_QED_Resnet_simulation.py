import itertools
import logging
import random
from concurrent.futures import ProcessPoolExecutor
from wrappers.polar_wrapper import (
    polar_code_p2, get_logical_error_on_accepted_states, divide_half_list
)
from wrappers.stim_wrapper import (
    calculate_logical_error_result_polar_normal,
    simulate_batch_and_save_result_polar_normal,
    simulate_batch_and_save_result_polar_normal_update,
    generate_qiskit_polar_code, compiled_to_qiskit_hardware,
    find_and_delete_files
)

import pandas as pd
import os
import glob
import sys

from qiskit_ibm_runtime import QiskitRuntimeService


def save_results_to_csv(results, filename="polar_results.csv"):
    df = pd.DataFrame([results])
    if os.path.exists(filename):
        # Append without rewriting header
        df.to_csv(filename, mode="a", header=False, index=False)
    else:
        df.to_csv(filename, index=False)

def wrapper(args):
    return calculate_logical_error_result_polar_normal(*args)

# -----------------------------
# Setup logging
# -----------------------------
logging.basicConfig(
    filename="simulation.log",       # log file name
    filemode="a",                    # append mode
    level=logging.INFO,              # log level
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# -----------------------------
# Worker function
# -----------------------------
def run_simulation(args):
    n, lstate, sim_type, p_error, i, shots, seed, decoder = args
    print(f"Starting: n={n}, lstate={lstate}, sim_type={sim_type}, p_error={p_error}, i={i}, shots={shots}, decoder={decoder}")

    if sim_type == "m3":
        result = simulate_batch_and_save_result_polar_normal_update(n, lstate, sim_type, p_error, i, shots, seed, decoder)
    else:
        result = simulate_batch_and_save_result_polar_normal(n, lstate, sim_type, p_error, i, shots, seed, decoder)

    # save_results_to_csv(result, filename=f"./output/STIM/normal/n{n}_result/polar_results_json_normal_{seed}.csv")
    save_results_to_csv(result, filename=f"./output/STIM/clean/n{n}_result/polar_results_json_normal_{seed}.csv")
    # print(f"Finished: n={n}, lstate={lstate}, sim_type={sim_type}, p_error={p_error}, i={i}, shots={shots}")
    # return result

def run_all(lstate_values, sim_type_values, n_values, p_error_values, i_values, shots_values, decoder_values):
    
    seed_values = [random.randint(1, 99999999)]

    param_grid = list(itertools.product(
        n_values,
        lstate_values,
        sim_type_values,
        p_error_values,
        i_values,
        shots_values,
        seed_values,
        decoder_values
    ))

    max_workers = 12 # Adjust to your CPU
    # results = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        executor.map(run_simulation, param_grid)

    print(f"✅ All simulations finished data)!")

# -----------------------------
# Parallel execution
# -----------------------------
if __name__ == "__main__":
    pass

    shots_values = [int(1e3)]
    sim_type_values = ["m3"]
    n_values = [4]
    # p_error_values = [0.01, 0.0075, 0.005, 0.0025, 0.001]
    p_error_values = [0]
    lstate_values = ["z"]
    i_values = [5]
    # i_values = [9]

    decoder_values = ["val", "anqi"]
    
    for _ in range(1):
        run_all(lstate_values, sim_type_values, n_values, p_error_values, i_values, shots_values, decoder_values)
    