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

token = "23OwipXqZzd8plKZR2LDMK-peWuU74UQAyjAhMIaFHCM"
QiskitRuntimeService.save_account(channel="ibm_quantum_platform", token=token, instance="free", overwrite=True)
service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token, instance="free")

def run_all(lstate_values, sim_type_values, n_values, p_error_values, i_values, shots_values, hw_name_values, accepted_target_count_values):
    
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
        seed_transpiler_values,
        accepted_target_count_values
    ))

    for hw_name in hw_name_values:
        for sim_type in sim_type_values:

            param_grid = list(itertools.product(
                n_values,
                lstate_values,
                i_values,
                p_error_values,
                [sim_type],
                shots_values,
                hw_name_values,
                accepted_target_count_values
            ))

            results = []
            with ProcessPoolExecutor(max_workers=10) as executor:
                for res in executor.map(wrapper, param_grid):
                    if res is not None:
                        results.append(res)

            if accepted_target_count_values[0] != None:
                suffix_path = "_accepted"

            if hw_name != None:
                save_results_to_csv(results, filename=f"./output/STIM/{hw_name}_polar_results_json{suffix_path}.csv")
                print(f"✅ Results saved to {hw_name}_polar_results_json{suffix_path}.csv")
            else:
                save_results_to_csv(results, filename=f"./output/STIM/polar_results_json{suffix_path}.csv")
                print(f"✅ Results saved to polar_results_json{suffix_path}.csv")

# -----------------------------
# Parallel execution
# -----------------------------
if __name__ == "__main__":
    lstate_values = ["x", "z"]
    # lstate_values = ["x"]
    sim_type_values = ["m1", "m2"]
    # sim_type_values = ["normal"]
    n_values = [3]
    p_error_values = [0.01, 0.001]
    # i_values = [2]
    i_values = range(2, (2**n_values[0])+1)
    shots_values = [int(1e6)]
    # hw_name_values = ["ibm_brisbane"]
    hw_name_values = [None]
    accepted_target_count_values = [1e6]

    run_all(lstate_values, sim_type_values, n_values, p_error_values, i_values, shots_values, hw_name_values, accepted_target_count_values)


   
