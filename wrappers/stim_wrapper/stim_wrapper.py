import stim
# import random
# import csv
import pandas as pd
import collections
import os
from wrappers.polar_wrapper import (divide_half_list, get_logical_error_on_accepted_states, get_q1prep_sr)
import json

from qiskit import QuantumCircuit
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit.converters import circuit_to_dag, dag_to_circuit  

import glob
import sys
import numpy as np

def convert_i_to_meas_type(i, n, lstate = "z"):
    bit_format = "0:0{}b".format(n)
    bit_format = "{" + bit_format + "}" 

    if lstate == "z":
        zpos = i-1
    else:
        zpos = i-2

    n_bit = bit_format.format(zpos)[::-1]
    meas_type = ['x' if char == '0' else 'z' for char in n_bit]
    
    # print(n, lstate, i, n_bit, meas_type)

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

    print(n, lstate, sim_type, i, p_error, shots, total_shots, total_meta_shots, seeds, meas_type)

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

            # bitstrings.append(bit_string)
            # counts.update([bit_string])
            counts[bit_string] += 1
    else:

        while sum(counts.values()) + total_shots < target_accept_count:
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

            # bitstrings.append(bit_string)
            # counts.update([bit_string])
            counts[bit_string] += 1

    # counts = collections.Counter(bitstrings)
    
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
    
    print(n, lstate, sim_type, p_error, i, shots, total_shots, total_shots + shots, "real shot:", total_real_shots)

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
                # qc.cz(d1[idx], d2[idx])
            else:
                qc.h(ancillas[idx])
                qc.cx(ancillas[idx], d1[idx])
                qc.cx(ancillas[idx], d2[idx])
                # qc.cz(ancillas[idx], d1[idx])
                # qc.cz(ancillas[idx], d2[idx])
                qc.h(ancillas[idx])
                
                # qc.measure(ancillas[idx], idx)
                # qc.reset(ancillas[idx])

        elif meas_type.lower() == "z":
            qc.cx(d1[idx], ancillas[idx])
            qc.cx(d2[idx], ancillas[idx])
            # qc.cz(d1[idx], ancillas[idx])
            # qc.cz(d2[idx], ancillas[idx])

            # qc.measure(ancillas[idx], idx)
            # qc.reset(ancillas[idx])
    
    return qc

def generate_qiskit_polar_code(n, lstate, sim_type, i, skip_reset=False):
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

    if not skip_reset:
        # initialization
        for i in range(total_qubits):
            qc.reset(i)

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
    # Compile first to get the initial layout with the noise-aware
    pm = generate_preset_pass_manager(
        optimization_level=optimization_level, backend=backend,
        seed_transpiler=seed_transpiler)
    tqc = pm.run(qc)

    initial_layout = tqc.layout.initial_index_layout(filter_ancillas=True)
    # print(hw_name, seed_transpiler, initial_layout)

    basis_gates = backend.configuration().basis_gates
    if 'cx' not in basis_gates:
            basis_gates = basis_gates + ['cx']
            basis_gates = basis_gates + ['h']
            basis_gates = basis_gates + ['swap']

    pm = generate_preset_pass_manager(
            optimization_level=3, backend=backend,        
            seed_transpiler=seed_transpiler,
            initial_layout=initial_layout,
            basis_gates=basis_gates
            )
        
    tqc_new = pm.run(qc)

    return tqc_new


    ## change later back to 3
    pm = generate_preset_pass_manager(
        optimization_level=3, backend=backend,
        seed_transpiler=seed_transpiler,
        basis_gates=basis_gates
        )
    
    tqc = pm.run(qc)

    return tqc

# -------------- STIM with Normal Simulation ------------------

def generate_circuit_extraction_syndrome_stim_normal(circuit: stim.Circuit, k, meas_type, x_first = False, p_error = 0, start_idx_list = [0],
                                              error_1q = None, error_2q = None, readout_error = None, initial_layout = None, cm=None
                                              ):
    
    num_qbits = (2**k) + (2**(k-1))
    num_cbits = 2**(k-1)
    h_1 = []
    h_2 = []
    cnot_1 = []
    cnot_2 = []
    m = []
    r = []

    for start_idx in start_idx_list:
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
                    h_1.append(d1[idx])
                    cnot_1.append(d1[idx])
                    cnot_1.append(d2[idx])

                else:
                    h_1.append(ancillas[idx])
                    cnot_1.append(ancillas[idx])
                    cnot_1.append(d1[idx])
                    cnot_2.append(ancillas[idx])
                    cnot_2.append(d2[idx])
                    h_2.append(ancillas[idx])
                    m.append(ancillas[idx])
                    r.append(ancillas[idx])

            elif meas_type.lower() == "z":
                cnot_1.append(d1[idx])
                cnot_1.append(ancillas[idx])
                cnot_2.append(d2[idx])
                cnot_2.append(ancillas[idx])
                m.append(ancillas[idx])
                r.append(ancillas[idx])

    if len(h_1) > 0: 
        circuit.append("H", h_1)

        if error_1q != None:
            for idx in h_1:
                pq_targ = initial_layout[idx]
                error_rate = error_1q[pq_targ] * p_error
                circuit.append("X_ERROR", idx, error_rate)    
        else:
            circuit.append("X_ERROR", h_1, p_error)

    if len(cnot_1) > 0: 
        circuit.append("CNOT", cnot_1)

        if error_2q != None:
            for ctrl, targ in zip(cnot_1[::2], cnot_1[1::2]):
                # pq = physical qubit
                pq_ctrl = initial_layout[ctrl]
                pq_targ = initial_layout[targ]

                path = cm.shortest_undirected_path(pq_ctrl, pq_targ)
                path_pairs = list(zip(path[:-1], path[1:]))

                fid_total = 1
                for pair in path_pairs:
                    fid_total *= (1 - error_2q[pair])

                error_rate = (1 - fid_total) * p_error

                circuit.append("DEPOLARIZE2", [ctrl, targ], error_rate)
        else:
            circuit.append("DEPOLARIZE2", cnot_1, p_error)

    
    if len(cnot_2) > 0: 
        circuit.append("CNOT", cnot_2)

        if error_2q != None:
            for ctrl, targ in zip(cnot_2[::2], cnot_2[1::2]):
                # pq = physical qubit
                pq_ctrl = initial_layout[ctrl]
                pq_targ = initial_layout[targ]

                path = cm.shortest_undirected_path(pq_ctrl, pq_targ)
                path_pairs = list(zip(path[:-1], path[1:]))

                fid_total = 1
                for pair in path_pairs:
                    fid_total *= (1 - error_2q[pair])

                error_rate = (1 - fid_total) * p_error

                circuit.append("DEPOLARIZE2", [ctrl, targ], error_rate)
        else:
            circuit.append("DEPOLARIZE2", cnot_2, p_error)

    if len(h_2) > 0: 
        circuit.append("H", h_2)

        if error_1q != None:
            for idx in h_2:
                pq_targ = initial_layout[idx]
                error_rate = error_1q[pq_targ] * p_error
                circuit.append("X_ERROR", idx, error_rate)    
        else:
            circuit.append("X_ERROR", h_2, p_error)

    if len(m) > 0: 
        if error_1q != None:
            for idx in m:
                pq_targ = initial_layout[idx]
                error_rate = error_1q[pq_targ] * p_error
                circuit.append("X_ERROR", idx, error_rate)    
        else:
            circuit.append("X_ERROR", m, p_error)

        circuit.append("M", m)

    if len(r) > 0: 
        circuit.append("R", r)
        if error_1q != None:
            for idx in r:
                pq_targ = initial_layout[idx]
                error_rate = error_1q[pq_targ] * p_error
                circuit.append("X_ERROR", idx, error_rate)    
        else:
            circuit.append("X_ERROR", r, p_error)

def create_circuit_polar_stim_normal(n, lstate, sim_type, p_error, seed, shots, 
                           error_1q, readout_error, error_2q,
                           meas_type, total_qubits, x_ind,
                           cm = None, initial_layout = None
                            ):

    circuit = stim.Circuit()

    # initialization error
    r_start = []
    for i in range(total_qubits):
        r_start.append(i)

    circuit.append("R", r_start)
    if error_1q != None:
        for idx in r_start:
            pq_targ = initial_layout[idx]
            error_rate = error_1q[pq_targ] * p_error
            circuit.append("X_ERROR", idx, error_rate)    
    else:
        circuit.append("X_ERROR", r_start, p_error)

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
            
            start_idx_list = []

            for loop_idx in range(num_loops):
                start_idx = loop_idx * start_idx_mult
                start_idx_list.append(start_idx)
            
            # print("meas_type:", meas_type, level-1)

            generate_circuit_extraction_syndrome_stim_normal(circuit, level, meas_type[level - 1], x_first, p_error=p_error, start_idx_list=start_idx_list,
                                                        error_1q=error_1q, error_2q=error_2q, readout_error=readout_error, initial_layout=initial_layout, cm=cm)
        
    # Final measurements
    h_last = []
    m_last = []
    for qb_idx in (j for j in range(total_qubits) if j % 3 != 2):
        if lstate.lower() == "x":
            h_last.append(qb_idx)
        m_last.append(qb_idx)
        
    circuit.append("H", h_last)
    if error_1q != None:
        for idx in h_last:
            pq_targ = initial_layout[idx]
            error_rate = error_1q[pq_targ] * p_error
            circuit.append("X_ERROR", idx, error_rate)    
    else:
        circuit.append("X_ERROR", h_last, p_error)

    if error_1q != None:
        for idx in m_last:
            pq_targ = initial_layout[idx]
            error_rate = error_1q[pq_targ] * p_error
            circuit.append("X_ERROR", idx, error_rate)    
    else:
        circuit.append("X_ERROR", m_last, p_error)
    circuit.append("M", m_last) 
    

    # circuit = add_stim_error(circuit, p_error)
    # circuit.diagram("timeline-svg")

    return circuit

def simulate_stim_polar_code_normal(n, lstate, sim_type, i, p_error, shots, seed, backend = None, initial_layout = None):
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
    total_qubits = N + ancilla_qubits

    x_ind = 0
    for idx, m_type in enumerate(meas_type):
        if m_type == "x":
            x_ind = idx
            break

    circuit = create_circuit_polar_stim_normal(n, lstate, sim_type, p_error, seed, shots, 
                           error_1q, readout_error, error_2q,
                           meas_type, total_qubits, x_ind,
                           cm = cm, initial_layout = initial_layout
                            )
    
    sampler = circuit.compile_sampler(seed=seed)
    results = sampler.sample(shots=int(shots) )

    counts = {}
    for res in results:
        bit_string = ""
        for i in res:
            if i:
                bit_string = "1" + bit_string 
            else:
                bit_string = "0" + bit_string

        if sim_type in ["m1", "m2"]:
            bit_string = bit_string + "0"*(2**(n - 1))

        if bit_string in counts:
            counts[bit_string] = counts[bit_string] + 1
        else:
            counts[bit_string] = 1   
    
    return counts

def simulate_batch_and_save_result_polar_normal(n, lstate, sim_type, p_error, i, shots, seed):

    zpos_list = [-1, -1, 1, 3, 6, 7, 22, 15, 90, 31, 362]
    zpos_list[n] = i-1

    results = simulate_stim_polar_code_normal(n, lstate, sim_type, i, p_error, shots, seed)
    
    print(n, lstate, sim_type, p_error, i, shots)

    # file_path = f"./output/STIM/n{n}/polar_n{n}_{lstate}_{i}_{p_error}_{sim_type}.txt"
    # with open(file_path, "a") as f:  # "a" means append mode
    #     f.write("\n".join(results) + "\n")

    file_path = f"./output/STIM/normal/n{n}/polar_n{n}_{lstate}_{i}_{p_error}_{sim_type}_{seed}.json"

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

def calculate_logical_error_result_polar_normal(n, lstate, i, p_error, sim_type, seed):
    meas_type = convert_i_to_meas_type(i, n, lstate)

    file_path = f"./output/STIM/normal/n{n}/polar_n{n}_{lstate}_{i}_{p_error}_{sim_type}_{seed}.json"    
         
    try:
        with open(file_path, "r") as f:  # "a" means append mode
            loaded_dict = json.load(f)
            current_counter = collections.Counter(loaded_dict)
            shots_remained = sum(current_counter.values())

    except FileNotFoundError:
        return None
    
    counts = dict(current_counter)
    total_shots = sum(counts.values())

    zpos_list = [-1, -1, 1, 3, 6, 7, 22, 15, 90, 31, 362]
    zpos_list[n] = i - 1

    count_accept, count_logerror, count_undecided, ler, detect_normal, decoding_normal = \
        get_logical_error_on_accepted_states(
            n, lstate.upper(), counts, zpos_list
        )

    print(n, lstate, i, p_error, sim_type, count_accept)
    # Return structured result
    return {
        "n": n,
        "lstate": lstate,
        "i": i,
        "meas_type": meas_type,
        "p_error": p_error,
        "sim_type": sim_type,
        "total_meta_shots": 0,
        "shots": total_shots,
        "count_accept": count_accept,
        "count_logerror": count_logerror,
        "count_undecided": count_undecided,
        "count_detect_discard": 0,
        "prep_rate": count_accept / (total_shots - 0),
        "LER": 1 - ler,
        "detect_normal": detect_normal,
        "decoding_normal": decoding_normal,
    }


# -------------- STIM with Normal Simulation From Qiskit Compilation ------------------

def compile_circuit_qiskit_to_stim(tqc, backend, p_error):
    dag = circuit_to_dag(tqc)
    circuit = stim.Circuit()
    m_order = []

    t1, t2, error_1q, readout_error, error_2q = get_backend_information(backend)

    for idx, layer in enumerate(dag.layers()):
        layer_as_circuit = dag_to_circuit(layer['graph']) 

        for g in layer_as_circuit:
            
            op = g.operation
            qbits = g.qubits
            cbits = g.clbits
            qb1 = qbits[0]._index
            # print(op, qbits, cbits, op)

            if op.num_qubits == 1:
                # print(op.name, op.num_qubits, qbits[0]._index)
                if op.name == "h":
                    error_rate = error_1q[qb1] * p_error

                    circuit.append(op.name, qb1)
                    circuit.append("DEPOLARIZE1", qb1, error_rate)
                    
                elif op.name == "reset":
                    error_rate = error_1q[qb1] * p_error

                    circuit.append("r", qb1)
                    circuit.append("X_ERROR", qb1, error_rate)

                elif op.name == "measure":
                    error_rate = readout_error[qb1] * p_error

                    circuit.append("X_ERROR", qb1, error_rate)
                    circuit.append("m", qb1)
                    
                    m_order.append(cbits[0]._index)
                    # print(g)
                    
            else:
                qb2 = qbits[1]._index
                error_rate = error_2q[(qb1, qb2)] * p_error

                if op.name == "cx":
                    circuit.append(op.name, [qb1, qb2])
                    circuit.append("DEPOLARIZE2", [qb1, qb2], error_rate)
                elif op.name == "swap":
                    circuit.append("cx", [qb1, qb2])
                    circuit.append("DEPOLARIZE2", [qb1, qb2], error_rate)
                    circuit.append("cx", [qb2, qb1])
                    circuit.append("DEPOLARIZE2", [qb1, qb2], error_rate)
                    circuit.append("cx", [qb1, qb2])
                    circuit.append("DEPOLARIZE2", [qb1, qb2], error_rate)

    return circuit, m_order
                    
def create_circuit_polar_stim_from_qiskit(n, lstate, sim_type, i, p_error, seed, backend
                            ):

    circuit = stim.Circuit()

    qc = generate_qiskit_polar_code(n, lstate.lower(), sim_type, i)
    tqc = compiled_to_qiskit_hardware(qc, backend, 3, seed)

    circuit, m_order = compile_circuit_qiskit_to_stim(tqc, backend, p_error)
    
    new_m_order = []
    if sim_type in ["m1", "m2"]:
        for idx in range(2**(n - 1)):
            new_m_order.append(idx)

        for idx in m_order:
            new_m_order.append(idx)
    else:
        new_m_order = m_order

    return circuit, new_m_order    

def simulate_stim_polar_code_normal_from_qiskit_circuit(n, lstate, sim_type, i, p_error, shots, seed, backend):
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
    total_qubits = N + ancilla_qubits

    x_ind = 0
    for idx, m_type in enumerate(meas_type):
        if m_type == "x":
            x_ind = idx
            break

    circuit, m_order = create_circuit_polar_stim_from_qiskit(n, lstate, sim_type, i, p_error, seed, backend)
    
    sampler = circuit.compile_sampler(seed=seed)
    results = sampler.sample(shots=int(shots) )

    res_bit_string = {}
    for res in results:
        bit_string = ""

        if sim_type in ["m1", "m2"]:
            bit_string = bit_string + "0"*(2**(n - 1))

        for i in res:
            if i:
                bit_string = bit_string + "1" 
            else:
                bit_string = bit_string + "0"

        # print(len(bit_string), bit_string, m_order)

        new_bits = [''] * len(bit_string)

        # Loop through each bit in the original string
        for i in range(len(bit_string)):
            # Get the bit from the original string
            original_bit = bit_string[i]
            
            # Get the new position for this bit from the order list
            new_position = m_order[i]
            
            # Place the bit in its new position
            new_bits[new_position] = original_bit

        reordered_string = "".join(new_bits)[::-1]


        if reordered_string in res_bit_string:
            res_bit_string[reordered_string] = res_bit_string[reordered_string] + 1
        else:
            res_bit_string[reordered_string] = 1

    return res_bit_string

def simulate_batch_and_save_result_polar_qiskit(n, lstate, sim_type, p_error, i, shots, seed, backend):
  
    results = simulate_stim_polar_code_normal_from_qiskit_circuit(n, lstate, sim_type, i, p_error, shots, seed, backend)
    
    print(n, lstate, sim_type, p_error, i, shots)

    file_path = f"./output/STIM/qiskit/n{n}/{backend.name}_polar_n{n}_{lstate}_{i}_{p_error}_{sim_type}_{seed}.json"

    try:
        with open(file_path, "r") as f:  
            loaded_dict = json.load(f)
            current_counter = collections.Counter(loaded_dict)

    except FileNotFoundError:
        current_counter = collections.Counter()

    # updating the counter with the new results
    current_counter.update(results)

    with open(file_path, "w") as f:  
        json.dump(dict(current_counter), f)

def calculate_logical_error_result_polar_qiskit(n, lstate, i, p_error, sim_type, hw_name, seed):
    #m1 circuit simplify
    #m2 m1 + error detection

    meas_type = convert_i_to_meas_type(i, n, lstate)

    file_path = f"./output/STIM/qiskit/n{n}/{hw_name}_polar_n{n}_{lstate}_{i}_{p_error}_{sim_type}_{seed}.json"

    try:
        with open(file_path, "r") as f:  # "a" means append mode
            loaded_dict = json.load(f)
            current_counter = collections.Counter(loaded_dict)
            shots_remained = sum(current_counter.values())

    except FileNotFoundError:
        return None
    
    counts = dict(current_counter)
    total_shots = sum(counts.values())

    zpos_list = [-1, -1, 1, 3, 6, 7, 22, 15, 90, 31, 362]
    zpos_list[n] = i - 1

    count_accept, count_logerror, count_undecided, ler, detect_normal, decoding_normal = \
        get_logical_error_on_accepted_states(
            n, lstate.upper(), counts, zpos_list
        )
    

    print(n, lstate, i, meas_type, p_error, sim_type, count_accept, total_shots)
    # Return structured result
    return {
        "n": n,
        "lstate": lstate,
        "i": i,
        "meas_type": meas_type,
        "p_error": p_error,
        "sim_type": sim_type,
        "total_meta_shots": 0,
        "shots": total_shots,
        "count_accept": count_accept,
        "count_logerror": count_logerror,
        "count_undecided": count_undecided,
        "count_detect_discard": 0,
        "prep_rate": count_accept / (total_shots - 0),
        "LER": 1 - ler,
        "detect_normal": detect_normal,
        "decoding_normal": decoding_normal,
    }

def combine_data(file_pattern, output_filename):
    """
    Finds, combines, and aggregates CSV files based on specified keys.
    """
    print(f"Looking for files matching: {file_pattern}")
    
    # 1. Find all files matching the pattern
    all_files = glob.glob(file_pattern)
    
    # Exclude the output file itself if it matches the pattern
    if output_filename in all_files:
        all_files.remove(output_filename)

    if not all_files:
        print("Error: No files found to combine. Check your FILE_PATTERN.")
        sys.exit()

    print(f"Found {len(all_files)} files. Reading and concatenating...")

    # 2. Load all files into a list of DataFrames
    df_list = []
    for f in all_files:
        try:
            df_list.append(pd.read_csv(f))
        except Exception as e:
            print(f"Warning: Could not read {f}. Error: {e}")

    if not df_list:
        print("Error: No files were successfully read.")
        sys.exit()

    # 3. Combine all DataFrames into one
    full_df = pd.concat(df_list, ignore_index=True)
    print("All files concatenated.")

    # 4. Define grouping keys and columns for aggregation
    grouping_keys = ['n', 'lstate', 'i', 'meas_type', 'p_error', 'sim_type']
    
    # These columns represent raw counts and should be SUMMED
    count_columns = [
        'total_meta_shots',
        'shots',
        'count_accept',
        'count_logerror',
        'count_undecided',
        'count_detect_discard',
        'detect_normal',
        'decoding_normal'
    ]
    
    # These columns are rates. We will calculate the MEAN for those
    # whose formula isn't obvious.
    rate_columns = [
        'LER',
    ]

    # Filter lists to only include columns that actually exist in the DataFrame
    present_keys = [col for col in grouping_keys if col in full_df.columns]
    present_counts = [col for col in count_columns if col in full_df.columns]
    present_rates = [col for col in rate_columns if col in full_df.columns]

    print(f"Grouping by: {present_keys}")

    # 5. Perform the aggregation
    
    # First, aggregate counts using sum()
    agg_df_counts = full_df.groupby(present_keys)[present_counts].sum()
    
    # Second, aggregate unknown rates using mean()
    agg_df_rates = full_df.groupby(present_keys)[present_rates].mean()
    
    # Join the two aggregated DataFrames back together
    agg_df = agg_df_counts.join(agg_df_rates).reset_index()

    # 6. Recalculate rates based on the new sums
    # From your example, prep_rate = count_accept / shots
    # We use np.where for safe division (avoids dividing by zero)
    
    if 'count_accept' in agg_df.columns and 'shots' in agg_df.columns:
        print("Recalculating 'prep_rate'...")
        agg_df['prep_rate'] = np.where(
            agg_df['shots'] > 0,              # Condition
            agg_df['count_accept'] / agg_df['shots'], # If true
            0                                 # If false
        )
    
    # Re-order columns to match the original input format
    original_order = [
        'n','lstate','i','meas_type','p_error','sim_type',
        'total_meta_shots','shots','count_accept','count_logerror',
        'count_undecided','count_detect_discard','prep_rate','LER',
        'detect_normal','decoding_normal'
    ]
    
    final_columns = [col for col in original_order if col in agg_df.columns]
    agg_df = agg_df[final_columns]

    # 7. Save the final DataFrame to a new CSV
    try:
        agg_df.to_csv(output_filename, index=False)
        print(f"\nSuccess! Combined data saved to: {output_filename}")
        
        # print("\n--- Head of new combined DataFrame ---")
        # print(agg_df.head())
        # print("--------------------------------------")

    except Exception as e:
        print(f"Error saving file: {e}")

def find_and_delete_files(pattern):
    """
    Finds files matching a pattern, asks for confirmation,
    and then deletes them.
    """
    print(f"Searching for files matching pattern: {pattern}\n")
    
    # 1. Find all files matching the pattern
    files_to_delete = glob.glob(pattern)
    
    if not files_to_delete:
        print("No files found matching that key. Exiting.")
        sys.exit()

    # # 2. List all files found and ask for confirmation
    # print("--- Files Found for Deletion ---")
    # for f in files_to_delete:
    #     # print(f)
    # print("----------------------------------")
    
    print("Deleting files...")
    deleted_count = 0
    error_count = 0
    
    for f in files_to_delete:
        try:
            os.remove(f)
            # print(f"Deleted: {f}")
            deleted_count += 1
        except OSError as e:
            print(f"Error deleting {f}: {e}")
            error_count += 1
            
    print(f"\nOperation complete. {deleted_count} file(s) deleted.")
    if error_count > 0:
        print(f"{error_count} file(s) could not be deleted.")
            
   