import stim
# import random
# import csv
# import pandas as pd
import collections
import os
from wrappers.polar_wrapper import (divide_half_list, get_logical_error_on_accepted_states)
import json

def convert_i_to_meas_type(i, n, lstate = "z"):
    bit_format = "0:0{}b".format(n)
    bit_format = "{" + bit_format + "}" 

    if lstate == "z":
        zpos = i-1
    else:
        zpos = i-2

    n_bit = bit_format.format(zpos)[::-1]
    meas_type = ['x' if char == '0' else 'z' for char in n_bit]
    
    print(n, lstate, i, n_bit, meas_type)

    return meas_type

def noisy_cx(sim: stim.TableauSimulator, ctrl: int, targ: int, p: float):
    sim.cx(ctrl, targ)
    sim.depolarize2(ctrl,targ, p=p)

def noisy_h(sim: stim.TableauSimulator, targ, p):
    sim.h(targ)
    sim.depolarize1(targ, p=p)

def noisy_x(sim: stim.TableauSimulator, targ, p):
    sim.x(targ)
    sim.depolarize1(targ, p=p)

def noisy_z(sim: stim.TableauSimulator, targ, p):
    sim.z(targ)
    sim.depolarize1(targ, p=p)

def noisy_reset(sim: stim.TableauSimulator, targ, p):
    sim.reset(targ)
    sim.x_error(targ, p=p)

def noisy_measurement(sim: stim.TableauSimulator, targ, p):
    sim.x_error(targ, p=p)
    sim.measure(targ)

def generate_circuit_extraction_syndrome_stim(sim: stim.TableauSimulator, k, meas_type, x_first = False, p_error = 0, start_idx = 0):
    num_qbits = (2**k) + (2**(k-1))
    num_cbits = 2**(k-1)

    data_qubits = []
    ancillas = []
    for i in range(2**(k-1)):
        ancillas.append(i * 3 + 2 + start_idx) 

    for i in range(start_idx, num_qbits + start_idx):
        if i not in ancillas:
            data_qubits.append(i) 

    d1, d2 = divide_half_list(data_qubits)

    for idx in range(len(d1)):

        if meas_type.lower() == "x":

            if x_first:
                noisy_h(sim, d1[idx], p=p_error)
                noisy_cx(sim, d1[idx], d2[idx], p=p_error)

            else:
                noisy_h(sim, ancillas[idx], p=p_error)
                noisy_cx(sim, ancillas[idx], d1[idx], p=p_error)
                noisy_cx(sim, ancillas[idx], d2[idx], p=p_error)
                noisy_h(sim, ancillas[idx], p=p_error)


        elif meas_type.lower() == "z":
            noisy_cx(sim, d1[idx], ancillas[idx], p=p_error)
            noisy_cx(sim, d2[idx], ancillas[idx], p=p_error)


def check_for_mismatch(syndrome_bits, n, x_ind, detection_layer = 1):
    """
    Helper function to check for a pattern mismatch in the measurement record.
    Returns True if a mismatch is found, False otherwise.
    d_layer = detection layer
    """
    expected_length = 2**(n - 1)
    
    full_bitstring = ''.join(['1' if b else '0' for b in syndrome_bits])
    
    # Extract the relevant portion of the syndrome for this layer.
    start_index = expected_length * detection_layer
    syndrome_to_check = full_bitstring[start_index:]
    
    bit_gap = 2**x_ind

    # print(len(full_bitstring), full_bitstring, syndrome_to_check, expected_length, bit_gap, x_ind)
    
    for i in range(expected_length):
        if (i % (2 * bit_gap)) < bit_gap:
            j = i + bit_gap
            if syndrome_to_check[i] != syndrome_to_check[j]:
                # print(f"Mismatch found at indices ({i}, {j}) for string {syndrome_to_check}.")
                return True
            
    return False

def simulate_stim_polar_code(n, lstate, sim_type, i, p_error, shots, seeds):
    """
    Simulates a quantum circuit for stabilizer code, simplified and optimized.

    Args:
        n (int): code length for polar code
        lstate (str): z for logical |0>, z for logical |+>
        sim_type: normal, m1, m2, m3
        p_error (float): The probability of an error occurring.
        shots (int): The number of simulation runs.
        seeds (list): A list of seeds for the simulator.
        i (int): An index used to determine measurement types (message location)

    Returns:
        dict: A dictionary of measurement outcome counts.
    """
    #m1 circuit simplify
    #m2 m1 + error detection
    #m3 m1 + error correction
    
    meas_type = convert_i_to_meas_type(i, n, lstate)
    N = 2**n
    ancilla_qubits = 2**(n - 1)

    counts = collections.Counter()
    bitstrings = []
    total_qubits = N + ancilla_qubits

    x_ind = 0
    for idx, m_type in enumerate(meas_type):
        if m_type == "x":
            x_ind = idx
            break

    # print("index of the first x :", x_ind)
    # gap = 2**x_ind

    count_detect_discard = 0

    for shot_idx in range(shots):
        sim = stim.TableauSimulator(seed=seeds[shot_idx])

        error_detected_this_shot = False

        for level in range(1, n+1):

            # print(level, "-", meas_type[level - 1])
            
            num_loops = 2**(n - level)
            start_idx_mult = 2**(level) + 2**(level - 1)

            if sim_type in ["m1", "m2"] and level == x_ind + 1:
                x_first = True
            else:
                x_first = False

            if level <= x_ind:
                # skip the beginning of zz measurement
                # print("skip :" , level, x_ind)
                pass
            else:
                # print("num_loops :", num_loops)
                for loop_idx in range(num_loops):
                    start_idx = loop_idx * start_idx_mult
                    generate_circuit_extraction_syndrome_stim(sim, level, meas_type[level - 1], x_first, p_error=p_error, start_idx=start_idx)
            
                # with the simplification, the first measurement will be always 0
                if not x_first:
                    for qb in range(2, total_qubits, 3): 
                        noisy_measurement(sim, qb, p_error)
                        noisy_reset(sim, qb, p_error)

            # add error detection
            # first error detection
            if sim_type in ["m2"] and level - x_ind == 2:
                cms = sim.current_measurement_record()
                # print(cms)

                detection_layer = 1
                if sim_type == "m2":
                    detection_layer -=1

                if check_for_mismatch(cms, n, x_ind, detection_layer):
                    error_detected_this_shot = True
                    break # Break from the `level` loop

        # if error is detected, skip the operation
        if error_detected_this_shot:
            count_detect_discard += 1
            continue # Continue to the next shot

        # Final measurements, simplified.
        for qb_idx in (j for j in range(total_qubits) if j % 3 != 2):
            if lstate == "x":
                noisy_h(sim, qb_idx, p_error)
            noisy_measurement(sim, qb_idx, p_error, )
            

        final_measurements = sim.current_measurement_record()

        # Generate the bit string, reverse it, and update the counts.
        bit_string = ''.join(['1' if b else '0' for b in final_measurements])[::-1]

        if sim_type in ["m1", "m2"]:
            bit_string = bit_string + "0"*(2**(level - 1))
        

        # counts[bit_string] += 1
        bitstrings.append(bit_string)

    counts = collections.Counter(bitstrings)
    return counts
    # return bitstrings

def get_processed_shots(n, lstate, p_error, i):
    total_shots = 0

    # file_path = f"./output/STIM/n{n}/polar_n{n}_{lstate}_{i}_{p_error}_normal.txt"
    # if os.path.exists(file_path):
    #     with open(file_path, "r") as f:
    #         lines = f.read().splitlines()
    #         total_shots = len(lines)

    file_path = f"./output/STIM/n{n}/polar_n{n}_{lstate}_{i}_{p_error}_normal.json"
    if os.path.exists(file_path):
        with open(file_path, "r") as f:  # "a" means append mode
            loaded_dict = json.load(f)
            current_counter = collections.Counter(loaded_dict)
            total_shots = sum(current_counter.values())
    

    return total_shots

def simulate_batch_and_save_result_polar(n, lstate, sim_type, p_error, i, shots, seed_starts):

    zpos_list = [-1, -1, 1, 3, 6, 7, 22, 15, 90, 31, 362]
    zpos_list[n] = i-1

    # to get total shots from the normal method files
    total_shots = get_processed_shots(n, lstate, p_error, i)
    seed_list = range(total_shots, total_shots + shots + 5)
    print(n, lstate, sim_type, p_error, i, shots, total_shots, total_shots + shots + 5)

    # print(existing_data, seed_list[0], seed_list[-1])
    results = simulate_stim_polar_code(n, lstate, sim_type, i, p_error, shots, seed_list)

    # file_path = f"./output/STIM/n{n}/polar_n{n}_{lstate}_{i}_{p_error}_{sim_type}.txt"
    # with open(file_path, "a") as f:  # "a" means append mode
    #     f.write("\n".join(results) + "\n")

    file_path = f"./output/STIM/n{n}/polar_n{n}_{lstate}_{i}_{p_error}_{sim_type}.json"
    try:
        with open(file_path, "r") as f:  # "a" means append mode
            loaded_dict = json.load(f)
            current_counter = collections.Counter(loaded_dict)

    except FileNotFoundError:
        current_counter = collections.Counter()

    # updating the counter with the new results
    current_counter.update(results)

    with open(file_path, "w") as f:  # "a" means append mode
        json.dump(dict(current_counter), f)


def calculate_logical_error_result_polar(n, lstate, i, p_error, sim_type, shots):
    #m1 circuit simplify
    #m2 m1 + error detection

    meas_type = convert_i_to_meas_type(i, n, lstate)
    # print(n, lstate, i, p_error, sim_type, meas_type, file_path)

    # to get total shots from the normal method files
    total_shots = get_processed_shots(n, lstate, p_error, i)

    # file_path = f"./output/STIM/n{n}/polar_n{n}_{lstate}_{i}_{p_error}_{sim_type}.txt"
    # if not os.path.exists(file_path):
    #     return None  # skip missing files

    # with open(file_path, "r") as f:
    #     lines = f.read().splitlines()

    # shots_remained = len(lines)
    # count_detect_discard = total_shots - shots_remained
    # counts = collections.Counter(lines)

    file_path = f"./output/STIM/n{n}/polar_n{n}_{lstate}_{i}_{p_error}_{sim_type}.json"
    try:
        with open(file_path, "r") as f:  # "a" means append mode
            loaded_dict = json.load(f)
            current_counter = collections.Counter(loaded_dict)
            shots_remained = sum(current_counter.values())

    except FileNotFoundError:
        return None

    count_detect_discard = total_shots - shots_remained
    counts = dict(current_counter)

    zpos_list = [-1, -1, 1, 3, 6, 7, 22, 15, 90, 31, 362]
    zpos_list[n] = i - 1

    # for key, value in counts.items():
    #     print(key, len(key), value)
    #     break

    count_accept, count_logerror, count_undecided, ler, detect_normal, decoding_normal = \
        get_logical_error_on_accepted_states(
            n, lstate.upper(), counts, zpos_list
        )

    # Return structured result
    return {
        "n": n,
        "lstate": lstate,
        "i": i,
        "meas_type": meas_type,
        "p_error": p_error,
        "sim_type": sim_type,
        "shots": total_shots,
        "count_accept": count_accept,
        "count_logerror": count_logerror,
        "count_undecided": count_undecided,
        "count_detect_discard": count_detect_discard,
        "prep_rate": count_accept / (total_shots - count_detect_discard),
        "LER": 1 - ler,
        "detect_normal": detect_normal,
        "decoding_normal": decoding_normal,
    }
