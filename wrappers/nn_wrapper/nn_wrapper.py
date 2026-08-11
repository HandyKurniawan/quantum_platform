import os
import secrets
import time
import stim
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.utils.data import TensorDataset, DataLoader, DataLoader, TensorDataset

from wrappers.stim_wrapper import (create_circuit_polar_stim_normal, convert_i_to_meas_type, 
simulate_batch_and_save_result_polar_normal)

from wrappers.polar_wrapper import (is_q1prep_accepted, get_logical_error_on_accepted_states, 
                                    get_q1prep_accepted_states)


# Generate N large 32-bit integers suitable for PyTorch/NumPy seeds
def generate_seeds(count, max_val=2_147_483_647):
    return [secrets.randbelow(max_val) for _ in range(count)]

def create_stim_circuit_polar(n, i, lstate, sim_type, p_error, shots, seed):
    N = 2**(n)
    ancilla_qubits = 2**(n - 1)
    total_qubits = N + ancilla_qubits
    meas_type = convert_i_to_meas_type(i, n, lstate)
    # print(meas_type, sim_type, "total qubits:", total_qubits, ", total ancilla:", ancilla_qubits)
    x_ind = 0
    for idx, m_type in enumerate(meas_type):
        if m_type == "x":
            x_ind = idx
            break

    circuit = create_circuit_polar_stim_normal(n, lstate, sim_type, p_error, seed, shots, 
                                               None, None, None, meas_type, total_qubits, x_ind)
    return circuit

def set_global_seeds(seed=12345):
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def generate_filtered_qed_dataset(n, i, lstate, sim_type, p_error, is_accepted_func, 
                                  num_shots=100000, seed=42):
    np.random.seed(seed)
    torch.manual_seed(seed)

    circuit = create_stim_circuit_polar(n, i, lstate, sim_type, p_error, 0, 0)

    meas_type = convert_i_to_meas_type(i, n, lstate)
    x_ind = 0
    for idx, m_type in enumerate(meas_type):
        if m_type == "x":
            x_ind = idx
            break
    
    # 1. Sample Noisy Data from Hardware / Stim
    sampler_noisy = circuit.compile_sampler(seed=seed)
    raw_measurements = sampler_noisy.sample(shots=num_shots).astype(int)


    if sim_type == "normal":
        pass
    elif sim_type == "m1":
        # print("masuk sini gak sih", len(raw_measurements[0]))
        tens = torch.tensor(raw_measurements)
        raw_measurements = F.pad(tens, (2**(n-1), 0), value=0).numpy()

    total_meas_ancilla = 2**(n-1) * (n-x_ind)
    syndromes = raw_measurements[:, :total_meas_ancilla]

    data_measurements = raw_measurements[:, total_meas_ancilla:]

    # print("raw:", raw_measurements[0], len(raw_measurements[0]))
    # print("data:", data_measurements[0], len(data_measurements[0]))
    # print(x_ind, 2**(n-1), total_meas_ancilla, sim_type, n)
    # print("synd:", syndromes[0], len(syndromes[0]))
    
    # 3. Ground Truth: Target error status of Information Qubit Q3 (Index 3)
    zpos_list = [-1, -1, 1, 3, 6, 7, 22, 15, 90, 31, 362]
    zpos_list[n] = i-1
    info_idx = i-1
    y_target = data_measurements[:, info_idx].reshape(-1, 1).astype(np.float32)
    
    # 4. Filter using your custom Classical Acceptance Function
    # Checks each syndrome vector against your classical error detection rules
    accepted_mask = np.array([is_accepted_func(n, lstate, zpos_list, s) for s in syndromes], dtype=bool)
    # print(sum(accepted_mask))
    
    rejected_mask = ~accepted_mask
    
    # Extract ONLY rejected shots for training the NN
    X_rejected = syndromes[rejected_mask].astype(np.float32)
    Y_rejected = y_target[rejected_mask]
    
    # Performance Baseline Metrics
    total_accepted = accepted_mask.sum()
    total_rejected = rejected_mask.sum()
    
    print("="*55)
    print("        DATASET GENERATION WITH CLASSICAL FILTERING       ")
    print("="*55)
    print(f"Total Shots Simulated     : {num_shots}")
    print(f"Classically Accepted      : {total_accepted} ({100 * total_accepted / num_shots:.2f}% Yield)")
    print(f"Classically Rejected      : {total_rejected} ({100 * total_rejected / num_shots:.2f}% Sent to NN)")
    print("="*55)
    
    return (
        torch.tensor(X_rejected), 
        torch.tensor(Y_rejected), 
        torch.tensor(syndromes, dtype=torch.float32), 
        torch.tensor(y_target),
        torch.tensor(raw_measurements, dtype=torch.float32)
    )

def evaluate_cascaded_qed(model, n, i, lstate, X_test_all, Y_test_all, Data_test_all, is_accepted_func, error_prob=0.5, device="cpu"):
    """
    Evaluates the cascaded QED model on CPU or GPU.
    
    Parameters:
        device (str or torch.device): Device to run the model and tensor ops on ('cpu', 'cuda', etc.).
    """
    # Ensure device object
    device = torch.device(device)
    
    # Move model to selected device and set to eval mode
    model = model.to(device)
    model.eval()

    with torch.no_grad():
        num_shots = len(X_test_all)

        zpos_list = [-1, -1, 1, 3, 6, 7, 22, 15, 90, 31, 362]
        zpos_list[n] = i - 1
        
        # Determine lstate based on n or context if required by is_accepted_func
        # (Assuming lstate handling is internal or captured via arguments/scope)
        
        # Step 1: Classical Acceptance (Runs on CPU via NumPy)
        # Convert X_test_all to numpy once for CPU filtering
        X_cpu_np = X_test_all.cpu().numpy() if isinstance(X_test_all, torch.Tensor) else np.array(X_test_all)
        classical_mask_np = np.array([is_accepted_func(n, lstate, zpos_list, s) for s in X_cpu_np], dtype=bool)
        
        # Convert classical mask to a PyTorch boolean tensor on the target device
        classical_mask = torch.tensor(classical_mask_np, dtype=torch.bool, device=device)
        
        # Step 2: NN Rescues from Rejected Pool
        rejected_mask = ~classical_mask
        
        # Move input data tensors to target device if not already there
        X_test_all_dev = X_test_all.to(device)
        Y_test_all_dev = Y_test_all.to(device)
        Data_test_all_dev = Data_test_all.to(device)

        X_rejected = X_test_all_dev[rejected_mask]
        
        nn_rescued_mask = torch.zeros(num_shots, dtype=torch.bool, device=device)
        
        if len(X_rejected) > 0:
            # Model forward pass on selected device
            logits = model(X_rejected)
            probs = torch.sigmoid(logits)
            
            # Keep states where NN predicts error probability < 0.75 (or threshold)
            rescued_mask_rejected = (probs < error_prob).squeeze(-1)
            
            # Map rescued status back to global indices on device
            rejected_indices = torch.where(rejected_mask)[0]
            rescued_global_indices = rejected_indices[rescued_mask_rejected]
            nn_rescued_mask[rescued_global_indices] = True

        # Combine both masks on device
        total_accepted_mask = classical_mask | nn_rescued_mask
        
        # Extract Accepted States
        accepted_syndromes = X_test_all_dev[total_accepted_mask]
        accepted_data_bits = Data_test_all_dev[total_accepted_mask]
        
        # Calculate Metrics directly on device
        num_accepted = total_accepted_mask.sum().item()
        final_yield = total_accepted_mask.float().mean().item()
        
        if num_accepted > 0:
            final_fidelity = 1.0 - Y_test_all_dev[total_accepted_mask].float().mean().item()
        else:
            final_fidelity = 1.0

        print(f"[{device.type.upper()}] Final Yield: {final_yield*100:.2f}% | Final Fidelity: {final_fidelity*100:.2f}%")
        
        return accepted_syndromes, accepted_data_bits

def verify_with_our_function(n, lstate, zpos_list, final_data):
    # Handle empty dataset right away
    total_len = len(final_data)
    if total_len == 0:
        return 0, 0, 0.0, 0.0, 0.0

    counts = {}
    for res in final_data:
        bit_string = ""
        for j in res:
            if j:
                bit_string = "1" + bit_string
            else:
                bit_string = "0" + bit_string

        counts[bit_string] = counts.get(bit_string, 0) + 1

    (
        count_accept,
        count_logerror,
        count_undecided,
        ler,
        detect_normal,
        decoding_normal,
    ) = get_logical_error_on_accepted_states(
        n, lstate.upper(), counts, zpos_list
    )

    # Safe division calculations
    prep_rate = count_accept / total_len if total_len > 0 else 0.0

    ler_clean = (
        (count_logerror - (count_undecided / 2)) / count_accept
        if count_accept > 0
        else 1
    )

    one_minus_ler = 1 - ler if ler is not None else 1

    return count_accept, total_len, prep_rate, ler_clean, one_minus_ler

def load_model_from_checkpoint(
    checkpoint_path, model, optimizer=None, device="cpu", is_eval=True
):
    """Loads model (and optionally optimizer) state from a PyTorch checkpoint file.

    Parameters:
    -----------
    checkpoint_path : str
        Path to the saved `.pt` or `.pth` checkpoint file.
    model : torch.nn.Module
        An instance of your model class (must match saved architecture).
    optimizer : torch.optim.Optimizer, optional
        An instance of your optimizer if resuming training.
    device : str or torch.device
        Device to map tensors to ('cpu' or 'cuda').
    is_eval : bool
        If True, sets `model.eval()`. If False, sets `model.train()`.

    Returns:
    --------
    model : torch.nn.Module
        Restored model.
    optimizer : torch.optim.Optimizer or None
        Restored optimizer (if provided).
    start_epoch : int
        Next epoch number to resume from (0 if fresh).
    loss : float or None
        Last recorded loss from the checkpoint.
    """
    if not os.path.exists(checkpoint_path):
        raise FileNotFoundError(
            f"No checkpoint found at path: '{checkpoint_path}'"
        )

    print(f"[INFO] Loading checkpoint from: {checkpoint_path}")
    checkpoint = torch.load(checkpoint_path, map_location=device)

    # 1. Restore Model Weights
    if "model_state_dict" in checkpoint:
        model.load_state_dict(checkpoint["model_state_dict"])
    else:
        # Fallback if state_dict was saved directly
        model.load_state_dict(checkpoint)

    # 2. Restore Optimizer State (if provided)
    if optimizer is not None and "optimizer_state_dict" in checkpoint:
        optimizer.load_state_dict(checkpoint["optimizer_state_dict"])

    # 3. Extract Metadata
    start_epoch = checkpoint.get("epoch", 0)
    last_loss = checkpoint.get("loss", None)

    # 4. Set Mode (Evaluation vs Training)
    if is_eval:
        model.eval()
    else:
        model.train()

    print(f"[SUCCESS] Checkpoint loaded. Last Epoch: {start_epoch}")
    if last_loss is not None:
        print(f"[INFO] Saved Loss: {last_loss:.6f}")

    return model, optimizer, start_epoch, last_loss

class ResidualBlock(nn.Module):
    def __init__(self, hidden_dim, dropout_rate=0.2):
        super(ResidualBlock, self).__init__()
        self.block = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout_rate),
            nn.Linear(hidden_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim)
        )
        self.activation = nn.GELU()

    def forward(self, x):
        return self.activation(x + self.block(x))

class ScalablePolarQED(nn.Module):
    def __init__(self, n, x_ind, sim_type, include_data_bits=False):
        """
        Dynamically builds the QED network based on n, x_ind, and sim_type.
        """
        super(ScalablePolarQED, self).__init__()
        
        # 1. Base Dimensions
        self.n = n
        self.x_ind = x_ind
        self.N = 2 ** n                 
        self.aux_qubits = self.N // 2   
        
        # 2. Calculate Active Measurement Layers
        self.active_layers = n - x_ind
        
        # # If sim_type is "m1", we skip one more layer of Pauli measurements
        # if sim_type == "m1":
        #     self.active_layers -= 1
            
        # Safety check to ensure we don't end up with 0 or negative layers
        self.active_layers = max(1, self.active_layers)
            
        # 3. Calculate Exact Input Dimension (No 0-padding needed anymore!)
        self.syndrome_bits = self.active_layers * self.aux_qubits 
        self.total_bits = self.syndrome_bits + self.N
        
        self.input_dim = self.total_bits if include_data_bits else self.syndrome_bits
        
        # 4. Scale Network Capacity based on n (Polar Graph Complexity)
        self.hidden_dim = 128 * (2 ** (n - 3)) 
        self.num_blocks = n - 1 
        
        print("="*55)
        print(f"       DYNAMIC MODEL INITIALIZED (n={self.n}, N={self.N})       ")
        print("="*55)
        print(f"Base Layers      : {n} (Skipped {x_ind} due to x_ind)")
        print(f"Sim Type Adjust  : {'-1 Layer' if sim_type == 'm1' else 'None'} ({sim_type})")
        print(f"Active Layers    : {self.active_layers}")
        print(f"Input Dimension  : {self.input_dim} bits (No padding required)")
        print(f"Hidden Dimension : {self.hidden_dim} neurons per layer")
        print("="*55)

        # 5. Build Network Architecture
        self.input_layer = nn.Sequential(
            nn.Linear(self.input_dim, self.hidden_dim),
            nn.BatchNorm1d(self.hidden_dim),
            nn.GELU()
        )
        
        self.res_blocks = nn.ModuleList([
            ResidualBlock(self.hidden_dim) for _ in range(self.num_blocks)
        ])
        
        self.output_layer = nn.Sequential(
            nn.Linear(self.hidden_dim, self.hidden_dim // 2),
            nn.BatchNorm1d(self.hidden_dim // 2),
            nn.GELU(),
            nn.Linear(self.hidden_dim // 2, 1) 
        )

    def forward(self, x):
        x = self.input_layer(x)
        for block in self.res_blocks:
            x = block(x)
        x = self.output_layer(x)
        return x

def training_model(
    model,
    n,
    i,
    lstate,
    sim_type,
    p_error_list,
    is_accepted_func,
    train_shots,
    test_shots,
    batch_size,
    adam_lr,
    current_epochs,
    target_epochs,
    device="cpu"
):
    train_seeds = generate_seeds(len(p_error_list))
    test_seeds = generate_seeds(len(p_error_list))

    # --- METRIC TRACKING 1: Model Size & Parameter Count ---
    total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    model_mem_mb = (total_params * 4) / (1024 ** 2)  # 32-bit float = 4 bytes

    print("=" * 55)
    print("      STEP 1: GENERATING MULTI-NOISE DATASETS     ")
    print("=" * 55)

    X_train_list = []
    Y_train_list = []
    test_datasets = {}

    # Pool training data across all noise levels
    for p_error, train_seed, test_seed in zip(p_error_list, train_seeds, test_seeds):
        print(f"[DATA PREP] Generating data for p_error: {p_error}")

        # 1. Training samples for this noise rate
        X_tr, Y_tr, _, _, _ = generate_filtered_qed_dataset(
            n, i, lstate, sim_type, p_error, is_accepted_func, num_shots=train_shots, seed=train_seed
        )
        X_train_list.append(X_tr)
        Y_train_list.append(Y_tr)

        # 2. Test samples stored individually for evaluating each noise rate later
        _, _, X_te, Y_te, data_te = generate_filtered_qed_dataset(
            n, i, lstate, sim_type, p_error, is_accepted_func, num_shots=test_shots, seed=test_seed
        )
        test_datasets[p_error] = (X_te, Y_te, data_te)

    # Concatenate all training sets into a single pooled multi-noise dataset
    X_train_pooled = torch.cat(X_train_list, dim=0).to(device)
    Y_train_pooled = torch.cat(Y_train_list, dim=0).to(device)

    # DataLoader shuffles and mixes noise levels dynamically in every batch
    train_loader = DataLoader(
        TensorDataset(X_train_pooled, Y_train_pooled),
        batch_size=batch_size,
        shuffle=True,
    )

    print("\n" + "=" * 55)
    print(f"      STEP 2: TRAINING UNIFIED MODEL (Device: {str(device).upper()})   ")
    print("=" * 55)
    print(f"Total Pooled Training Samples : {len(X_train_pooled):,}")
    print(f"Model Complexity              : {total_params:,} Parameters ({model_mem_mb:.2f} MB)")

    checkpoint_path = f"NN_Model/checkpoint_{lstate}_{n}_{i}_{sim_type}_multinoise_ep{target_epochs}.pt"

    model = model.to(device)
    optimizer = optim.Adam(model.parameters(), lr=adam_lr)

    # Compute class balance weight across the entire pooled dataset
    num_positives = Y_train_pooled.sum()
    num_negatives = len(Y_train_pooled) - num_positives
    pos_weight = num_negatives / torch.clamp(num_positives, min=1.0)
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)

    start_epoch = 0
    avg_loss = 0.0  # Initialize variable safely outside loop
    os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)

    # Safely load checkpoint and restore previous loss if training skipped
    if os.path.exists(checkpoint_path):
        print(f"\n[INFO] Found checkpoint file: '{checkpoint_path}'")
        checkpoint = torch.load(checkpoint_path, map_location=device)
        model.load_state_dict(checkpoint["model_state_dict"])
        optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        start_epoch = checkpoint["epoch"]
        avg_loss = checkpoint.get("loss", 0.0)  # <-- Restores saved loss if epoch loop is skipped!
        print(f"[INFO] Resuming training from Epoch {start_epoch + 1}/{target_epochs}\n")
    else:
        print("\n[INFO] Starting fresh multi-noise training...\n")

    # --- METRIC TRACKING 2: Training Time ---
    train_start_time = time.perf_counter()

    for epoch in range(start_epoch, target_epochs):
        model.train()
        total_loss = 0.0

        for batch_x, batch_y in train_loader:
            optimizer.zero_grad()
            logits = model(batch_x)
            loss = criterion(logits, batch_y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        avg_loss = total_loss / len(train_loader)
        current_epoch_num = epoch + 1

        print(f"Epoch {current_epoch_num:03d}/{target_epochs:03d} | BCE Loss: {avg_loss:.4f}")

        checkpoint = {
            "epoch": current_epoch_num,
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "loss": avg_loss,
        }
        torch.save(checkpoint, checkpoint_path)

    train_total_time = time.perf_counter() - train_start_time

    # --- METRIC TRACKING 3: Inference Latency & Throughput ---
    print("\n" + "=" * 55)
    print("      STEP 3: PROFILING MODEL INFERENCE      ")
    print("=" * 55)
    
    model.eval()

    # Use first noise level's test tensor to measure real-time hardware execution speeds
    first_p = p_error_list[0]
    sample_X_test = test_datasets[first_p][0].to(device)
    single_sample = sample_X_test[:1]

    # Warmup passes for GPU clock stability
    with torch.no_grad():
        for _ in range(50):
            _ = model(single_sample)

    # Single-shot latency over 1,000 forward passes
    if device == "cuda":
        torch.cuda.synchronize()
    lat_start = time.perf_counter()
    with torch.no_grad():
        for _ in range(1000):
            _ = model(single_sample)
    if device == "cuda":
        torch.cuda.synchronize()
        
    single_shot_latency_us = ((time.perf_counter() - lat_start) / 1000) * 1e6  # Microseconds

    # Batch Throughput (Shots evaluated per second)
    if device == "cuda":
        torch.cuda.synchronize()
    tp_start = time.perf_counter()
    with torch.no_grad():
        _ = model(sample_X_test)
    if device == "cuda":
        torch.cuda.synchronize()
        
    batch_inference_time = time.perf_counter() - tp_start
    throughput_shots_per_sec = len(sample_X_test) / batch_inference_time

    print(f"Total Training Time      : {train_total_time:.2f} seconds")
    print(f"Single-Shot Latency      : {single_shot_latency_us:.2f} µs/shot")
    print(f"Batch Throughput         : {throughput_shots_per_sec:,.0f} shots/sec")
    print("=" * 55 + "\n")

    # Store unified model and metrics mapped to each test p_error
    experiment_results = {}
    
    for p_error in p_error_list:
        X_test_all, Y_test_all, data_test_all = test_datasets[p_error]
        
        # Calculate specific TEST BCE Loss for this exact p_error
        with torch.no_grad():
            X_test_dev = X_test_all.to(device)
            Y_test_dev = Y_test_all.to(device)
            test_logits = model(X_test_dev)
            test_bce_loss = criterion(test_logits, Y_test_dev).item()

        experiment_results[p_error] = {
            "model": model,
            "X_test_all": X_test_all,
            "Y_test_all": Y_test_all,
            "data_test_all": data_test_all,
            "metrics": {
                "total_params": total_params,
                "model_mem_mb": model_mem_mb,
                "train_time_sec": train_total_time,
                "latency_us": single_shot_latency_us,
                "throughput_shots_sec": throughput_shots_per_sec,
                "train_pooled_loss": avg_loss,      # Overall training loss on pooled data
                "test_bce_loss": test_bce_loss        # Specific test loss for this p_error
            }
        }

    return experiment_results

def direct_nn_prediction(model, X_test_all, data_test_all, device="cpu", threshold = 0.5):
    """
    Evaluates the entire dataset using only the Neural Network.
    Bypasses classical filtering entirely.
    """
    print("="*55)
    print("        DIRECT NEURAL NETWORK INFERENCE       ")
    print("="*55)
    
    # 1. Set the model to evaluation mode (disables dropout/batchnorm updates)
    model.eval()
    
    # 2. Ensure data is on the correct device
    X_test_all = X_test_all.to(device)
    
    with torch.no_grad():
        # 3. Forward pass: get the raw logits for all shots
        logits = model(X_test_all)
        
        # 4. Convert logits to probabilities (0.0 to 1.0)
        probs = torch.sigmoid(logits)
        
        # 5. Threshold the probabilities
        # Assuming < 0.5 means the network predicts the information qubit is SAFE (0)
        nn_accepted_mask = (probs < threshold).squeeze().cpu()
        
    # 6. Apply the mask to extract only the states the NN deemed safe
    accepted_syndromes = X_test_all.cpu()[nn_accepted_mask]
    accepted_data_bits = data_test_all.cpu()[nn_accepted_mask]
    
    # Calculate metrics
    total_shots = len(X_test_all)
    accepted_shots = len(accepted_syndromes)
    yield_percentage = (accepted_shots / total_shots) * 100
    
    print(f"Total Shots Evaluated : {total_shots}")
    print(f"States Accepted by NN : {accepted_shots}")
    print(f"Direct NN Yield       : {yield_percentage:.2f}%")
    print("="*55)
    
    # Return the clean, accepted matrices for the SC Decoder
    return accepted_syndromes, accepted_data_bits, nn_accepted_mask

def simulate_direct_nn_prediction_by_threshold(model, n, i , lstate, X_test_all, data_test_all, threshold, device = "cpu"):

    final_syndromes, final_data_bits, acceptance_mask = direct_nn_prediction(
        model=model,
        X_test_all=X_test_all,
        data_test_all=data_test_all,
        device=device,
        threshold=threshold
    )

    zpos_list = [-1, -1, 1, 3, 6, 7, 22, 15, 90, 31, 362]
    zpos_list[n] = i-1

    count_accept, total_data, prep_rate, ler_clean, ler_all = verify_with_our_function(n, lstate, zpos_list,final_data_bits)

    # print("Error Prob:", threshold, ", PR:", prep_rate, ", LER:", ler_clean, ", count:", count_accept, ", total data:", total_data, "ler_all:", ler_all)

    return count_accept, total_data, prep_rate, ler_clean, ler_all

def run_simulation(
    n,
    i,
    lstate,
    sim_type,
    batch_size,
    adam_lr,
    current_epochs,
    target_epochs,
    p_error_list,
    train_shots,
    test_shots,
    model,
    prob_thresholds=np.linspace(0.05, 1.0, 20),  # NN acceptance thresholds
    is_accepted_func=is_q1prep_accepted,
    output_dir="NN_Model",
    device="cpu"
):
    """
    End-to-End Orchestrator for Multi-Noise Training, Hardware Profiling,
    and Threshold-Sweeping Evaluation for Quantum Error Detection.
    """
    
    # ---------------------------------------------------------
    # 1. TRAIN UNIFIED MULTI-NOISE MODEL & RETRIEVE METRICS
    # ---------------------------------------------------------
    # training_model returns a dictionary keyed by p_error containing
    # test datasets and hardware profiling metrics.
    experiment_results = training_model(
        model=model,
        n=n,
        i=i,
        lstate=lstate,
        sim_type=sim_type,
        p_error_list=p_error_list,
        is_accepted_func=is_accepted_func,
        train_shots=train_shots,
        test_shots=test_shots,
        batch_size=batch_size,
        adam_lr=adam_lr,
        current_epochs=current_epochs,
        target_epochs=target_epochs,
        device=device
    )

    # Calculate polar code block size
    N_code = 2 ** n

    # ---------------------------------------------------------
    # 2. PREPARE OUTPUT LOGGING CSV
    # ---------------------------------------------------------
    output_file = os.path.join(output_dir, f"qpc_{lstate}_n{n}_i{i}_{sim_type}.csv")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    columns = [
        # Circuit & Code Metadata
        "n",
        "N",
        "i",
        "lstate",
        "sim_type",
        
        # Noise & NN Decision Parameters
        "p_error",             # Physical channel error rate
        "prob_threshold",      # NN error probability acceptance cutoff (theta)
        
        # Quantum Performance Metrics
        "count_accept",
        "total_data",
        "prep_rate",           # Yield (%)
        "ler_clean",           # LER of accepted states
        "ler_all",             # LER of raw dataset (baseline)
        
        # Hardware & Computational Metrics
        "total_params",        # Model size (trainable parameters)
        "model_mem_mb",        # VRAM / RAM footprint (MB)
        "train_time_sec",      # Total wall-clock training time (seconds)
        "latency_us",          # Single-shot inference latency (microseconds)
        "train_pooled_loss",   # Batch inference evaluation speed (shots/sec)
        "test_bce_loss"        # Final training BCE loss
    ]

    # Write headers only if the file does not already exist
    file_exists = os.path.exists(output_file)
    if not file_exists:
        pd.DataFrame(columns=columns).to_csv(output_file, mode="w", index=False)

    print("=" * 65)
    print("      STEP 4: RUNNING THRESHOLD SWEEP & LOGGING RESULTS       ")
    print("=" * 65)

    # ---------------------------------------------------------
    # 3. EVALUATION LOOP ACROSS NOISE RATES & THRESHOLDS
    # ---------------------------------------------------------
    model.eval()

    # Iterate through each physical error rate tested
    for p_error in p_error_list:
        p_data = experiment_results[p_error]
        
        trained_model = p_data["model"]
        X_test_all = p_data["X_test_all"]
        data_test_all = p_data["data_test_all"]
        hw_metrics = p_data["metrics"]

        print(f"\n[EVALUATION] Testing Physical Noise p_error = {p_error:.5f}")

        # Sweep NN probability acceptance threshold (theta)
        for threshold in prob_thresholds:
            thresh_val = float(threshold)

            # Evaluate performance under the specific decision threshold
            count_accept, total_data, prep_rate, ler_clean, ler_all = (
                simulate_direct_nn_prediction_by_threshold(
                    model=trained_model,
                    n=n,
                    i=i,
                    lstate=lstate,
                    X_test_all=X_test_all,
                    data_test_all=data_test_all,
                    threshold=thresh_val,
                    device=device
                )
            )

            row = {
                "n": n,
                "N": N_code,
                "i": i,
                "lstate": lstate,
                "sim_type": sim_type,
                "p_error": float(p_error),
                "prob_threshold": thresh_val,
                "count_accept": count_accept,
                "total_data": total_data,
                "prep_rate": prep_rate,
                "ler_clean": ler_clean,
                "ler_all": ler_all,
                
                # Directly mapped hardware and loss metrics:
                "total_params": hw_metrics["total_params"],
                "model_mem_mb": hw_metrics["model_mem_mb"],
                "train_time_sec": hw_metrics["train_time_sec"],
                "latency_us": hw_metrics["latency_us"],
                "throughput_shots_sec": hw_metrics["throughput_shots_sec"],
                "train_pooled_loss": hw_metrics["train_pooled_loss"], # Overall training loss
                "test_bce_loss": hw_metrics["test_bce_loss"],         # Specific loss for this p_error
            }

            # Append row directly to CSV
            pd.DataFrame([row]).to_csv(output_file, mode="a", header=False, index=False)

        print(f" -> Completed threshold sweep for p_error = {p_error:.5f}. Logged to CSV.")

    print("\n" + "=" * 65)
    print(f"[SUCCESS] All simulation results written to:\n  {output_file}")
    print("=" * 65)
    
    return experiment_results, output_file
    


