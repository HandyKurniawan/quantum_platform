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
    df = pd.DataFrame([results])
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
    n, lstate, sim_type, p_error, i, shots, seed, hw_name, seed_transpiler, target_accept_count, comp_type = args
    print(f"Starting: n={n}, lstate={lstate}, sim_type={sim_type}, p_error={p_error}, i={i}, shots={shots}, seed_starts={seed}, hw_name={hw_name}, seed_transpiler={seed_transpiler}, target_accept_count={target_accept_count}, comp_type={comp_type}")

    if hw_name != None:
        backend = service.backend(hw_name)
        # qc = generate_qiskit_polar_code(n, lstate, sim_type, i)
        # tqc = compiled_to_qiskit_hardware(qc, backend, 3, seed_transpiler)
        # initial_layout = tqc.layout.initial_index_layout(filter_ancillas=True)
        # print(hw_name, seed_transpiler, initial_layout)

        initial_layout = None
    else:
        backend = None
        initial_layout = None

    result = simulate_batch_and_save_result_polar(n, lstate, sim_type, p_error, i, shots, seed, backend=backend, initial_layout=initial_layout,
                                                  target_accept_count=target_accept_count, comp_type=comp_type)
    suffix_path = ""
    # if target_accept_count != None:
    #     suffix_path = "_accepted"

    hardware_path = ""
    if hw_name != None:
        hardware_path = f"{hw_name}_"

    # if hw_name != None:
    #     save_results_to_csv(result, filename=f"./output/STIM/{hw_name}_polar_results_json{suffix_path}.csv")
    #     print(f"✅ Results saved to {hw_name}_polar_results_json{suffix_path}.csv")
    # else:
    #     print(f"✅ Results saved to polar_results_json{suffix_path}.csv")
    #     save_results_to_csv(result, filename=f"./output/STIM/polar_results_json{suffix_path}.csv")
    #     # print(f"✅ Results saved to polar_results_json{suffix_path}.csv")

    print(f"✅ Results saved to polar_results_json.csv")
    save_results_to_csv(result, filename=f"./output/STIM/{hardware_path}prop-3_result/{hardware_path}polar_results_json_{seed}.csv")

    # logging.info(f"Finished: n={n}, lstate={lstate}, sim_type={sim_type}, p_error={p_error}, i={i}, shots={shots}, seed_starts={seed_starts}, hw_name={hw_name}, seed_transpiler={seed_transpiler}, target_accept_count={target_accept_count}")
    # return result

def run_all(lstate_values, sim_type_values, n_values, p_error_values, i_values, shots_values, hw_name_values, accepted_target_count_values, comp_type_values):
    
    # shots_values = [int(1e3)]
    seed_starts_values = [random.randint(1, 99999999)]
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
        seed_transpiler_values,
        accepted_target_count_values,
        comp_type_values
    ))

    max_workers = 10  # Adjust to your CPU
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        list(executor.map(run_simulation, param_grid))

    logging.info("✅ All simulations finished!")

# -----------------------------
# Parallel execution
# -----------------------------
if __name__ == "__main__":
    pass

    lstate_values = ["x"]
    sim_type_values = ["m2"]
    n_values = [4]
    p_error_values = [1, 0.8, 0.5, 0.3, 0.1]
    # p_error_values = [0]
    i_values = [2, 3]
    # i_values = [9]
    # i_values = range(2, (2**n_values[0])+1)
    shots_values = [int(5e4)]
    hw_name_values = ["ibm_marrakesh"]
    # hw_name_values = [None]
    accepted_target_count_values = [None]
    comp_type_values = ["na"]

    for _ in range(100000):
        run_all(lstate_values, sim_type_values, n_values, p_error_values, i_values, shots_values, hw_name_values, accepted_target_count_values, comp_type_values)

