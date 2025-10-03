import itertools
import logging
import random
from concurrent.futures import ProcessPoolExecutor
from wrappers.polar_wrapper import (
    polar_code_p2, get_logical_error_on_accepted_states, divide_half_list
)
from wrappers.stim_wrapper import (
    calculate_logical_error_result_polar,
    simulate_batch_and_save_result_polar,
    generate_qiskit_polar_code, compiled_to_qiskit_hardware
)

import pandas as pd
import os

from qiskit_ibm_runtime import QiskitRuntimeService


def save_results_to_csv(results, filename="polar_results.csv"):
    df = pd.DataFrame(results)
    if os.path.exists(filename):
        # Append without rewriting header
        df.to_csv(filename, mode="a", header=False, index=False)
    else:
        df.to_csv(filename, index=False)

def wrapper(args):
    return calculate_logical_error_result_polar(*args)

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

token = "23OwipXqZzd8plKZR2LDMK-peWuU74UQAyjAhMIaFHCM"
QiskitRuntimeService.save_account(channel="ibm_quantum_platform", token=token, instance="free", overwrite=True)
service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token, instance="free")

# -----------------------------
# Worker function
# -----------------------------
def run_simulation(args):
    n, lstate, sim_type, p_error, i, shots, seed_starts, hw_name, seed_transpiler = args
    logging.info(f"Starting: n={n}, lstate={lstate}, sim_type={sim_type}, p_error={p_error}, i={i}, shots={shots}")

    if hw_name != None:
        backend = service.backend(hw_name)
        qc = generate_qiskit_polar_code(n, lstate, sim_type, i)
        tqc = compiled_to_qiskit_hardware(qc, backend, 3, seed_transpiler)
        initial_layout = tqc.layout.initial_index_layout(filter_ancillas=True)
        print(hw_name, seed_transpiler, initial_layout)
    else:
        backend = None
        initial_layout = None

    result = simulate_batch_and_save_result_polar(n, lstate, sim_type, p_error, i, shots, seed_starts, backend=backend, initial_layout=initial_layout)
    logging.info(f"Finished: n={n}, lstate={lstate}, sim_type={sim_type}, p_error={p_error}, i={i}, shots={shots}")
    return result

def run_all(lstate_values, sim_type_values, n_values, p_error_values, i_values, shots_values, hw_name_values):
    
    # shots_values = [int(1e3)]
    seed_starts_values = [100]
    seed_transpiler_values = [random.randint(1, 9999999)]
    # hw_name_values = ["ibm_torino"]

    param_grid = list(itertools.product(
        n_values,
        lstate_values,
        sim_type_values,
        p_error_values,
        i_values,
        shots_values,
        seed_starts_values,
        hw_name_values,
        seed_transpiler_values
    ))

    max_workers = 10  # Adjust to your CPU
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        list(executor.map(run_simulation, param_grid))

    logging.info("✅ All simulations finished!")

    for hw_name in hw_name_values:
        for sim_type in sim_type_values:

            param_grid = list(itertools.product(
                n_values,
                lstate_values,
                i_values,
                p_error_values,
                [sim_type],
                shots_values,
                hw_name_values
            ))

            results = []
            with ProcessPoolExecutor(max_workers=10) as executor:
                for res in executor.map(wrapper, param_grid):
                    if res is not None:
                        results.append(res)

            save_results_to_csv(results, filename=f"./output/STIM/{hw_name}_polar_results_json.csv")
            print(f"✅ Results saved to {hw_name}_polar_results_json.csv")

# -----------------------------
# Parallel execution
# -----------------------------
if __name__ == "__main__":
    lstate_values = ["x", "z"]
    sim_type_values = ["normal", "m1", "m2"]
    n_values = [3]
    p_error_values = [0.01]
    # i_values = [4]
    i_values = range(2, (2**n_values[0])+1)
    shots_values = [int(1e5)]
    hw_name_values = ["ibm_torino"]

    run_all(lstate_values, sim_type_values, n_values, p_error_values, i_values, shots_values, hw_name_values)

    # n_values = [4]
    # p_error_values = [0.01, 0.001]
    # i_values = [4,6,7,13]

    # run_all(n_values, p_error_values, i_values)

    # n_values = [5]
    # p_error_values = [0.01, 0.001]
    # i_values = [8, 21]

    # run_all(n_values, p_error_values, i_values)

    # n_values = [6]
    # p_error_values = [0.001]
    # i_values = [8, 25]

    # run_all(n_values, p_error_values, i_values)


    # lstate_values = ["x"]
    # sim_type_values = ["normal", "m1", "m2"]
    # shots_values = [int(1e4)]
    # seed_starts_values = [100]

    # n_values = [3]
    # p_error_values = [0.001]
    # i_values = [4]

    # param_grid = list(itertools.product(
    #     n_values,
    #     lstate_values,
    #     sim_type_values,
    #     p_error_values,
    #     i_values,
    #     shots_values,
    #     seed_starts_values
    # ))

    # max_workers = 10  # Adjust to your CPU
    # with ProcessPoolExecutor(max_workers=max_workers) as executor:
    #     list(executor.map(run_simulation, param_grid))

    # logging.info("✅ All simulations finished!")

    # for sim_type in sim_type_values:

    #     param_grid = list(itertools.product(
    #         n_values,
    #         lstate_values,
    #         i_values,
    #         p_error_values,
    #         [sim_type],
    #         shots_values
    #     ))

    #     results = []
    #     with ProcessPoolExecutor(max_workers=10) as executor:
    #         for res in executor.map(wrapper, param_grid):
    #             if res is not None:
    #                 results.append(res)

    #     save_results_to_csv(results, filename="./output/STIM/polar_results_json.csv")
    #     print("✅ Results saved to polar_results_json.csv")

