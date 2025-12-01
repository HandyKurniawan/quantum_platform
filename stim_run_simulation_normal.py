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
# Define parameter grid
# -----------------------------
# n_values = [6]
# lstate_values = ["z"]
# # lstate_values = ["z"]
# # sim_type_values = ["normal", "m1", "m2"]
# sim_type_values = ["m2"]
# p_error_values = [0.001]
# # p_error_values = [0.01, 0.001]
# # i_values = [8,12,14,15,20,22,23,25,26,27,36,38,39,42,43,45,50,51,53]
# i_values = [45, 50, 51, 53]
# # i_values = range(2, (2**n_values[0])+1)
# shots_values = [int(1e6)]
# seed_starts_values = [100]

# token = "23OwipXqZzd8plKZR2LDMK-peWuU74UQAyjAhMIaFHCM"
# QiskitRuntimeService.save_account(channel="ibm_quantum_platform", token=token, instance="free", overwrite=True)
# service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token, instance="free")

# -----------------------------
# Worker function
# -----------------------------
def run_simulation(args):
    n, lstate, sim_type, p_error, i, shots, seed = args
    print(f"Starting: n={n}, lstate={lstate}, sim_type={sim_type}, p_error={p_error}, i={i}, shots={shots}")
    result = simulate_batch_and_save_result_polar_normal(n, lstate, sim_type, p_error, i, shots, seed)

    save_results_to_csv(result, filename=f"./output/STIM/normal/n{n}_result/polar_results_json_normal_{seed}.csv")
    # print(f"Finished: n={n}, lstate={lstate}, sim_type={sim_type}, p_error={p_error}, i={i}, shots={shots}")
    # return result

def run_all(lstate_values, sim_type_values, n_values, p_error_values, i_values, shots_values):
    
    seed_values = [random.randint(1, 99999999)]

    param_grid = list(itertools.product(
        n_values,
        lstate_values,
        sim_type_values,
        p_error_values,
        i_values,
        shots_values,
        seed_values,
    ))

    max_workers = 10  # Adjust to your CPU
    # results = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        executor.map(run_simulation, param_grid)

    print(f"✅ All simulations finished data)!")

    # for sim_type in sim_type_values:
    #     for p_error in p_error_values:

    # param_grid = list(itertools.product(
    #     n_values,
    #     lstate_values,
    #     i_values,
    #     # [p_error],
    #     p_error_values,
    #     # [sim_type],
    #     sim_type_values,
    #     seed_values,
    # ))

    # results = []
    # with ProcessPoolExecutor(max_workers=max_workers) as executor:
    #     for res in executor.map(wrapper, param_grid):
    #         if res is not None:
    #             results.append(res)

    # save_results_to_csv(results, filename=f"./output/STIM/normal/polar_results_json_normal_{seed_values[0]}.csv")
    # print(f"✅ Results saved to polar_results_json_normal.csv")

    # find_and_delete_files(f"./output/STIM/normal/n{n_values[0]}/*{seed_values[0]}.json")
# -----------------------------
# Parallel execution
# -----------------------------
if __name__ == "__main__":
    pass

    lstate_values = ["x"]
    sim_type_values = ["normal"]
    # sim_type_values = ["normal", "m1"]
    n_values = [4]
    # p_error_values = [0.01, 0.005]
    # # i_values = [4]
    # i_values = range(2, (2**n_values[0]))
    # shots_values = [int(1e5)]

    # p_error_values = [0.01, 0.005, 0.001, 0.0005, 0.0001]
    p_error_values = [0.001]
    # i_values = range(2, (2**n_values[0]))
    i_values = [2]
    shots_values = [int(1e7)]
    
    for _ in range(10000):
        run_all(lstate_values, sim_type_values, n_values, p_error_values, i_values, shots_values)
    
    # for i in range(1000):
    #     lstate_values = ["z"]
    #     sim_type_values = ["normal"]
    #     n_values = [4]
    #     p_error_values = [0.01]
    #     i_values = [16]
    #     shots_values = [int(5e6)]

    #     run_all(lstate_values, sim_type_values, n_values, p_error_values, i_values, shots_values)

    # for i in range(50):
    #     lstate_values = ["z"]
    #     sim_type_values = ["normal", "m1"]
    #     n_values = [4]
    #     p_error_values = [0.005]
    #     i_values = [12, 14, 15]
    #     shots_values = [int(2e6)]

    #     run_all(lstate_values, sim_type_values, n_values, p_error_values, i_values, shots_values)

    # for i in range(50):
    #     lstate_values = ["z"]
    #     sim_type_values = ["normal", "m1"]
    #     n_values = [4]
    #     p_error_values = [0.001]
    #     i_values = [8, 12, 14, 15]
    #     shots_values = [int(2e6)]

    #     run_all(lstate_values, sim_type_values, n_values, p_error_values, i_values, shots_values)

    # for i in range(100):
    #     lstate_values = ["x"]
    #     sim_type_values = ["normal", "m1"]
    #     n_values = [5]
    #     p_error_values = [0.01]
    #     i_values = [2, 3, 5, 9, 17]
    #     shots_values = [int(1e6)]

    #     run_all(lstate_values, sim_type_values, n_values, p_error_values, i_values, shots_values)

    # for i in range(100):
    #     lstate_values = ["x"]
    #     sim_type_values = ["normal", "m1"]
    #     n_values = [5]
    #     p_error_values = [0.005]
    #     i_values = [2, 3, 5, 9, 17]
    #     shots_values = [int(1e6)]

    #     run_all(lstate_values, sim_type_values, n_values, p_error_values, i_values, shots_values)

    # for i in range(100):
    #     lstate_values = ["x"]
    #     sim_type_values = ["normal", "m1"]
    #     n_values = [5]
    #     p_error_values = [0.01, 0.005]
    #     i_values = [9, 17]
    #     shots_values = [int(1e6)]

    #     run_all(lstate_values, sim_type_values, n_values, p_error_values, i_values, shots_values)

    # for i in range(50):
    #     lstate_values = ["x"]
    #     sim_type_values = ["normal", "m1"]
    #     n_values = [4]
    #     p_error_values = [0.001]
    #     i_values = [2, 3, 5, 9, 17]
    #     shots_values = [int(1e6)]

    #     run_all(lstate_values, sim_type_values, n_values, p_error_values, i_values, shots_values)

    