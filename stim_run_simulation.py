import itertools
import logging
from concurrent.futures import ProcessPoolExecutor
from wrappers.polar_wrapper import (
    polar_code_p2, get_logical_error_on_accepted_states, divide_half_list
)
from wrappers.stim_wrapper import (
    convert_i_to_meas_type, generate_circuit_extraction_syndrome_stim,
    simulate_stim_polar_code, noisy_cx, noisy_h, noisy_x, noisy_z,
    noisy_reset, noisy_measurement, simulate_batch_and_save_result_polar
)

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
n_values = [6]
# lstate_values = ["x", "z"]
lstate_values = ["z"]
# sim_type_values = ["normal", "m1", "m2"]
sim_type_values = ["normal", "m2"]
# p_error_values = [0.01, 0.005]
p_error_values = [0.01]
i_values = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16]
# i_values = range(2, (2**n_values[0])+1)
shots_values = [int(1e5)]

param_grid = list(itertools.product(
    n_values,
    lstate_values,
    sim_type_values,
    p_error_values,
    i_values,
    shots_values
))

# -----------------------------
# Worker function
# -----------------------------
def run_simulation(args):
    n, lstate, sim_type, p_error, i, shots = args
    logging.info(f"Starting: n={n}, lstate={lstate}, sim_type={sim_type}, p_error={p_error}, i={i}, shots={shots}")
    result = simulate_batch_and_save_result_polar(n, lstate, sim_type, p_error, i, shots)
    logging.info(f"Finished: n={n}, lstate={lstate}, sim_type={sim_type}, p_error={p_error}, i={i}, shots={shots}")
    return result

# -----------------------------
# Parallel execution
# -----------------------------
if __name__ == "__main__":
    max_workers = 10  # Adjust to your CPU
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        list(executor.map(run_simulation, param_grid))

    logging.info("✅ All simulations finished!")
