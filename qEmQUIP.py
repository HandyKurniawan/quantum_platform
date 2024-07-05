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
    calibration_type_enum, qiskit_compilation_enum, normalize_counts, Config,  \
    num_sort, convert_dict_binary_to_int, calculate_success_rate_tvd, sum_last_n_digits_dict
import inspect
from qiskit import QuantumCircuit, transpile
from wrappers.qiskit_wrapper import QiskitCircuit
from qiskit_ibm_runtime import QiskitRuntimeService, Session, Options
from qiskit_ibm_runtime import SamplerV2 as Sampler, EstimatorV2 as Estimator
from qiskit_ibm_runtime.options import SamplerOptions, EstimatorOptions, DynamicalDecouplingOptions, TwirlingOptions
from qiskit_aer.noise import NoiseModel
from qiskit.quantum_info import SparsePauliOp

from datetime import datetime
import mysql.connector
import time
import json
import mapomatic as mm
import mthree
import pandas as pd

from qiskit.circuit.library import XGate, YGate
from qiskit.transpiler.passes import ALAPScheduleAnalysis, ASAPScheduleAnalysis, PadDynamicalDecoupling
from qiskit.transpiler import PassManager
from scheduler import check_result_availability, get_result, process_simulator, get_metrics

conf = Config()
debug = conf.activate_debugging_time


class QEM:
    def __init__(self, runs=1, 
                 user_id = 99,
                 token=conf.qiskit_token,
                 skip_db=False
                 ):

        self.session: Session = None
        self.service: QiskitRuntimeService = None
        self.real_backend = None
        self.backend = None
        self.program: (Sampler | Estimator) = None

        self.conn = None
        self.cursor = None    

        self.circuit_name = None
        self.qasm = None 
        self.qasm_original = None 
        self.runs = runs
        
        self.header_id = None
        self.user_id = user_id
        self.token = token

        if not skip_db:
            self.open_database_connection()
            conf.send_to_backend = True
        else:
            conf.send_to_backend = False

        self.set_service(hardware_name=conf.hardware_name, token=token)
        
        if conf.initialized_triq == 1:
            self.update_hardware_configs()


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

    def set_service(self, hardware_name=conf.hardware_name, token=None):
        
        if debug: tmp_start_time  = time.perf_counter()

        if token == None: token = self.token
        QiskitRuntimeService.save_account(channel="ibm_quantum", token=token, overwrite=True)

        if hardware_name == "ibm_algiers":
            self.service = QiskitRuntimeService(channel="ibm_cloud", token=token, instance=conf.ibm_cloud_instance)
        else:
            self.service = QiskitRuntimeService(channel="ibm_quantum", token=token)
        
        self.real_backend = self.service.get_backend(hardware_name)
        
        if debug: tmp_end_time = time.perf_counter()
        if debug: print("Time for setup the services: {} seconds".format(tmp_end_time - tmp_start_time))

    def set_backend(self, program_type="sampler", backend=None, shots=conf.shots, 
                    dd_options: DynamicalDecouplingOptions = {}, twirling_options: TwirlingOptions = {}):
        
        if debug: tmp_start_time  = time.perf_counter()

        if backend == None: 
            self.backend = self.real_backend
        else:
            self.backend = backend
        
        if program_type == "sampler":
            options = SamplerOptions(
                default_shots=shots,
                dynamical_decoupling=dd_options,
                twirling= twirling_options
            )
            self.program = Sampler(mode=self.backend, options=options) 
        elif program_type == "estimator":
            options = EstimatorOptions(
                default_shots=shots,
                optimization_level=conf.optimization_level,
                resilience_level=conf.resilience_level,
                dynamical_decoupling=dd_options,
                twirling= twirling_options
            )
            self.program = Estimator(mode=self.backend,options=options)

        
        if debug: tmp_end_time = time.perf_counter()
        if debug: print("Time for setup the backends: {} seconds".format(tmp_end_time - tmp_start_time))

    def get_circuit_properties(self, qasm_source, skip_simulation=False):
        self.circuit_name = qasm_source.split("/")[-1].split(".")[0]

        qc = QiskitCircuit(qasm_source, name=self.circuit_name, skip_simulation=skip_simulation)
        self.qasm = qc.qasm
        self.qasm_original = qc.qasm_original
            
        if conf.send_to_db:
            database_wrapper.update_circuit_data(self.conn, self.cursor, qc, conf.skip_update_simulator)

        return qc


    def apply_qiskit(self, 
                     qasm = None, observable= None,
                     compilation_name = qiskit_compilation_enum.qiskit_3,
                     generate_props = False, recent_n = None, noise_level=None
                     ):
        """
        hmmm
        """
        enable_mirage = False
        enable_mapomatic = False
        calibration_type = None

        if qasm is None:
            qasm = self.qasm

        compilation_name, calibration_type, enable_mapomatic, qiskit_optimization_level = qiskit_wrapper.get_compilation_setup(compilation_name, recent_n)
        
        updated_qasm, compilation_time, initial_mapping = qiskit_wrapper.optimize_qasm(
            qasm, self.real_backend, qiskit_optimization_level,
            enable_mirage=enable_mirage, enable_mapomatic=enable_mapomatic,
            calibration_type=calibration_type, generate_props=generate_props, recent_n=recent_n)

        if conf.send_to_backend: 
            database_wrapper.insert_to_result_detail(self.conn, self.cursor, self.header_id, self.circuit_name, conf.noisy_simulator, noise_level, 
                                                     compilation_name, compilation_time, updated_qasm, observable, initial_mapping)
            
        return updated_qasm, initial_mapping

    def apply_triq(self, compilation_name, qasm=None, observable=None, layout="mapo", generate_props = False, noise_level=None):
        """
        """    
        if qasm is None:
            qasm = self.qasm


        calibration_type, hardware_name = triq_wrapper.get_compilation_config(compilation_name)

        initial_mapping = ""
        if layout == "mapo":
            # Generate Initial Mapping from Mapomatic to a File
            initial_mapping = qiskit_wrapper.get_initial_mapping_mapomatic(
                    qasm, self.real_backend, calibration_type=calibration_type, 
                    generate_props=generate_props, recent_n=0)
        elif layout == "sabre":
            initial_mapping = qiskit_wrapper.get_initial_mapping_sabre(
                    qasm, self.real_backend, calibration_type=calibration_type, 
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
            database_wrapper.insert_to_result_detail(self.conn, self.cursor, self.header_id, self.circuit_name, conf.noisy_simulator, noise_level, 
                                                     compilation_name, compilation_time, updated_qasm, observable, initial_mapping, final_mapping)

        return updated_qasm, initial_mapping
    
    def apply_mthree(self, backend, initial_mapping, counts, shots):
        mit = mthree.M3Mitigation(backend)
        mit.cals_from_system(initial_mapping, shots)

        shortened_counts = sum_last_n_digits_dict(counts, len(initial_mapping))

        m3_quasi = mit.apply_correction(shortened_counts, initial_mapping)
        probs = m3_quasi.nearest_probability_distribution()
        probs_int = convert_dict_binary_to_int(probs)

        return probs_int
    
    def apply_dd(self, circuit, backend, sequence_type = "XX", scheduling_method = "alap"):

        X = XGate()
        Y = YGate()
        
        if sequence_type == "XX":
            dd_sequence = [X, X]
        elif sequence_type == "XpXm":
            dd_sequence = [X, X]
        elif sequence_type == "XY4":
            dd_sequence = [X, Y, X, Y]

        target = backend.target

        # Set the scheduling method
        if scheduling_method == "alap":
            scheduling = ALAPScheduleAnalysis(target=target)
        elif scheduling_method == "asap":
            scheduling = ASAPScheduleAnalysis(target=target)

        dd_pm = PassManager(
        [
            scheduling,
            PadDynamicalDecoupling(target=target, dd_sequence=dd_sequence),
        ]
        )
        
        circuit_dd = dd_pm.run(circuit)

        return circuit_dd

        
    def send_qasm_to_real_backend(self, program_type, dd_options: DynamicalDecouplingOptions = {}, 
                                  twirling_options: TwirlingOptions = {}):
        if debug: tmp_start_time  = time.perf_counter()

        results_1 = database_wrapper.get_header_with_null_job(self.cursor)
        print("Total send to real backend :", len(results_1))
        for res_1 in results_1:
            header_id, qiskit_token, shots, runs = res_1

            # Set backend
            # TODO: save program_type, dd_options and twirling_options in the database
            self.set_backend(program_type=program_type, shots=shots, dd_options=dd_options, twirling_options=twirling_options)

            results = database_wrapper.get_detail_with_header_id(self.cursor, header_id)
            
            success = False
            list_circuits = []

            for res in results:
                detail_id, updated_qasm, compilation_name = res

                qc = QiskitCircuit(updated_qasm, skip_simulation=True)

                circuit = qc.transpile_to_target_backend(self.real_backend)

                for i in range(runs):
                    list_circuits.append(circuit)
                
            print("Total no of circuits :",len(list_circuits))
            while not success:
                try:

                    print("Sending to {} with batch id: {} ... ".format(conf.hardware_name, header_id))
                    job_id = None

                    if isinstance(self.program, Sampler):

                        job = self.program.run(list_circuits)
                        job_id = job.job_id()

                    elif isinstance(self.program, Estimator):
                        pass

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

    def compile(self, qasm, compilation_name, observable=None, generate_props=False, noise_level=None):

        updated_qasm = ""
        initial_mapping = ""
        if "qiskit" in compilation_name or "mapomatic" in compilation_name:
            updated_qasm, initial_mapping = self.apply_qiskit(qasm=qasm, observable=observable, compilation_name=compilation_name, generate_props=generate_props, noise_level=noise_level)
        elif "triq" in compilation_name:
            tmp = compilation_name.split("_")
            layout = tmp[2]
            compilation = tmp[0] + "_" + tmp[1]
            updated_qasm, initial_mapping = self.apply_triq(qasm=qasm, observable=observable, compilation_name=compilation, layout=layout, noise_level=noise_level)

        return updated_qasm, initial_mapping

#region Run
    def run_simulator(self, program_type, qasm_files, compilations, noise_levels, shots, 
                      observables = None,
                      mitigation = None, send_to_db = False,
                      apply_dd = False, sequence_type = "XX", scheduling_method = "alap"):
        """
        
        """
        skip_simulation = False
        # validation
        if program_type == "estimator":
            skip_simulation = True
            if len(qasm_files) != len(observables):
                raise ValueError("The number of observables should be the same as the number of circuits when using the program type 'estimator'.")

        # initialize variables
        res_circuit_name, res_compilations, res_noise_levels, res_success_rate, res_success_rate_m3 = ([] for _ in range(5))

        # this function always run on a simulator
        conf.noisy_simulator = True

        if send_to_db:
            conf.send_to_db = True
            # init header
            self.header_id = database_wrapper.init_result_header(self.cursor, self.user_id, 
                                                                 token=self.token, program_type=program_type)

        for idx, qasm in enumerate(qasm_files):
            qc = self.get_circuit_properties(qasm_source=qasm, skip_simulation=skip_simulation)

            for comp in compilations:

                for noise_level in noise_levels:
                    noise_model, noisy_simulator, coupling_map = qiskit_wrapper.get_noisy_simulator(self.real_backend, noise_level)

                    # set the backend and the program
                    self.set_backend(program_type=program_type, backend=noisy_simulator, shots=shots)

                    observable = None
                    if program_type == "estimator":
                        observable = observables[idx]

                    updated_qasm, initial_mapping = self.compile(qasm=qc.qasm_original, observable=observable, compilation_name=comp, generate_props=False, noise_level=noise_level)
                    compiled_qc = QiskitCircuit(updated_qasm, skip_simulation=skip_simulation)
                    circuit = compiled_qc.transpile_to_target_backend(self.real_backend)

                    if apply_dd:
                        circuit = self.apply_dd(circuit, noisy_simulator, sequence_type=sequence_type, scheduling_method=scheduling_method)

                    if isinstance(self.program, Sampler):

                        job = self.program.run(pubs=[circuit])
                        result = job.result()[0]  
                        output = result.data.c.get_counts()
                        output_normalize = normalize_counts(output, shots=shots)

                        tvd = calculate_success_rate_tvd(qc.correct_output,output_normalize)

                    elif isinstance(self.program, Estimator):

                        p_obs = []
                        for obs in observable:
                            print(obs)
                            tmp = SparsePauliOp(obs)
                            p_obs.append(tmp)

                        print(p_obs)
                        pub = (circuit, p_obs)
                        job = self.program.run(pubs=[pub])

                        tvd = job.result()[0].data.evs

                    

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
    
    def send_to_real_backend(self, program_type, qasm_files, compilations, hardware_name = conf.hardware_name,
                             dd_options: DynamicalDecouplingOptions = {"enable":False}, twirling_options: TwirlingOptions = {}):
        # Update the
        conf.send_to_db = True
        conf.hardware_name = hardware_name

        # init header
        self.header_id = database_wrapper.init_result_header(self.cursor, self.user_id, token=self.token, 
                                                             dd_options=dd_options)

        for qasm in qasm_files:
            qc = self.get_circuit_properties(qasm_source=qasm)
            
            for comp in compilations:
                print("Compiling circuit: {} for compilation: {}".format(self.circuit_name, comp))
                self.compile(qasm=qc.qasm_original, compilation_name=comp)

        if conf.noisy_simulator:
            # Send to local simulator, just send to the database, execution is on scheduler.py
            self.run_on_noisy_simulator_local()
        else:
            # Send to backend
            self.send_qasm_to_real_backend(program_type, dd_options=dd_options, twirling_options=twirling_options)
            
                
#endregion

    def get_qiskit_result(self):
        pending_jobs = database_wrapper.get_pending_jobs()
            
        tmp_qiskit_token = ""
        header_id, job_id, qiskit_token = None, None, None
        service = None
        
        print('Pending jobs: ', len(pending_jobs))
        for result in pending_jobs:
            header_id, job_id, qiskit_token, hw_name = result

            if tmp_qiskit_token == "" or tmp_qiskit_token != qiskit_token:
                QiskitRuntimeService.save_account(channel="ibm_quantum", token=qiskit_token, overwrite=True)
                service = QiskitRuntimeService(channel="ibm_quantum", token=qiskit_token)
            
            if job_id == "simulator":
                process_simulator(service, header_id, job_id, hw_name)
            else:
                job = service.job(job_id)
                print("Checking results for: ", job_id, "with header id :", header_id)

                if check_result_availability(job, header_id):
                    get_result(job)

            tmp_qiskit_token = qiskit_token

        executed_jobs = database_wrapper.get_executed_jobs()
        print('Executed jobs :', len(executed_jobs))
        for result in executed_jobs:
            header_id, job_id = result
            try:
                get_metrics(header_id, job_id)
            except Exception as e:
                print("Error metric:", str(e))
