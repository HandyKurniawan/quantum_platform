import mysql.connector
import numpy as np
import json

from qiskit import *
from qiskit.result import *
from qiskit_ibm_runtime import QiskitRuntimeService, RuntimeJob, RuntimeJobV2
from qiskit.providers import JobStatus
from qiskit.primitives import SamplerResult, PrimitiveResult
from qiskit_ibm_runtime.utils.runner_result import RunnerResult
from commons import (Config, convert_utc_to_local, calculate_time_diff, get_count_1q, get_count_2q, 
    calculate_circuit_cost, get_correct_output_dict, calculate_success_rate_nassc, calculate_success_rate_tvd, 
    calculate_success_rate_polar, calculate_hellinger_distance, calculate_success_rate_tvd_new, 
    convert_to_json, is_mitigated, get_initial_mapping_json, normalize_counts, convert_dict_int_to_binary, reverse_string_keys, convert_dict_binary_to_int,
    sum_middle_digits_dict
)

import wrappers.qiskit_wrapper as qiskit_wrapper
import wrappers.polar_wrapper as polar_wrapper
import wrappers.database_wrapper as database_wrapper

from wrappers.qiskit_wrapper import QiskitCircuit

from qiskit.qasm2 import dumps
from qiskit_aer import AerSimulator
# import traceback

conf = Config()

def check_result_availability(job: (RuntimeJob | RuntimeJobV2), header_id):
    
    print("Job status :", job.status())

    if(job.errored() or job.cancelled()):
        database_wrapper.update_result_header_status_by_header_id(header_id, "error")
        return False

    if(not job.done()):
        return False

    if(job.done()):
        return True

def get_result(job: (RuntimeJob | RuntimeJobV2)):        
    try:
        conn = mysql.connector.connect(**conf.mysql_config)
        cursor = conn.cursor()

        job_id = job.job_id()

        # get list of detail_id here
        cursor.execute('''SELECT d.id, h.shots FROM framework.result_header h 
INNER JOIN framework.result_detail d ON h.id = d.header_id
WHERE h.status = %s AND h.job_id = %s;''', ('pending', job_id, ))
        results_details = cursor.fetchall()

        if (type(job.result()) is PrimitiveResult):
            # quasi_dists = job.result().quasi_dists
            job_results = job.result()

            avg_result = {}
            std_json = {}
            qasm_dict = {}
            mitigation_overhead_dict = {}
            mitigation_time_dict = {}
            no_of_optimization = len(results_details)
            no_of_result = len(job_results)
            runs = int(no_of_result / no_of_optimization)
            idx_1, idx_2 = 0, 0

            for idx, res in enumerate(results_details):
                detail_id, shots = res
                avg_result[detail_id] = []
                std_json[detail_id] = []
                qasm_dict[detail_id] = []
                mitigation_overhead_dict[detail_id] = None
                mitigation_time_dict[detail_id] = None
                sum_result = {}
                std_dev = {}
                std_dict = {}

                # to initialize the dict
                for j in range(runs):
                    res_dict = convert_dict_binary_to_int(job_results[idx_1].data.c.get_counts())

                    for key, value in res_dict.items():
                        key_bin = key
                        sum_result[key_bin] = 0
                        std_dict[key_bin] = 0
                        std_dev[key_bin] = []
                        
                    idx_1 += 1

                # to put them together
                for j in range(runs):
                    res_dict = convert_dict_binary_to_int(job_results[idx_2].data.c.get_counts())
                    
                    for key, value in res_dict.items():
                        key_bin = key
                        sum_result[key_bin] += (value / shots)
                        std_dev[key_bin].append((value / shots))
                        
                    idx_2 += 1
                    
                for key, value in sum_result.items():
                    sum_result[key] /= runs
                    std_dict[key] = np.std(std_dev[key])

                avg_result[detail_id] = convert_to_json(sum_result)
                std_json[detail_id] = convert_to_json(std_dict)
                qasm_dict[detail_id] = dumps(job.inputs["pubs"][idx_2-1][0])

                if is_mitigated(job):
                    mitigation_overhead_dict[detail_id] = job.result().metadata[idx_2-1]["readout_mitigation_overhead"]
                    mitigation_time_dict[detail_id] = job.result().metadata[idx_2-1]["readout_mitigation_time"]

            for idx, res in enumerate(results_details):
                detail_id, shots = res
                job_results = avg_result[detail_id]
                job_results_std = std_json[detail_id]
                qasm = qasm_dict[detail_id]
                mapping_json = get_initial_mapping_json(qasm)
                mitigation_overhead = mitigation_overhead_dict[detail_id]
                mitigation_time = mitigation_time_dict[detail_id]

                # check if the result_backend_json is already there, just update
                cursor.execute('SELECT detail_id FROM result_backend_json WHERE detail_id = %s', (detail_id,))
                existing_row = cursor.fetchone()

                if existing_row:
                    cursor.execute('''UPDATE result_backend_json SET quasi_dists = %s, quasi_dists_std = %s, qasm = %s, 
                    shots = %s, mapping_json = %s, mitigation_overhead = %s, mitigation_time = %s  WHERE detail_id = %s;''',
                    (job_results, job_results_std, qasm, shots, mapping_json, mitigation_overhead, mitigation_time, detail_id))
                else:
                    cursor.execute('''INSERT INTO result_backend_json 
                                    (detail_id, quasi_dists, quasi_dists_std, qasm, shots, mapping_json, mitigation_overhead, mitigation_time) 
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
                    (detail_id, job_results, job_results_std, qasm, shots, mapping_json, mitigation_overhead, mitigation_time))
                

                database_wrapper.update_result_header(cursor, job)

            conn.commit()
        
        else:
            pass

        cursor.close()
        conn.close()

    except Exception as e:
        print("Error for check result availability :", str(e))

def process_simulator(service:QiskitRuntimeService, 
                      header_id: int, 
                      job_id: str, 
                      hw_name: str, 
                      noisy_simulator:AerSimulator = None):
    print("Checking results for: ", job_id, "with header id :", header_id)
    

    conn = mysql.connector.connect(**conf.mysql_config)
    cursor = conn.cursor()

    backend = None
    
    if noisy_simulator == None:
        backend = service.backend(hw_name)
    else:
        backend = noisy_simulator
        print(backend.backend_name)

    cursor.execute('''SELECT d.id, q.updated_qasm, d.compilation_name, d.noise_level, h.shots, h.seed 
FROM result_detail d
INNER JOIN result_header h ON d.header_id = h.id
INNER JOIN result_updated_qasm q ON d.id = q.detail_id 
LEFT JOIN framework.result_backend_json j ON d.id = j.detail_id
WHERE h.status = %s AND h.job_id = %s AND d.header_id = %s AND j.quasi_dists IS NULL  ''', ('pending', job_id, header_id,))
    results_details = cursor.fetchall()

    # print(len(results_details))
    for idx, res in enumerate(results_details):

        try:

            detail_id, updated_qasm, compilation_name, noise_level, shots, seed_simulator = res

            qc = QiskitCircuit(updated_qasm, skip_simulation=True)

            if compilation_name not in ("qiskit_3", "qiskit_0") and "nc" not in compilation_name:
            #if "nc" not in compilation_name:
                circuit = qc.transpile_to_target_backend(backend)
            else:
                circuit = qc.circuit_original
                # print(dumps(circuit))

            noiseless = False
            if noise_level == 0.0:
                noiseless = True
                print("Preparing the noiseless simulator", compilation_name, noise_level, noiseless)
                sim_ideal = AerSimulator()
                job = sim_ideal.run(circuit, shots=shots, seed_simulator=seed_simulator)
            elif noisy_simulator != None and isinstance(backend, AerSimulator):
                print("Preparing the custom noisy simulator", backend.name, compilation_name, noise_level, noiseless)
                job = backend.run(circuit, shots=shots, seed_simulator=seed_simulator)

            elif conf.user_id == 8:
                print("Preparing the noisy CX simulator", backend.name, compilation_name, noise_level, noiseless)

                sim_noisy = qiskit_wrapper.generate_sim_noise_cx(backend, noise_level)

                job = sim_noisy.run(circuit, shots=shots, seed_simulator=seed_simulator)

            else:
                print("Preparing the noisy simulator from backend", backend.name, compilation_name, noise_level, noiseless)
                noise_model, sim_noisy, coupling_map = qiskit_wrapper.get_noisy_simulator(backend, noise_level, noiseless)
                # noise_model, sim_noisy, coupling_map = qiskit_wrapper.get_noisy_simulator(backend, noise_level, noiseless=True)
                job = sim_noisy.run(circuit, shots=shots, seed_simulator=seed_simulator)

            # print("run the job")
            result = job.result()  
            # print("get result")
            output = result.get_counts()
            # print("get counts")
            output_normalize = normalize_counts(output, shots=shots)
            # print(output_normalize)

            quasi_dists = convert_to_json(output_normalize)
            quasi_dists_std = ""
            qasm = dumps(circuit)
            mapping_json = get_initial_mapping_json(qasm)
            mitigation_overhead = 0
            mitigation_time = 0

            # check if the result_backend_json is already there, just update
            cursor.execute('SELECT detail_id FROM result_backend_json WHERE detail_id = %s', (detail_id,))
            existing_row = cursor.fetchone()

            if existing_row:
                cursor.execute('''UPDATE result_backend_json SET quasi_dists = %s, quasi_dists_std = %s, qasm = %s, 
                shots = %s, mapping_json = %s, mitigation_overhead = %s, mitigation_time = %s  WHERE detail_id = %s;''',
                (quasi_dists, quasi_dists_std, qasm, shots, mapping_json, mitigation_overhead, mitigation_time, detail_id))
            else:
                cursor.execute('''INSERT INTO result_backend_json 
                                (detail_id, quasi_dists, quasi_dists_std, qasm, shots, mapping_json, mitigation_overhead, mitigation_time) 
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
                (detail_id, quasi_dists, quasi_dists_std, qasm, shots, mapping_json, mitigation_overhead, mitigation_time))

            conn.commit()

        except Exception as e:
            print("Error happened: ", str(e))

    cursor.execute('UPDATE result_header SET status = "executed", updated_datetime = NOW() WHERE id = %s', (header_id,))
    conn.commit()

    cursor.close()
    conn.close()
    

def get_metrics(header_id, job_id):
    # print("")
    print("Getting qasm for :", header_id, job_id)
    conn = mysql.connector.connect(**conf.mysql_config)
    cursor = conn.cursor()

    try:
        cursor.execute('''SELECT j.detail_id, j.qasm, j.quasi_dists, j.quasi_dists_std, d.circuit_name, 
                       d.compilation_name, d.noise_level, j.shots, d.mp_circuits, h.dd_enable, q.updated_qasm
                       FROM framework.result_backend_json j
        INNER JOIN framework.result_detail d ON j.detail_id = d.id
        INNER JOIN framework.result_header h ON d.header_id = h.id
        INNER JOIN framework.result_updated_qasm q ON q.detail_id = d.id
        WHERE h.status = %s AND h.job_id = %s AND h.id = %s AND j.quasi_dists IS NOT NULL;''', ("executed", job_id, header_id))
        results_details_json = cursor.fetchall()

        mp_data = []
        mp_total_clbits = 0
        success_rate_quasi = 0
        success_rate_nassc = 0
        success_rate_tvd = 0
        success_rate_tvd_new = 0
        hellinger_distance = 0

        # print(len(results_details_json))
        # updated qasm: this is the circuit qasm before adding delay and dd sequence
        # qasm: this is the circuit qasm after adding delay, but it is broken if dd is enabled.
        for idx, res in enumerate(results_details_json):
            detail_id, qasm, quasi_dists, quasi_dists_std, circuit_name, compilation_name, noise_level, shots, mp_circuits, dd_enable, updated_qasm = res

            mp_data.append({})

            n = 2
            lstate = "Z"
            if "polar_all_meas" in circuit_name:
                tmp = circuit_name.split("_")
                n = int(tmp[3][1])
                if len(tmp) == 5:
                    lstate = tmp[4].upper()
            elif "polar" in circuit_name:
                tmp = circuit_name.split("_")
                n = int(tmp[1][1])
                if len(tmp) == 3:
                    lstate = tmp[2].upper()
            
            # print(n, lstate, circuit_name)
            
            quasi_dists_dict = json.loads(quasi_dists) 
            count_dict = {}
            if (round(sum(quasi_dists_dict.values())) <= 1):
                for key, value in quasi_dists_dict.items():
                    count_dict[key] = value * shots
            else:
                count_dict = quasi_dists_dict


            # quasi_dists_std_dict = json.loads(quasi_dists_std) 
            
            
            
            # 20250328, Handy - Delay cannot be transpiled ot basis gates
            if dd_enable != 1:
                qc = QuantumCircuit.from_qasm_str(qasm)
                qc = qiskit_wrapper.transpile_to_basis_gate(qc)
            else:
                qc = QuantumCircuit.from_qasm_str(updated_qasm)
                
            
            total_gate = sum(qc.count_ops().values())
            total_one_qubit_gate = get_count_1q(qc)
            total_two_qubit_gate = get_count_2q(qc)
            circuit_depth = qc.depth()
            circuit_cost = calculate_circuit_cost(qc)

            count_accept = 0
            count_logerror = 0
            count_undecided = None
            decoding_time = None
            detection_time = None

            if "polar_all_meas" in circuit_name:
                print("get metrics: n =", n, ", lstate =", lstate)
                # total_qubit = (2**n) * (n)
                if lstate == "X":
                    if n == 2:
                        total_qubit = 8
                    elif n == 3:
                        total_qubit = 20
                    elif n == 4:
                        total_qubit = 40
                else:
                    if n == 2:
                        total_qubit = 6
                    elif n == 3:
                        total_qubit = 12
                    elif n == 4:
                        total_qubit = 48

                if mp_circuits != None:
                    count_dict_bin = convert_dict_int_to_binary(count_dict, total_qubit*mp_circuits)
                else:
                    count_dict_bin = convert_dict_int_to_binary(count_dict, total_qubit)

                # tmp = reverse_string_keys(count_dict_bin)

                tmp = count_dict_bin
                          
                # print(count_dict_bin)
                # print("----")
                # print(tmp)

                if mp_circuits == None:
                    count_accept, count_logerror, count_undecided, success_rate_polar, detection_time, decoding_time = polar_wrapper.get_logical_error_on_accepted_states(n, lstate, tmp)
                    print(circuit_name, noise_level, compilation_name, count_accept, count_logerror, count_undecided, success_rate_polar)
                else:
                    count_accept = 0
                    count_logerror = 0
                    count_undecided = 0 
                    success_rate_polar = 0 
                    detection_time = 0 
                    decoding_time = 0
                    
                    for key, value in tmp.items():
                        end_index = 0
                        start_index = None
                        
                        total_partition = mp_circuits
                        # total_partition = 6

                        # print(len(key), total_partition, value)
                    
                        total_count_accept = 0
                        for i in range(total_partition):
                            end_index = end_index - total_qubit
                    
                            tmp_dict = {key[end_index : start_index]:value}
                            # res = sum_middle_digits_dict(hardware_counts[-1], end_index, start_index)
                            # print(f"Reps-{i}")

                            # tmp_dict = reverse_string_keys(tmp_dict)

                            tmp_count_accept, tmp_count_logerror, tmp_count_undecided, tmp_success_rate_polar, tmp_detection_time, tmp_decoding_time =   polar_wrapper.get_logical_error_on_accepted_states(n, lstate, tmp_dict)
                            total_count_accept = total_count_accept + tmp_count_accept
                            
                            start_index = end_index
                    
                        if total_count_accept > 0:
                            count_accept = count_accept + value

                    print(circuit_name, noise_level, compilation_name, count_accept, len(tmp))

                success_rate_quasi = 0
                success_rate_nassc = 0
                success_rate_tvd = 0
                success_rate_tvd_new = 0
                hellinger_distance = 0

            elif "polar" in circuit_name:
                print("get metrics: n =", n, ", lstate =", lstate)
                # total_qubit = (2**n) * (n)
                if lstate == "X":
                    if n == 2:
                        total_qubit = (2**n)
                    elif n == 3:
                        total_qubit = 12
                    elif n == 4:
                        total_qubit = 24
                else:
                    if n == 2:
                        total_qubit = 0
                    elif n == 3:
                        total_qubit = 4
                    elif n == 4:
                        total_qubit = 32
                    
                quasi_dists_dict_bin = convert_dict_int_to_binary(quasi_dists_dict, total_qubit)
                tmp = reverse_string_keys(quasi_dists_dict_bin)
                # print(quasi_dists_dict_bin)
                # print("----")
                # print(tmp)
                success_rate_polar = polar_wrapper.get_q1prep_sr(n, lstate, tmp)
                print(circuit_name, noise_level, compilation_name, success_rate_polar)

                success_rate_quasi = 0
                success_rate_nassc = 0
                success_rate_tvd = 0
                success_rate_tvd_new = 0
                hellinger_distance = 0
            else:
                if mp_circuits == None:

                    correct_output = get_correct_output_dict(cursor, detail_id)

                    mp_data[idx]["correct_output"] = correct_output
                    mp_data[idx]["num_clbits"] = qc.num_clbits
                    mp_data[idx]["circuit_name"] = circuit_name
                    mp_total_clbits = mp_total_clbits + qc.num_clbits

                    success_rate_quasi = calculate_success_rate_nassc(correct_output, quasi_dists_dict)
                    success_rate_nassc = success_rate_quasi
                    # success_rate_quasi_std = calculate_success_rate_nassc(correct_output, quasi_dists_std_dict)
                    success_rate_tvd = calculate_success_rate_tvd(correct_output, quasi_dists_dict)
                    success_rate_tvd_new = calculate_success_rate_tvd_new(correct_output, quasi_dists_dict)
                    hellinger_distance = calculate_hellinger_distance(correct_output, quasi_dists_dict)
                    success_rate_polar = 0
                else:

                    end_index = 0
                    start_index = None

                    success_rate_quasi = 0
                    success_rate_nassc = 0
                    success_rate_tvd = 0
                    success_rate_tvd_new = 0
                    hellinger_distance = 0

                    count_dict_bin = convert_dict_int_to_binary(quasi_dists_dict, mp_total_clbits)
                    total_circuit = len(mp_data)- 1 

                    for k in range(total_circuit) :
                        mp_dict = mp_data[k]

                        mp_corr_out = mp_dict["correct_output"]
                        # mp_corr_out_count = {}
                        # if (round(sum(mp_corr_out.values())) <= 1):
                        #     for key, value in mp_corr_out.items():
                        #         mp_corr_out_count[key] = value * shots


                        mp_num_clbits = mp_dict["num_clbits"]
                        mp_circ_name = mp_dict["circuit_name"]

                        mp_corr_out_bin = convert_dict_int_to_binary(mp_corr_out, mp_num_clbits)

                        end_index = end_index - mp_num_clbits
                        
                        tmp =  sum_middle_digits_dict(count_dict_bin, end_index, start_index)
                        
                        start_index = end_index
                        print(mp_circ_name, calculate_success_rate_tvd(mp_corr_out_bin, tmp), mp_corr_out_bin )

                        success_rate_quasi = success_rate_quasi + calculate_success_rate_nassc(mp_corr_out_bin, tmp)
                        success_rate_tvd = success_rate_tvd + calculate_success_rate_tvd(mp_corr_out_bin, tmp)
                        success_rate_tvd_new = success_rate_tvd_new + calculate_success_rate_tvd_new(mp_corr_out_bin, tmp)
                        hellinger_distance = hellinger_distance + calculate_hellinger_distance(mp_corr_out_bin, tmp)
                        

                    success_rate_quasi = success_rate_quasi / total_circuit

                    success_rate_nassc = success_rate_quasi

                    success_rate_tvd = success_rate_tvd / total_circuit
                    success_rate_tvd_new = success_rate_tvd_new / total_circuit
                    hellinger_distance = hellinger_distance / total_circuit
                    success_rate_polar = 0

            # check if the metric is already there, just update
            cursor.execute('SELECT detail_id FROM metric WHERE detail_id = %s', (detail_id,))
            existing_row = cursor.fetchone()

            if existing_row:
                cursor.execute("""UPDATE metric SET total_gate = %s, total_one_qubit_gate = %s, total_two_qubit_gate = %s, circuit_depth = %s, 
                circuit_cost = %s, success_rate_tvd = %s, success_rate_nassc = %s, success_rate_quasi = %s, 
                success_rate_polar = %s, hellinger_distance = %s, success_rate_tvd_new = %s, polar_count_accept = %s, polar_count_logerror = %s,
                polar_count_undecided = %s, detection_time = %s, decoding_time = %s 
                WHERE detail_id = %s; """, 
                (total_gate, total_one_qubit_gate, total_two_qubit_gate, circuit_depth, 
                circuit_cost, success_rate_tvd, success_rate_nassc, success_rate_quasi, 
                success_rate_polar, hellinger_distance, success_rate_tvd_new, count_accept, count_logerror, 
                count_undecided, detection_time, decoding_time, detail_id))
                
            else:
                cursor.execute("""INSERT INTO metric(detail_id, total_gate, total_one_qubit_gate, total_two_qubit_gate, circuit_depth, 
                circuit_cost, success_rate_tvd, success_rate_nassc, success_rate_quasi, 
                success_rate_polar, hellinger_distance, success_rate_tvd_new, polar_count_accept, polar_count_logerror, 
                polar_count_undecided, detection_time, decoding_time)
                VALUES (%s, %s, %s, %s, %s,
                %s, %s, %s, %s, 
                %s, %s, %s, %s, %s, 
                %s, %s, %s); """, 
                (detail_id, total_gate, total_one_qubit_gate, total_two_qubit_gate, circuit_depth, 
                circuit_cost, success_rate_tvd, success_rate_nassc, success_rate_quasi, 
                success_rate_polar, hellinger_distance, success_rate_tvd_new, count_accept, count_logerror, count_undecided, detection_time, decoding_time))
                
            # update_result_header_status_by_header_id(cursor, header_id, 'done')

            conn.commit()

        database_wrapper.update_result_header_status_by_header_id(header_id, 'done')

    except Exception as e:
        print("Error in getting the metrics : ", e)

        # # Extract the last traceback entry
        # tb = traceback.extract_tb(e.__traceback__)
        # last_entry = tb[-1]
        # line_number = last_entry.lineno

        # # Print the line number
        # print(f"Exception occurred on line: {line_number}")

    
    conn.commit()
    cursor.close()
    conn.close()

# if __name__ == "__main__":
#     conn = mysql.connector.connect(**conf.mysql_config)
#     cursor = conn.cursor()

#     pending_jobs = database_wrapper.get_pending_jobs()
        
#     tmp_qiskit_token = ""
#     header_id, job_id, qiskit_token = None, None, None
#     provider, backend, service = None, None, None
    
#     print('Pending jobs: ', len(pending_jobs))
#     for result in pending_jobs:
#         header_id, job_id, qiskit_token, hw_name = result

#         if tmp_qiskit_token == "" or tmp_qiskit_token != qiskit_token:
#             # QiskitRuntimeService.save_account(channel="ibm_cloud", token=qiskit_token, instance="Qiskit Runtime-ucm", overwrite=True)
#             # service = QiskitRuntimeService(channel="ibm_cloud", token=qiskit_token, instance="Qiskit Runtime-ucm")

#             QiskitRuntimeService.save_account(channel="ibm_quantum", token=qiskit_token, overwrite=True)
#             service = QiskitRuntimeService(channel="ibm_quantum", token=qiskit_token)
        
#         if job_id == "simulator":
#             status = process_simulator(service, header_id, job_id, hw_name)
#         else:
#             job = service.job(job_id)
#             print("Checking results for: ", job_id, "with header id :", header_id)

#             if check_result_availability(job, header_id):
#                 get_result(job)


#         tmp_qiskit_token = qiskit_token

#     cursor.close()
#     conn.close()

#     executed_jobs = database_wrapper.get_executed_jobs()
#     print('Executed jobs :', len(executed_jobs))
#     for result in executed_jobs:
#         header_id, job_id = result
#         try:
#              get_metrics(header_id, job_id)
#         except Exception as e:
#              print("Error metric:", str(e))
