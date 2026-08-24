import os
import time
import torch
import numpy as np

from wrappers.nn_wrapper import ScalablePolarQED, evaluate_saved_model_chunked
from wrappers.polar_wrapper import is_q1prep_accepted
from wrappers.stim_wrapper import convert_i_to_meas_type

def main():
    # ---------------------------------------------------------
    # 1. EVALUATION CONFIGURATION PARAMETERS
    # ---------------------------------------------------------
    n = 4  # Code length N = 2^4 = 16
    i = 7
    lstate_list = ["x", "z"]
    sim_type_list = ["normal", "m1"]

    # Physical Channel Error Rates to Test
    p_error_list = [0.01, 0.0075, 0.005, 0.0025, 0.001]

    # NN Acceptance Decision Cutoffs (Theta Sweep)
    prob_thresholds = np.linspace(0.05, 0.95, 19)

    # Evaluation & Hardware Profiling Parameters
    test_shots = int(1e5)        # 100,000 shots per noise level for high statistical precision
    chunk_size = 10240           # Maximum batch size per forward pass to protect GPU VRAM
    target_epochs = 10
    num_train_generations = 5
    checkpoint_dir = "NN_Model"
    output_dir = "NN_Model/eval_results"

    # Device Setup (CUDA GPU with fallback to CPU)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[SYSTEM] Using device: {device}")
    if device.type == "cuda":
        print(f"[SYSTEM] GPU Name: {torch.cuda.get_device_name(0)}")

    # ---------------------------------------------------------
    # 2. MASTER EVALUATION LOOP
    # ---------------------------------------------------------
    total_start_time = time.perf_counter()
    completed_runs = 0
    total_runs = len(lstate_list) * len(sim_type_list)

    for lstate in lstate_list:
        for sim_type in sim_type_list:
            completed_runs += 1
            print("\n" + "#" * 65)
            print(f"   EVALUATION RUN {completed_runs}/{total_runs} | lstate: '{lstate}' | sim_type: '{sim_type}'")
            print("#" * 65 + "\n")

            # Derive x_ind dynamically
            meas_type = convert_i_to_meas_type(i, n, lstate)
            x_ind = 0
            for idx, m_type in enumerate(meas_type):
                if m_type == "x":
                    x_ind = idx
                    break

            # Construct exact checkpoint file path saved during training
            checkpoint_path = os.path.join(
                checkpoint_dir, 
                f"checkpoint_{lstate}_{n}_{i}_{sim_type}_multinoise_gen{num_train_generations}_ep{target_epochs}.pt"
            )

            # Check if model file exists before proceeding
            if not os.path.exists(checkpoint_path):
                print(f"[ERROR] Skipping evaluation: Checkpoint file NOT found at:\n  {checkpoint_path}")
                continue

            # Instantiate blank model structure
            model = ScalablePolarQED(
                n=n, 
                x_ind=x_ind, 
                sim_type=sim_type, 
                include_data_bits=False
            ).to(device)

            run_start_time = time.perf_counter()

            # Execute memory-safe chunked evaluation
            evaluate_saved_model_chunked(
                model=model,
                checkpoint_path=checkpoint_path,
                n=n,
                i=i,
                lstate=lstate,
                sim_type=sim_type,
                p_error_list=p_error_list,
                prob_thresholds=prob_thresholds,
                test_shots=test_shots,
                is_accepted_func=is_q1prep_accepted,
                chunk_size=chunk_size,
                output_dir=output_dir,
                device=device
            )

            # Clean up VRAM after each evaluation run
            del model
            if device.type == "cuda":
                torch.cuda.empty_cache()

            run_elapsed = time.perf_counter() - run_start_time
            print(f"\n[COMPLETED] Evaluation {completed_runs}/{total_runs} finished in {run_elapsed / 60:.2f} minutes.")

    master_elapsed = time.perf_counter() - total_start_time
    print("\n" + "=" * 65)
    print(f"ALL {total_runs} EVALUATION RUNS COMPLETED!")
    print(f"Total Execution Time: {master_elapsed / 60:.2f} minutes")
    print("=" * 65)

if __name__ == "__main__":
    main()