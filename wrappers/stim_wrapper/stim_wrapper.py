import stim
# import random
# import csv
# import pandas as pd
import collections
import os
from wrappers.polar_wrapper import (divide_half_list, get_logical_error_on_accepted_states, get_q1prep_sr)
import json

from qiskit import QuantumCircuit
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

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



def noisy_cx(sim: stim.TableauSimulator, ctrl: int, targ: int, p: float, error_2q = None, initial_layout = None, cm = None):
    sim.cx(ctrl, targ)

    error_rate = p
    if error_2q != None:
        # pq = physical qubit
        pq_ctrl = initial_layout[ctrl]
        pq_targ = initial_layout[targ]

        path = cm.shortest_undirected_path(pq_ctrl, pq_targ)
        path_pairs = list(zip(path[:-1], path[1:]))

        fid_total = 1
        for pair in path_pairs:
            fid_total *= (1 - error_2q[pair])

        error_rate = (1 - fid_total) * p

    sim.depolarize2(ctrl,targ, p=error_rate)

def noisy_h(sim: stim.TableauSimulator, targ, p, error_1q = None, initial_layout = None):
    sim.h(targ)

    error_rate = p
    if error_1q != None:
        # pq = physical qubit
        pq_targ = initial_layout[targ]
        error_rate = error_1q[pq_targ] * p

    sim.depolarize1(targ, p=error_rate)

def noisy_x(sim: stim.TableauSimulator, targ, p, error_1q = None, initial_layout = None):
    sim.x(targ)
    error_rate = p
    if error_1q != None:
        # pq = physical qubit
        pq_targ = initial_layout[targ]
        error_rate = error_1q[pq_targ] * p

    sim.depolarize1(targ, p=error_rate)

def noisy_z(sim: stim.TableauSimulator, targ, p, error_1q = None, initial_layout = None):
    sim.z(targ)
    error_rate = p
    if error_1q != None:
        # pq = physical qubit
        pq_targ = initial_layout[targ]
        error_rate = error_1q[pq_targ] * p

    sim.depolarize1(targ, p=error_rate)

def noisy_reset(sim: stim.TableauSimulator, targ, p, error_1q = None, initial_layout = None):
    sim.reset(targ)
    error_rate = p
    if error_1q != None:
        # pq = physical qubit
        pq_targ = initial_layout[targ]
        error_rate = error_1q[pq_targ] * p

    sim.x_error(targ, p=error_rate)

def noisy_measurement(sim: stim.TableauSimulator, targ, p, error_meas = None, initial_layout = None):
    error_rate = p
    if error_meas != None:
        # pq = physical qubit
        pq_targ = initial_layout[targ]
        error_rate = error_meas[pq_targ] * p

    sim.x_error(targ, p=error_rate)
    sim.measure(targ)

def generate_circuit_extraction_syndrome_stim(sim: stim.TableauSimulator, k, meas_type, x_first = False, p_error = 0, start_idx = 0,
                                              error_1q = None, error_2q = None, initial_layout = None, cm=None
                                              ):
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
                noisy_h(sim, d1[idx], p=p_error, error_1q=error_1q, initial_layout=initial_layout)
                noisy_cx(sim, d1[idx], d2[idx], p=p_error, error_2q=error_2q, initial_layout=initial_layout, cm=cm)

            else:
                noisy_h(sim, ancillas[idx], p=p_error, error_1q=error_1q, initial_layout=initial_layout)
                noisy_cx(sim, ancillas[idx], d1[idx], p=p_error, error_2q=error_2q, initial_layout=initial_layout, cm=cm)
                noisy_cx(sim, ancillas[idx], d2[idx], p=p_error, error_2q=error_2q, initial_layout=initial_layout, cm=cm)
                noisy_h(sim, ancillas[idx], p=p_error, error_1q=error_1q, initial_layout=initial_layout)


        elif meas_type.lower() == "z":
            noisy_cx(sim, d1[idx], ancillas[idx], p=p_error, error_2q=error_2q, initial_layout=initial_layout, cm=cm)
            noisy_cx(sim, d2[idx], ancillas[idx], p=p_error, error_2q=error_2q, initial_layout=initial_layout, cm=cm)


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

def simulate_stim_one_shot(n, lstate, sim_type, p_error, seed, 
                           error_1q, readout_error, error_2q,
                           meas_type, total_qubits, x_ind,
                           cm = None, initial_layout = None
                            ):
    
    count_detect_discard = 0
    sim = stim.TableauSimulator(seed=seed)

    error_detected_this_shot = False

    # initialization error
    for qb in range(total_qubits):
        noisy_reset(sim, qb, p_error, error_1q, initial_layout)

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
                generate_circuit_extraction_syndrome_stim(sim, level, meas_type[level - 1], x_first, p_error=p_error, start_idx=start_idx,
                                                            error_1q=error_1q, error_2q=error_2q, initial_layout=initial_layout, cm=cm)
        
            # with the simplification, the first measurement will be always 0
            if not x_first:
                for qb in range(2, total_qubits, 3): 
                    noisy_measurement(sim, qb, p_error, readout_error, initial_layout)
                    noisy_reset(sim, qb, p_error, error_1q, initial_layout)

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
        return "", True

    # Final measurements, simplified.
    for qb_idx in (j for j in range(total_qubits) if j % 3 != 2):
        if lstate == "x":
            noisy_h(sim, qb_idx, p_error, error_1q, initial_layout)
        noisy_measurement(sim, qb_idx, p_error, readout_error, initial_layout )
        

    final_measurements = sim.current_measurement_record()

    # Generate the bit string, reverse it, and update the counts.
    bit_string = ''.join(['1' if b else '0' for b in final_measurements])[::-1]

    if sim_type in ["m1", "m2"]:
        bit_string = bit_string + "0"*(2**(level - 1))

    return bit_string, False

def simulate_stim_polar_code(n, lstate, sim_type, i, p_error, shots, total_shots, total_meta_shots, seeds, backend = None, initial_layout = None,
                             target_accept_count = None):
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
    
    if backend != None:
        t1, t2, error_1q, readout_error, error_2q = get_backend_information(backend)
        cm = backend.coupling_map
    else:
        t1, t2, error_1q, readout_error, error_2q = None, None, None, None, None
        cm = None

    meas_type = convert_i_to_meas_type(i, n, lstate)
    N = 2**n
    ancilla_qubits = 2**(n - 1)

    counts = collections.Counter()
    bitstrings = []
    total_qubits = N + ancilla_qubits

    zpos_list = [-1, -1, 1, 3, 6, 7, 22, 15, 90, 31, 362]
    zpos_list[n] = i-1

    x_ind = 0
    for idx, m_type in enumerate(meas_type):
        if m_type == "x":
            x_ind = idx
            break

    count_detect_discard = 0
    seed = 0
    total_real_shot = total_meta_shots

    if target_accept_count == None:

        for shot_idx in range(shots):
            total_real_shot+= 1

            seed = seeds[shot_idx]
            bit_string, flag_discard = simulate_stim_one_shot(n, lstate, sim_type, p_error, seed, 
                            error_1q, readout_error, error_2q,
                            meas_type, total_qubits, x_ind,
                            cm = cm, initial_layout = initial_layout,
                            )

            if flag_discard:
                count_detect_discard += 1
                continue

            bitstrings.append(bit_string)
    else:

        while len(bitstrings) + total_shots < target_accept_count:
            total_real_shot+= 1
            seed += 1 

            bit_string, flag_discard = simulate_stim_one_shot(n, lstate, sim_type, p_error, seed, 
                            error_1q, readout_error, error_2q,
                            meas_type, total_qubits, x_ind,
                            cm = cm, initial_layout = initial_layout,
                            )

            if flag_discard:
                count_detect_discard += 1
                continue

            res = {}
            res[bit_string] = 1

            count_accept, count_logerror, count_undecided, ler, detect_normal, decoding_normal = \
        get_logical_error_on_accepted_states(
            n, lstate.upper(), res, zpos_list
        )
            if round(count_accept) == 0:
                # print("kebuang", bit_string, total_real_shot)
                continue

            # print(total_real_shot, seed, bit_string)

            bitstrings.append(bit_string)

    counts = collections.Counter(bitstrings)
    return counts, total_real_shot
    # return bitstrings

def get_processed_shots(n, lstate, p_error, i, sim_type, hw_name = None, target_accept_count = None):
    total_shots = 0

    # file_path = f"./output/STIM/n{n}/polar_n{n}_{lstate}_{i}_{p_error}_normal.txt"
    # if os.path.exists(file_path):
    #     with open(file_path, "r") as f:
    #         lines = f.read().splitlines()
    #         total_shots = len(lines)

    # file_path = f"./output/STIM/n{n}/polar_n{n}_{lstate}_{i}_{p_error}_normal.json"
    if target_accept_count != None:
        suffix_path = "_accepted"

    if hw_name != None:
        file_path = f"./output/STIM/n{n}/{hw_name}_polar_n{n}_{lstate}_{i}_{p_error}_{sim_type}{suffix_path}.json"
    else:
        file_path = f"./output/STIM/n{n}/polar_n{n}_{lstate}_{i}_{p_error}_{sim_type}{suffix_path}.json"

    if os.path.exists(file_path):
        with open(file_path, "r") as f:  # "a" means append mode
            loaded_dict = json.load(f)
            current_counter = collections.Counter(loaded_dict)
            total_shots = sum(current_counter.values())

    return total_shots

def get_meta_total_shots(n, lstate, p_error, i, sim_type, hw_name = None, target_accept_count = None):
    total_shots = 0

    if target_accept_count != None:
        suffix_path = "_accepted"

    if hw_name != None:
        file_path = f"./output/STIM/n{n}/{hw_name}_polar_n{n}_{lstate}_{i}_{p_error}_{sim_type}{suffix_path}_meta.json"
    else:
        file_path = f"./output/STIM/n{n}/polar_n{n}_{lstate}_{i}_{p_error}_{sim_type}{suffix_path}_meta.json"

    if os.path.exists(file_path):
        with open(file_path, "r") as f:  # "a" means append mode
            loaded_dict = json.load(f)
            total_shots = loaded_dict["total_real_shots"]

    return total_shots

def simulate_batch_and_save_result_polar(n, lstate, sim_type, p_error, i, shots, seed_starts, backend = None, initial_layout = None,
                                         target_accept_count = None):

    zpos_list = [-1, -1, 1, 3, 6, 7, 22, 15, 90, 31, 362]
    zpos_list[n] = i-1

    # to get total shots from the normal method files
    hw_name = None
    if backend != None:
        hw_name = backend.name

    total_shots = get_processed_shots(n, lstate, p_error, i, sim_type, hw_name=hw_name, target_accept_count=target_accept_count)
    total_meta_shots = get_meta_total_shots(n, lstate, p_error, i, sim_type, hw_name=hw_name, target_accept_count=target_accept_count)
    seed_list = range(total_shots, total_shots + shots + 1)
    
    # print(existing_data, seed_list[0], seed_list[-1])
    results, total_real_shots = simulate_stim_polar_code(n, lstate, sim_type, i, p_error, shots, total_shots, total_meta_shots, seed_list, backend=backend, initial_layout=initial_layout,
                                       target_accept_count=target_accept_count)
    
    print(n, lstate, sim_type, p_error, i, shots, total_shots, total_shots + shots + 1, "real shot:", total_real_shots)

    # file_path = f"./output/STIM/n{n}/polar_n{n}_{lstate}_{i}_{p_error}_{sim_type}.txt"
    # with open(file_path, "a") as f:  # "a" means append mode
    #     f.write("\n".join(results) + "\n")

    if target_accept_count != None:
        suffix_path = "_accepted"

    if backend != None:
        file_path = f"./output/STIM/n{n}/{backend.name}_polar_n{n}_{lstate}_{i}_{p_error}_{sim_type}{suffix_path}.json"
    else:
        file_path = f"./output/STIM/n{n}/polar_n{n}_{lstate}_{i}_{p_error}_{sim_type}{suffix_path}.json"

    if backend != None:
        meta_path = f"./output/STIM/n{n}/{backend.name}_polar_n{n}_{lstate}_{i}_{p_error}_{sim_type}{suffix_path}_meta.json"
    else:
        meta_path = f"./output/STIM/n{n}/polar_n{n}_{lstate}_{i}_{p_error}_{sim_type}{suffix_path}_meta.json"

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


    meta_dict = {
        "total_shots": total_shots,
        "shots": shots,
        "total_real_shots": total_real_shots,
        "lstate": lstate,
        "p_error": p_error,
        "sim_type": sim_type
        }
    
    with open(meta_path, "w") as f:  # "a" means append mode
        json.dump(meta_dict, f)


def calculate_logical_error_result_polar(n, lstate, i, p_error, sim_type, shots, hw_name, target_accept_count):
    #m1 circuit simplify
    #m2 m1 + error detection

    meas_type = convert_i_to_meas_type(i, n, lstate)
    # print(n, lstate, i, p_error, sim_type, meas_type, shots, target_accept_count)

    # to get total shots from the normal method files
    total_shots = get_processed_shots(n, lstate, p_error, i, sim_type, hw_name, target_accept_count)
    total_meta_shots = get_meta_total_shots(n, lstate, p_error, i, sim_type, hw_name, target_accept_count)

    # file_path = f"./output/STIM/n{n}/polar_n{n}_{lstate}_{i}_{p_error}_{sim_type}.txt"
    # if not os.path.exists(file_path):
    #     return None  # skip missing files

    # with open(file_path, "r") as f:
    #     lines = f.read().splitlines()

    # shots_remained = len(lines)
    # count_detect_discard = total_shots - shots_remained
    # counts = collections.Counter(lines)
    if target_accept_count != None:
        suffix_path = "_accepted"

    if hw_name != None:
        file_path = f"./output/STIM/n{n}/{hw_name}_polar_n{n}_{lstate}_{i}_{p_error}_{sim_type}{suffix_path}.json"
    else:
        file_path = f"./output/STIM/n{n}/polar_n{n}_{lstate}_{i}_{p_error}_{sim_type}{suffix_path}.json"

    try:
        with open(file_path, "r") as f:  # "a" means append mode
            loaded_dict = json.load(f)
            current_counter = collections.Counter(loaded_dict)
            shots_remained = sum(current_counter.values())

    except FileNotFoundError:
        return None
    

    # print("shots :", shots, total_shots, shots_remained, file_path)
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
    
    # print(file_path, shots_remained, sum(counts.values()), count_accept, 1-ler)

    print(n, lstate, i, p_error, sim_type, total_meta_shots, count_accept, total_shots, count_detect_discard, "t:", (total_shots - count_detect_discard))
    # Return structured result
    return {
        "n": n,
        "lstate": lstate,
        "i": i,
        "meas_type": meas_type,
        "p_error": p_error,
        "sim_type": sim_type,
        "total_meta_shots": total_meta_shots,
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

#Region Qiskit Region
def get_backend_information(backend):

    properties = backend.properties()
    num_qubits = backend.num_qubits
    coupling_map = backend.coupling_map

    # We define various lists of metrics for all the qubits of the backend
    t1, t2, gate_error_x, readout_error, gate_error_cz = {}, {}, {}, {}, {}
    for i in range(num_qubits):
        # t1.append(properties.t1(i))
        # t2.append(properties.t2(i))
        # gate_error_x.append(properties.gate_error(gate="x", qubits=i))
        # readout_error.append(properties.readout_error(i))
        t1[i] = properties.t1(i)
        t2[i] = properties.t2(i)
        gate_error_x[i] = properties.gate_error(gate="x", qubits=i)
        readout_error[i] = properties.readout_error(i)

    if backend.name == "ibm_torino":
        for pair in coupling_map:
            gate_error_cz[pair] = properties.gate_error(gate="cz", qubits=pair)
    elif backend.name == "ibm_brisbane":
        for pair in coupling_map:
            gate_error_cz[pair] = properties.gate_error(gate="ecr", qubits=pair)
            gate_error_cz[(pair[1], pair[0])] = properties.gate_error(gate="ecr", qubits=pair)

    
    return t1, t2, gate_error_x, readout_error, gate_error_cz

def generate_circuit_extraction_syndrome(k, meas_type, x_first = False):
    num_qbits = (2**k) + (2**(k-1))
    num_cbits = 2**(k-1)

    qc = QuantumCircuit(num_qbits, num_cbits)

    data_qubits = []
    ancillas = []
    for i in range(2**(k-1)):
        ancillas.append(i *3 + 2)

    for i in range(num_qbits):
        if i not in ancillas:
            data_qubits.append(i)

    d1, d2 = divide_half_list(data_qubits)
    #print(d1,d2, ancillas)

    for idx in range(len(d1)):

        if meas_type.lower() == "x":

            if x_first:
                qc.h(d1[idx])
                qc.cx(d1[idx], d2[idx])
            else:
                qc.h(ancillas[idx])
                qc.cx(ancillas[idx], d1[idx])
                qc.cx(ancillas[idx], d2[idx])
                qc.h(ancillas[idx])
                
                # qc.measure(ancillas[idx], idx)
                # qc.reset(ancillas[idx])

        elif meas_type.lower() == "z":
            qc.cx(d1[idx], ancillas[idx])
            qc.cx(d2[idx], ancillas[idx])

            # qc.measure(ancillas[idx], idx)
            # qc.reset(ancillas[idx])
    
    return qc

def generate_qiskit_polar_code(n, lstate, sim_type, i):
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
    cbits = ( ancilla_qubits * n ) + N
    qc = QuantumCircuit(total_qubits, cbits)
    error_detected_this_shot = False

    m_idx = 0
    for level in range(1, n+1):

        # print(level, "-", meas_type[level - 1])
        
        num_loops = 2**(n - level)
        start_idx_mult = 2**(level) + 2**(level - 1)

        if sim_type in ["m1", "m2"] and level == x_ind + 1:
            x_first = True
            m_idx += ancilla_qubits
            # print("m_idx =", m_idx)
        else:
            x_first = False

        if level <= x_ind:
            # skip the beginning of zz measurement
            # print("skip :" , level, x_ind)
            # m_idx += ancilla_qubits
            # print("m_idx =", m_idx)
            pass
        else:
            # print("num_loops :", num_loops)
            for loop_idx in range(num_loops):
                start_idx = loop_idx * start_idx_mult
                circ = generate_circuit_extraction_syndrome(level, meas_type[level - 1], x_first)
                clbits = range(2**(level-1)) 

                # print(start_idx, level, clbits, total_qubits, cbits, start_idx_mult)
                qc.append(circ, range(start_idx, start_idx + start_idx_mult), clbits)
        
            # with the simplification, the first measurement will be always 0
            if not x_first:
                for qb in range(2, total_qubits, 3): 
                    qc.measure(qb, m_idx)
                    qc.reset(qb)
                    m_idx += 1


    qc = qc.decompose()
    # Final measurements, simplified.
    for qb_idx in (j for j in range(total_qubits) if j % 3 != 2):
        if lstate == "x":
            qc.h(qb_idx)
        qc.measure(qb_idx, m_idx)
        m_idx += 1
    
    return qc

def compiled_to_qiskit_hardware(qc, backend, optimization_level = 3, seed_transpiler = 12345):
    basis_gates = backend.configuration().basis_gates
    if 'cx' not in basis_gates:
        basis_gates = basis_gates + ['cx']
        basis_gates = basis_gates + ['h']


    ## change later back to 3
    pm = generate_preset_pass_manager(
        optimization_level=3, backend=backend,
        seed_transpiler=seed_transpiler
        )
    
    tqc = pm.run(qc)

    return tqc