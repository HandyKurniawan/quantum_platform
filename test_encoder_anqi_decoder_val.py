import numpy as np
# Import the Python wrapper class you created
from Encoders.polar import PyEncoderPolar
from wrappers.polar_wrapper import __polarcodec as codec

# --- 1. Configuration ---
K = 1
N = 8
num_iterations = int(1e1)
ebn0_db = 2.0  # Signal-to-Noise Ratio (Eb/N0) in dB
zpos = 6

# Create a mask where the first N-K positions are frozen (True)
# frozen_bits_mask = [1] * (N - K) + [0] * K
frozen_bits_mask = [1] * (N)
frozen_bits_mask[zpos] = 0

print("Initializing Polar Encoder...")
encoder = PyEncoderPolar(K, N, frozen_bits_mask)
print(f"Initialized with K={encoder.K}, N={encoder.N}")
print("frozen_bits_mask :", frozen_bits_mask)
# --- 2. Simulation Setup ---
# Pre-allocate the codeword array outside the loop for better performance
X_N = np.zeros(N, dtype=np.int32)

# Calculate Noise Standard Deviation (sigma)
# Rate R = K/N
R = K / N
# Convert Eb/N0 from dB to linear scale
ebn0_linear = 10 ** (ebn0_db / 10.0)
# Calculate noise variance assuming BPSK modulation
sigma = np.sqrt(1.0 / (2.0 * R * ebn0_linear))

block_errors = 0

print(f"\nRunning {num_iterations} iterations at Eb/N0 = {ebn0_db} dB...")

# --- 3. Monte Carlo Loop ---
for i in range(num_iterations):
    # A. Generate random information bits
    # U_K = np.random.randint(0, 2, K).astype(np.int32)
    U_K = np.random.randint(0, 2, K).astype(np.int32)

    # print("start :", frozen_bits_mask, U_K)

    # B. Perform encoding (modifies X_N in place)
    encoder.encode(U_K, X_N)

    # C. BPSK Modulation (0 -> +1, 1 -> -1)
    bpsk_symbols = 1.0 - 2.0 * X_N

    # D. Add AWGN Channel Noise
    noise = sigma * np.random.randn(N)
    # Y_N = bpsk_symbols + noise  # These are the noisy soft values (LLRs)
    Y_N = bpsk_symbols  # These are the noisy soft values (LLRs)

    # print(f"Y_N = {Y_N}")

    # E. Decode
    # Note: I've replaced the hardcoded '1' with 'K'. Ensure this matches 
    # what your C++ wrapper expects for the number of info bits.
    u_hat = codec.polardec(Y_N, zpos)

    # Ensure u_hat is iterable for comparison, in case K=1 returns a scalar
    if isinstance(u_hat, (int, np.integer, float)):
        u_hat = [u_hat]

    # print(Y_N, zpos, u_hat, U_K)
    # print("-----------------")

    # F. Check for Errors
    # If the decoded bits don't perfectly match the original bits, it's a block error
    if not np.array_equal(u_hat, U_K):
        block_errors += 1

# --- 4. Results ---
ler = block_errors / num_iterations

print("\n--- Simulation Complete ---")
print(f"Total Iterations : {num_iterations}")
print(f"Total Errors     : {block_errors}")
print(f"Logical Error Rate: {ler:.4e}")

