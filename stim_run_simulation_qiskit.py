import itertools
import logging
import random
from concurrent.futures import ProcessPoolExecutor
from wrappers.polar_wrapper import (
    polar_code_p2, get_logical_error_on_accepted_states, divide_half_list
)
from wrappers.stim_wrapper import (
    calculate_logical_error_result_polar_qiskit,
    simulate_batch_and_save_result_polar_qiskit,
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
    return calculate_logical_error_result_polar_qiskit(*args)

token = "23OwipXqZzd8plKZR2LDMK-peWuU74UQAyjAhMIaFHCM"
QiskitRuntimeService.save_account(channel="ibm_quantum_platform", token=token, instance="free", overwrite=True)
service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token, instance="free")

# -----------------------------
# Worker function
# -----------------------------
def run_simulation(args):
    n, lstate, sim_type, p_error, i, shots, seed, hw_name = args
    print(f"Starting: n={n}, lstate={lstate}, sim_type={sim_type}, p_error={p_error}, i={i}, shots={shots}, hw_name={hw_name}")
    
    backend = service.backend(hw_name)

    result = simulate_batch_and_save_result_polar_qiskit(n, lstate, sim_type, p_error, i, shots, seed, backend)
    print(f"Finished: n={n}, lstate={lstate}, sim_type={sim_type}, p_error={p_error}, i={i}, shots={shots}, hw_name={hw_name}")
    return result

def run_all(lstate_values, sim_type_values, n_values, p_error_values, i_values, shots_values, hw_name_values):
    
    seed_values = [random.randint(1, 9999999)]

    param_grid = list(itertools.product(
        n_values,
        lstate_values,
        sim_type_values,
        p_error_values,
        i_values,
        shots_values,
        seed_values,
        hw_name_values
    ))



    max_workers = 10  # Adjust to your CPU
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        list(executor.map(run_simulation, param_grid))

    print("✅ All simulations finished!")

    for hw_name in hw_name_values:
        for sim_type in sim_type_values:
            for p_error in p_error_values:

                param_grid = list(itertools.product(
                    n_values,
                    lstate_values,
                    i_values,
                    [p_error],
                    [sim_type],
                    hw_name_values
                ))

                results = []
                with ProcessPoolExecutor(max_workers=10) as executor:
                    for res in executor.map(wrapper, param_grid):
                        if res is not None:
                            results.append(res)

                save_results_to_csv(results, filename=f"./output/STIM/qiskit/{hw_name}_polar_results_json_qiskit.csv")
                print(f"✅ Results saved to polar_results_json_qiskit.csv")
# -----------------------------
# Parallel execution
# -----------------------------
if __name__ == "__main__":
    pass

    lstate_values = ["x", "z"]
    sim_type_values = ["normal", "m1"]
    n_values = [3]
    # p_error_values = [0.01, 0.005, 0.001, 0.0005, 0.0001]
    p_error_values = [1, 0.1, 0.5, 0.05, 0.01]
    # i_values = [4, 5]
    i_values = range(2, (2**n_values[0]))
    shots_values = [int(1e7)]
    hw_name_values = ["ibm_brisbane"]
    # hw_name_values = ["ibm_torino"]

    # run_all(lstate_values, sim_type_values, n_values, p_error_values, i_values, shots_values, hw_name_values)

    # lstate_values = ["x"]
    # n_values = [4]
    # p_error_values = [1, 0.1, 0.5, 0.05, 0.01]
    # i_values = range(2, (2**n_values[0]))
    # shots_values = [int(5e6)]

    # run_all(lstate_values, sim_type_values, n_values, p_error_values, i_values, shots_values, hw_name_values)

    # lstate_values = ["z"]
    # n_values = [4]
    # p_error_values = [1, 0.1, 0.5, 0.05, 0.01]
    # i_values = range(2, (2**n_values[0]))
    # shots_values = [int(5e6)]

    # run_all(lstate_values, sim_type_values, n_values, p_error_values, i_values, shots_values, hw_name_values)

    lstate_values = ["x"]
    n_values = [5]
    p_error_values = [1, 0.1, 0.01]
    i_values = [2, 5, 6, 7, 9, 13, 17]
    shots_values = [int(5e6)]

    run_all(lstate_values, sim_type_values, n_values, p_error_values, i_values, shots_values, hw_name_values)

    # lstate_values = ["z"]
    # n_values = [5]
    # p_error_values = [1, 0.1, 0.01]
    # i_values = [16, 24, 28, 31]
    # shots_values = [int(5e6)]

    # run_all(lstate_values, sim_type_values, n_values, p_error_values, i_values, shots_values, hw_name_values)