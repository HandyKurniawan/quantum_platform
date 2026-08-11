import time
import torch
import numpy as np
from wrappers.nn_wrapper import run_simulation, ScalablePolarQED
from wrappers.polar_wrapper import (is_q1prep_accepted, get_logical_error_on_accepted_states, 
                                    get_q1prep_accepted_states)
from wrappers.stim_wrapper import (create_circuit_polar_stim_normal, convert_i_to_meas_type, 
simulate_batch_and_save_result_polar_normal)

# Import your defined model class and the orchestrator function
# from model_architecture import ScalablePolarQED # Replace with your actual model class import
# from simulation_module import run_simulation  # Replace with your actual module import

def main():
    # ---------------------------------------------------------
    # 1. FIXED SIMULATION PARAMETERS
    # ---------------------------------------------------------
    n = 4  # Code length N = 2^4 = 16
    i = 7
    lstate_list = ["x", "z"]
    sim_type_list = ["normal", "m1"]

    # Physical Channel Error Rates
    p_error_list = [0.01, 0.0075, 0.005, 0.0025, 0.001]

    # NN Acceptance Decision Thresholds (Theta Sweep)
    prob_thresholds = np.linspace(0.05, 0.95, 19)

    # Training & Hardware Parameters
    train_shots = int(1e4)  # Cast to integer (100,000)
    test_shots = int(1e3)   # Cast to integer (10,000)
    batch_size = 1024
    adam_lr = 0.0001
    current_epochs = 0
    target_epochs = 10

    # Device Setup (CUDA GPU with fallback to CPU)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[SYSTEM] Using device: {device}")
    if device.type == "cuda":
        print(f"[SYSTEM] GPU Name: {torch.cuda.get_device_name(0)}")

    # ---------------------------------------------------------
    # 2. MASTER EXECUTION LOOP
    # ---------------------------------------------------------
    total_start_time = time.perf_counter()
    completed_runs = 0
    total_runs = len(lstate_list) * len(sim_type_list)

    for lstate in lstate_list:
        for sim_type in sim_type_list:
            completed_runs += 1
            print("\n" + "#" * 65)
            print(f"   STARTING RUN {completed_runs}/{total_runs} | lstate: '{lstate}' | sim_type: '{sim_type}'")
            print("#" * 65 + "\n")

            meas_type = convert_i_to_meas_type(i, n, lstate)
            x_ind = 0
            for idx, m_type in enumerate(meas_type):
                if m_type == "x":
                    x_ind = idx
                    break

            # 2. Set weight seed for reproducible initialization (optional)
            torch.manual_seed(42)

            # 3. Instantiate a fresh model and move to target device
            model = ScalablePolarQED(
                n=n, 
                x_ind=x_ind, 
                sim_type=sim_type, 
                include_data_bits=False
            ).to(device)

            run_start_time = time.perf_counter()

            # Execute full pipeline
            results, csv_path = run_simulation(
                n=n,
                i=i,
                lstate=lstate,
                sim_type=sim_type,
                batch_size=batch_size,
                adam_lr=adam_lr,
                current_epochs=current_epochs,
                target_epochs=target_epochs,
                p_error_list=p_error_list,
                prob_thresholds=prob_thresholds,
                train_shots=train_shots,
                test_shots=test_shots,
                model=model,
                is_accepted_func=is_q1prep_accepted,  # Pass your classical check function
                output_dir="NN_Model",
                device=device
            )

            # 5. Clean up VRAM after each run to prevent GPU Out-of-Memory (OOM)
            del model
            if device.type == "cuda":
                torch.cuda.empty_cache()

            run_elapsed = time.perf_counter() - run_start_time
            print(f"\n[COMPLETED] Run {completed_runs}/{total_runs} finished in {run_elapsed / 60:.2f} minutes.")

    master_elapsed = time.perf_counter() - total_start_time
    print("\n" + "=" * 65)
    print(f"ALL {total_runs} SIMULATION COMBINATIONS COMPLETED SUCCESSFULLY!")
    print(f"Total Execution Time: {master_elapsed / 3600:.2f} hours")
    print("=" * 65)

if __name__ == "__main__":
    main()