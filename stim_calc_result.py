import itertools
import logging
from concurrent.futures import ProcessPoolExecutor
from wrappers.polar_wrapper import (
    polar_code_p2, get_logical_error_on_accepted_states, divide_half_list
)
from wrappers.stim_wrapper import (
    convert_i_to_meas_type, generate_circuit_extraction_syndrome_stim, calculate_logical_error_result_polar,
    simulate_stim_polar_code, noisy_cx, noisy_h, noisy_x, noisy_z,
    noisy_reset, noisy_measurement, simulate_batch_and_save_result_polar
)

import pandas as pd
import os

def save_results_to_csv(results, filename="polar_results.csv"):
    df = pd.DataFrame(results)
    if os.path.exists(filename):
        # Append without rewriting header
        df.to_csv(filename, mode="a", header=False, index=False)
    else:
        df.to_csv(filename, index=False)

def wrapper(args):
    return calculate_logical_error_result_polar(*args)

if __name__ == "__main__":
    # -----------------------------
    # Define parameter grid
    # -----------------------------
    # n_values = [4]
    # # lstate_values = ["x", "z"]
    # lstate_values = ["x"]
    # # p_error_values = [0.01, 0.005, 0.001, 0.0005, 0.0001]
    # p_error_values = [0.01]
    # i_values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
    # sim_type_values = ["normal", "m1"]

    
    n_values = [6]
    lstate_values = ["z"]
    # lstate_values = ["z"]
    sim_type_values = ["normal", "m1", "m2"]
# sim_type_values = ["normal", "m2"]
# p_error_values = [0.01, 0.005]
    p_error_values = [0.01, 0.001]
    i_values = [8,12,14,15,20,22,23,25,26,27,36,38,39,42,43,45,50,51,53]
# i_values = [4,5]
# i_values = range(2, (2**n_values[0])+1)
    shots_values = [int(11e5)]
    seed_starts_values = [100000]

    n_values = [3]
    lstate_values = ["x"]
    sim_type_values = ["normal", "m1"]
    p_error_values = [0.001]
    i_values = [3]
    shots_values = [int(1e5)]
    seed_starts_values = [100]

    for sim_type in sim_type_values:

        param_grid = list(itertools.product(
            n_values,
            lstate_values,
            i_values,
            p_error_values,
            [sim_type],
            shots_values
        ))

        results = []
        with ProcessPoolExecutor(max_workers=10) as executor:
            for res in executor.map(wrapper, param_grid):
                if res is not None:
                    results.append(res)

        save_results_to_csv(results, filename="./output/STIM/polar_results_test.csv")
        print("✅ Results saved to polar_results.csv")
