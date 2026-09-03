import os
import time
import torch
import numpy as np
import pandas as pd

from wrappers.nn_wrapper import ScalablePolarQED, generate_filtered_qed_dataset, generate_seeds
from wrappers.polar_wrapper import is_q1prep_accepted
from wrappers.stim_wrapper import convert_i_to_meas_type

def compare_prediction_time(
    model,
    checkpoint_path,
    n,
    i,
    lstate,
    sim_type,
    p_error,
    test_shots,
    is_accepted_func,
    chunk_size=10240,
    device="cpu"
):
    """
    Profiles and compares execution speed between Classical Function acceptance checking
    and Neural Network inference on the same dataset.
    """
    print("=" * 70)
    print(f" BENCHMARK: NN vs Classical Check | lstate='{lstate}' | sim_type='{sim_type}' | p={p_error}")
    print("=" * 70)

    # ---------------------------------------------------------
    # 1. LOAD TRAINED MODEL
    # ---------------------------------------------------------
    if not os.path.exists(checkpoint_path):
        raise FileNotFoundError(f"Checkpoint file not found: {checkpoint_path}")

    checkpoint = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()

    # ---------------------------------------------------------
    # 2. GENERATE TEST DATASET
    # ---------------------------------------------------------
    print(f"[DATA PREP] Generating {test_shots:,} test shots...")
    test_seed = generate_seeds(1)[0]
    
    gen_start = time.perf_counter()
    _, _, X_test_all, Y_test_all, data_test_all = generate_filtered_qed_dataset(
        n, i, lstate, sim_type, p_error, is_accepted_func, 
        num_shots=test_shots, seed=test_seed
    )
    gen_time = time.perf_counter() - gen_start
    total_samples = len(X_test_all)
    print(f"[DATA PREP] Dataset generated in {gen_time:.2f} seconds ({total_samples:,} samples)")

    # ---------------------------------------------------------
    # 3. BENCHMARK CLASSICAL FUNCTION
    # ---------------------------------------------------------
    print("\n[BENCHMARK 1/2] Running Classical Function Check...")
    
    zpos_list = [-1, -1, 1, 3, 6, 7, 22, 15, 90, 31, 362]
    zpos_list[n] = i-1

    meas_type = convert_i_to_meas_type(i, n, lstate)
    x_ind = 0
    for idx, m_type in enumerate(meas_type):
        if m_type == "x":
            x_ind = idx
            break


    total_meas_ancilla = 2**(n-1) * (n-x_ind)
    syndromes = X_test_all.numpy()

    # Warmup pass
    _ = [is_accepted_func(n, lstate, zpos_list, shot) for shot in syndromes[:100]]

    class_start = time.perf_counter()
    
    # Process each shot through classical verification logic
    classical_results = [is_accepted_func(n, lstate, zpos_list, shot) for shot in syndromes]
    
    class_total_time = time.perf_counter() - class_start
    class_us_per_shot = (class_total_time / total_samples) * 1e6
    class_throughput = total_samples / class_total_time

    # ---------------------------------------------------------
    # 4. BENCHMARK NEURAL NETWORK INFERENCE
    # ---------------------------------------------------------
    print("[BENCHMARK 2/2] Running Neural Network Chunked Inference...")

    # Warmup pass (stabilize GPU clock speed)
    sample_chunk = X_test_all[:min(1000, total_samples)].to(device)
    with torch.no_grad():
        _ = model(sample_chunk)

    if device.type == "cuda":
        torch.cuda.synchronize()

    nn_start = time.perf_counter()

    all_nn_probs = []
    with torch.no_grad():
        for start_idx in range(0, total_samples, chunk_size):
            end_idx = min(start_idx + chunk_size, total_samples)
            X_chunk = X_test_all[start_idx:end_idx].to(device)
            
            logits = model(X_chunk)
            probs = torch.sigmoid(logits)
            all_nn_probs.append(probs.cpu())

    if device.type == "cuda":
        torch.cuda.synchronize()

    nn_total_time = time.perf_counter() - nn_start
    nn_us_per_shot = (nn_total_time / total_samples) * 1e6
    nn_throughput = total_samples / nn_total_time

    # ---------------------------------------------------------
    # 5. SPEEDUP & SUMMARY METRICS
    # ---------------------------------------------------------
    speedup_factor = class_total_time / nn_total_time if nn_total_time > 0 else 0.0
    time_saved_sec = class_total_time - nn_total_time
    time_saved_pct = (time_saved_sec / class_total_time) * 100 if class_total_time > 0 else 0.0

    print("\n" + "=" * 70)
    print("                     PERFORMANCE COMPARISON RESULTS                     ")
    print("=" * 70)
    print(f"Total Shots Processed   : {total_samples:,}")
    print(f"Target Device           : {str(device).upper()}")
    print("-" * 70)
    print(f"Classical Check Time    : {class_total_time:.4f} seconds ({class_us_per_shot:.2f} µs/shot)")
    print(f"Classical Throughput    : {class_throughput:,.0f} shots/sec")
    print("-" * 70)
    print(f"Neural Network Time     : {nn_total_time:.4f} seconds ({nn_us_per_shot:.2f} µs/shot)")
    print(f"NN Throughput           : {nn_throughput:,.0f} shots/sec")
    print("-" * 70)
    print(f"SPEEDUP FACTOR          : {speedup_factor:.2f}x Faster")
    print(f"TOTAL TIME SAVED        : {time_saved_sec:.4f} seconds ({time_saved_pct:.2f}% reduction)")
    print("=" * 70 + "\n")

    return {
        "n": n,
        "i": i,
        "lstate": lstate,
        "sim_type": sim_type,
        "device":device,
        "p_error": p_error,
        "total_shots": total_samples,
        "classical_time_sec": class_total_time,
        "classical_us_per_shot": class_us_per_shot,
        "nn_time_sec": nn_total_time,
        "nn_us_per_shot": nn_us_per_shot,
        "speedup_factor": speedup_factor,
        "time_saved_percent": time_saved_pct
    }


def main():
    n = 4
    i = 6
    lstate_list = ["x", "z"]
    sim_type_list = ["normal", "m1"]
    p_error = 0.01  # Test on representative error rate
    test_shots = int(1e5)  # 100,000 shots
    chunk_size = 10240
    target_epochs = 300
    num_train_generations = 10
    checkpoint_dir = "NN_Model"

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[SYSTEM] Hardware Accelerator: {device}")
    if device.type == "cuda":
        print(f"[SYSTEM] GPU Model: {torch.cuda.get_device_name(0)}")

    benchmark_records = []

    for lstate in lstate_list:
        for sim_type in sim_type_list:
            meas_type = convert_i_to_meas_type(i, n, lstate)
            x_ind = next(idx for idx, m_type in enumerate(meas_type) if m_type == "x")

            checkpoint_path = os.path.join(
                checkpoint_dir, 
                f"checkpoint_{lstate}_{n}_{i}_{sim_type}_multinoise_gen{num_train_generations}_ep{target_epochs}.pt"                
            )
            # checkpoint_x_4_7_normal_multinoise_gen10_ep300

            if not os.path.exists(checkpoint_path):
                print(f"\n[WARNING] Skipping {lstate}-{sim_type}: Checkpoint not found at {checkpoint_path}")
                continue

            model = ScalablePolarQED(
                n=n, 
                x_ind=x_ind, 
                sim_type=sim_type, 
                include_data_bits=False
            ).to(device)

            # Run timing comparison
            metrics = compare_prediction_time(
                model=model,
                checkpoint_path=checkpoint_path,
                n=n,
                i=i,
                lstate=lstate,
                sim_type=sim_type,
                p_error=p_error,
                test_shots=test_shots,
                is_accepted_func=is_q1prep_accepted,
                chunk_size=chunk_size,
                device=device
            )

            benchmark_records.append(metrics)

            del model
            if device.type == "cuda":
                torch.cuda.empty_cache()

    # Save summary dataframe
    if benchmark_records:
        df_summary = pd.DataFrame(benchmark_records)
        summary_csv = os.path.join(checkpoint_dir, f"nn_vs_classical_speedup{n}_{i}_{device.type}_ep{target_epochs}.csv")
        df_summary.to_csv(summary_csv, index=False)
        print(f"\n[SUMMARY] Speedup comparison saved to: {summary_csv}")


if __name__ == "__main__":
    main()