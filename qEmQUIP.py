"""
file name: qEmQUIP.py
author: Handy
date: 11 June 2024

A platform for experimenting with and applying various quantum compilation techniques across multiple quantum computing backends.

Functions:
...

Example:
"""
import wrappers.triq_wrapper as triq_wrapper
import wrappers.qiskit_wrapper as qiskit_wrapper
import wrappers.database_wrapper as database_wrapper
import sys, glob, os
from commons import convert_to_json, triq_optimization, qiskit_optimization, \
    calibration_type_enum, qiskit_compilation_enum, normalize_counts, Config, num_sort, convert_dict_binary_to_int, calculate_success_rate_tvd
import inspect
from qiskit import QuantumCircuit, transpile
from wrappers.qiskit_wrapper import QiskitCircuit
from qiskit_ibm_runtime import QiskitRuntimeService, Session, Sampler, Estimator, Options
from qiskit_aer.noise import NoiseModel

from datetime import datetime
import mysql.connector
import time
import json
import mapomatic as mm
import mthree
import pandas as pd

conf = Config()
debug = conf.activate_debugging_time


class QEM:
    def __init__(self, runs=2, 
                 fixed_initial_layout = False,  
                 user_id = 99,
                 token=conf.qiskit_token):

        self.session = None
        self.service = None
        self.backend = None
        self.sampler = None

        self.fixed_initial_layout = fixed_initial_layout
        self.initial_layout_qiskit = None
        self.initial_layout_triq = None 

        self.conn = None
        self.cursor = None    

        self.circuit_name = None
        self.qasm = None 
        self.qasm_original = None 
        self.runs = runs
        
        self.header_id = None
        self.user_id = user_id
        self.token = token

        self.open_database_connection()
        self.set_backend(token=token)
        
        if conf.initialized_triq == 1:
            self.update_hardware_configs()

        # if fixed_initial_layout:
        #     self.set_initial_layout()

    def open_database_connection(self):
        self.conn = mysql.connector.connect(**conf.mysql_config)
        self.cursor = self.conn.cursor()

    def close_database_connection(self):
        self.conn.commit()
        self.cursor.close()
        self.conn.close()

    def update_hardware_configs(self): 
        if debug: tmp_start_time  = time.perf_counter()
        triq_wrapper.generate_recent_average_calibration_data(self, 15, True)
        triq_wrapper.generate_realtime_calibration_data(self)
        triq_wrapper.generate_average_calibration_data(self)
        triq_wrapper.generate_mix_calibration_data(self)
        if debug: tmp_end_time = time.perf_counter()
        if debug: print("Time for update hardware configs: {} seconds".format(tmp_end_time - tmp_start_time))

    def set_backend(self, token=conf.qiskit_token, shots=conf.shots):
        if debug: tmp_start_time  = time.perf_counter()
        QiskitRuntimeService.save_account(channel="ibm_quantum", token=token, overwrite=True)

        if conf.hardware_name == "ibm_algiers":
            self.service = QiskitRuntimeService(channel="ibm_cloud", token=token, instance=conf.ibm_cloud_instance)
        else:
            self.service = QiskitRuntimeService(channel="ibm_quantum", token=token)
        
        self.backend = self.service.get_backend(conf.hardware_name)
        coupling_map = self.backend.configuration().coupling_map
        noise_model = NoiseModel.from_backend(self.backend)
        basis_gates = self.backend.configuration().basis_gates
        
        options = Options()
        options.execution.shots = shots
        options.optimization_level = conf.optimization_level
        options.resilience_level = conf.resilience_level
        
        self.sampler = Sampler(self.backend, options=options) 

        if debug: tmp_end_time = time.perf_counter()
        if debug: print("Time for setup the backends: {} seconds".format(tmp_end_time - tmp_start_time))

    def get_circuit_properties(self, qasm_source):
        circuit_name = qasm_source.split("/")[-1].split(".")[0]

        qc = QiskitCircuit(qasm_source, name=circuit_name)
            
        if conf.send_to_db:
            database_wrapper.update_circuit_data(self.conn, self.cursor, qc, conf.skip_update_simulator)

        return qc

    def set_initial_layout(self):
        initial_layout_dict = triq_wrapper.get_mapping(self.qasm, 
                                                       conf.hardware_name + "_" + self.calibration_type.value, 
                                                       "2")

        self.initial_layout_qiskit = []
        self.initial_layout_triq = []
        # for virtual, physical in initial_layout_dict.items():
        #     self.initial_layout.append(physical)

        for i in range(len(initial_layout_dict)):
            self.initial_layout_qiskit.append(initial_layout_dict[str(i)])
            self.initial_layout_triq.append(initial_layout_dict[str(i)])

        for i in range(self.backend.n_qubits):
            if i not in self.initial_layout_triq:
                self.initial_layout_triq.append(i)

        # print("Initial Layout qiskit: ", self.initial_layout_qiskit )
        # print("Initial Layout triq: ", self.initial_layout_triq )


    def apply_qiskit(self, 
                     qasm = None,
                     compilation_name = qiskit_compilation_enum.qiskit_3,
                     generate_props = False, recent_n = None, noise_level=None
                     ):
        """
        hmmm
        """
        qiskit_optimization_level = 3
        enable_noise_adaptive = False
        enable_mirage = False
        enable_mapomatic = False
        calibration_type = None

        if qasm is None:
            qasm = self.qasm

        compilation_name, calibration_type, enable_noise_adaptive, enable_mapomatic = qiskit_wrapper.get_compilation_setup(compilation_name, recent_n)
        
        updated_qasm, compilation_time, initial_mapping = qiskit_wrapper.optimize_qasm(
            qasm, self.backend, qiskit_optimization_level,
            enable_noise_adaptive=enable_noise_adaptive, enable_mirage=enable_mirage, enable_mapomatic=enable_mapomatic,
            calibration_type=calibration_type, generate_props=generate_props, recent_n=recent_n)

        if conf.send_to_backend: 
            database_wrapper.insert_to_result_detail(self.conn, self.cursor, self.header_id, self.circuit_name, noise_level, 
                                                     compilation_name, compilation_time, updated_qasm, initial_mapping)
            
        return updated_qasm, initial_mapping

    def apply_triq(self, compilation_name, qasm=None, layout="mapo", generate_props = False, noise_level=None):
        """
        """    
        if qasm is None:
            qasm = self.qasm


        calibration_type, hardware_name = triq_wrapper.get_compilation_config(compilation_name)

        initial_mapping = ""
        if layout == "mapo":
            # Generate Initial Mapping from Mapomatic to a File
            initial_mapping = qiskit_wrapper.get_initial_mapping_mapomatic(
                    qasm, self.backend, calibration_type=calibration_type, 
                    generate_props=generate_props, recent_n=0)
        elif layout == "na":
            initial_mapping = qiskit_wrapper.get_initial_mapping_na(
                    qasm, self.backend, calibration_type=calibration_type, 
                    generate_props=generate_props, recent_n=0)
        elif layout == "sabre":
            initial_mapping = qiskit_wrapper.get_initial_mapping_sabre(
                    qasm, self.backend, calibration_type=calibration_type, 
                    generate_props=generate_props, recent_n=0)
        
        triq_wrapper.generate_initial_mapping_file(initial_mapping)

           
        # print("TriQ hardware name :", hardware_name)
        tmp_start_time  = time.perf_counter()
        updated_qasm = triq_wrapper.run(qasm, hardware_name, 0, measurement_type=conf.triq_measurement_type)
        tmp_end_time = time.perf_counter()

        final_mapping = triq_wrapper.get_mapping(qasm, hardware_name, 0)

        compilation_time = tmp_end_time - tmp_start_time
        
        compilation_name = layout + "_" + compilation_name
        if conf.send_to_backend: 
            database_wrapper.insert_to_result_detail(self.conn, self.cursor, self.header_id, self.circuit_name, noise_level, 
                                                     compilation_name, compilation_time, updated_qasm, initial_mapping, final_mapping)

        return updated_qasm, initial_mapping
    
    def apply_mthree(self, backend, initial_mapping, counts, shots):
        mit = mthree.M3Mitigation(backend)
        mit.cals_from_system(initial_mapping, shots)
        m3_quasi = mit.apply_correction(counts, initial_mapping)
        probs = m3_quasi.nearest_probability_distribution()
        probs_int = convert_dict_binary_to_int(probs)

        return probs_int

        
    def send_qasm_to_real_backend(self):
        if debug: tmp_start_time  = time.perf_counter()

        results_1 = database_wrapper.get_header_with_null_job(self.cursor)
        print("Total send to real backend :", len(results_1))
        for res_1 in results_1:
            header_id, qiskit_token, shots, runs = res_1

            self.set_backend(qiskit_token, shots=shots)

            results = database_wrapper.get_detail_with_header_id(self.cursor, header_id)
            
            success = False
            list_circuits = []

            for res in results:
                detail_id, updated_qasm, compilation_name = res

                qc = QiskitCircuit(updated_qasm, skip_simulation=True)

                circuit = qc.transpile_to_target_backend(self.backend)

                for i in range(runs):
                    list_circuits.append(circuit)
                
            print("Total no of circuits :",len(list_circuits))
            while not success:
                try:

                    print("Sending to {} with batch id: {} ... ".format(conf.hardware_name, header_id))
                    job = self.sampler.run(list_circuits, skip_transpilation=True)
                    job_id = job.job_id()

                    success = True

                    # update to result detail
                    print("Sent!")
                    self.cursor.execute('UPDATE result_header SET job_id = %s, status = "pending", updated_datetime = NOW() WHERE id = %s', (job_id, header_id))

                    self.conn.commit()

                except Exception as e:
                    print(f"An error occurred: {str(e)}. Will try again in 30 seconds...")

                    for i in range(30, 0, -1):
                        time.sleep(1)
                        print(i)

        if debug: tmp_end_time = time.perf_counter()
        if debug: print("Time for sending to real backend: {} seconds".format(tmp_end_time - tmp_start_time))

    def run_on_noisy_simulator_local(self):
        if debug: tmp_start_time  = time.perf_counter()
        
        results_1 = database_wrapper.get_header_with_null_job(self.cursor)
        print("Total send to local simulator :", len(results_1))
        for res_1 in results_1:
            header_id, qiskit_token, shots, runs = res_1
            
            success = False

            while not success:
                try:

                    print("Running to {} with batch id: {} ... ".format("Local Simulator", header_id))

                    success = True

                    # update to result detail
                    print("Sent!")
                    self.cursor.execute('UPDATE result_header SET job_id = %s, status = "pending", updated_datetime = NOW() WHERE id = %s', ("simulator", header_id))

                    self.conn.commit()

                except Exception as e:
                    print(f"An error occurred: {str(e)}. Will try again in 30 seconds...")

                    for i in range(30, 0, -1):
                        time.sleep(1)
                        print(i)

        if debug: tmp_end_time = time.perf_counter()
        if debug: print("Time for sending to local simulator: {} seconds".format(tmp_end_time - tmp_start_time)) 

    def get_qasm_files_from_path(self, file_path = conf.base_folder):
        return glob.glob(os.path.expanduser(os.path.join(file_path, "*.qasm")))

    def compile(self, qasm, compilation_name, generate_props=False, noise_level=None):

        updated_qasm = ""
        initial_mapping = ""
        if "qiskit" in compilation_name or "mapomatic" in compilation_name:
            updated_qasm, initial_mapping = self.apply_qiskit(qasm=qasm, compilation_name=compilation_name, generate_props=generate_props, noise_level=noise_level)
        elif "triq" in compilation_name:
            tmp = compilation_name.split("_")
            layout = tmp[2]
            compilation = tmp[0] + "_" + tmp[1]
            updated_qasm, initial_mapping = self.apply_triq(qasm=qasm, compilation_name=compilation, layout=layout, noise_level=noise_level)

        return updated_qasm, initial_mapping

#region Run
    def run_simulator(self, qasm_files, compilations, noise_levels, shots, mitigation = None, send_to_db = False):
        """
        
        """
        if send_to_db:
            conf.send_to_db = True
            # init header
            self.header_id = database_wrapper.init_result_header(self.cursor, self.user_id, token=self.token)

        res_circuit_name, res_compilations, res_noise_levels, res_success_rate, res_success_rate_m3 = ([] for _ in range(5))

        for noise_level in noise_levels:
            noise_model, noisy_simulator, coupling_map = qiskit_wrapper.get_noisy_simulator(self.backend, noise_level)

            for qasm in qasm_files:
                qc = self.get_circuit_properties(qasm_source=qasm)
                self.circuit_name = qasm.split("/")[-1].split(".")[0]
                self.qasm = qc.qasm
                self.qasm_original = qc.qasm_original

                for comp in compilations:
                
                    updated_qasm, initial_mapping = self.compile(qasm=qc.qasm_original, compilation_name=comp, noise_level=noise_level)
                    compiled_qc = QiskitCircuit(updated_qasm)
                    circuit = compiled_qc.transpile_to_target_backend(self.backend, False)
                    
                    job = noisy_simulator.run(circuit, shots=shots)
                    result = job.result()  
                    output = result.get_counts()
                    output_normalize = normalize_counts(output, shots=shots)

                    tvd = calculate_success_rate_tvd(qc.correct_output,output_normalize)

                    res_circuit_name.append(self.circuit_name)
                    res_compilations.append(comp)
                    res_noise_levels.append(noise_level)
                    res_success_rate.append(tvd)

                    if mitigation == "m3":
                        probs_m3 = self.apply_mthree(noisy_simulator, initial_mapping, output, shots)
                        tvd_m3 = calculate_success_rate_tvd(qc.correct_output, probs_m3)
                        res_success_rate_m3.append(tvd_m3)

        df = pd.DataFrame({
            'circuit_name': res_circuit_name,
            'compilation': res_compilations,
            'noise_level': res_noise_levels,
            'success_rate': res_success_rate,
        })

        if send_to_db:  
            # Send to local simulator
            
            self.run_on_noisy_simulator_local()
                  

        return df
    
    def send_to_real_backend(self, qasm_files, compilations, hardware_name = conf.hardware_name):
        # Update the
        conf.send_to_db = True
        conf.hardware_name = hardware_name

        # init header
        self.header_id = database_wrapper.init_result_header(self.cursor, self.user_id, token=self.token)

        for qasm in qasm_files:
            qc = self.get_circuit_properties(qasm_source=qasm)
            self.circuit_name = qasm.split("/")[-1].split(".")[0]
            self.qasm = qc.qasm
            self.qasm_original = qc.qasm_original

            for comp in compilations:
                print("Compiling circuit: {} for compilation: {}".format(self.circuit_name, comp))
                self.compile(qasm=qc.qasm_original, compilation_name=comp)

        if conf.noisy_simulator:
            # Send to local simulator
            self.run_on_noisy_simulator_local()
        else:
            # Send to backend
            self.send_qasm_to_real_backend()
            
                
#endregion
