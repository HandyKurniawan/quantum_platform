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
from wrappers.multiprogramming_wrapper import (
    avoid_simultaneous_cnot, add_zz_on_simultaneous_cnot, 
    build_idle_coupling_map, multiprogram_compilation_qiskit, merge_circuits,
    get_LF_presets_cm
)

from wrappers.prune_wrapper import (
    get_qubits_by_thresholds, get_qubits_by_lf
)

import sys, glob, os
from commons import (
    convert_to_json, triq_optimization, qiskit_optimization, 
    calibration_type_enum, qiskit_compilation_enum, normalize_counts, Config,  
    num_sort, convert_dict_binary_to_int, calculate_success_rate_tvd, sum_last_n_digits_dict,
    used_qubits
)
import inspect
from qiskit import QuantumCircuit, transpile
from qiskit.transpiler import CouplingMap
from wrappers.qiskit_wrapper import QiskitCircuit
from qiskit_ibm_runtime import QiskitRuntimeService, Session, Options
from qiskit_ibm_runtime import SamplerV2 as Sampler, EstimatorV2 as Estimator, IBMBackend
from qiskit_aer.primitives import SamplerV2 as SamplerAer
from qiskit_ibm_runtime.options import SamplerOptions, EstimatorOptions, DynamicalDecouplingOptions, TwirlingOptions
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel
from qiskit.quantum_info import SparsePauliOp
from qiskit.qasm2 import dumps

from datetime import datetime
import mysql.connector
import time
import numpy as np
# import json
# import mapomatic as mm
# import mthree
# import pandas as pd

from qiskit.circuit.library import XGate, YGate, ZGate, RZGate
from qiskit.transpiler.passes import ALAPScheduleAnalysis, ASAPScheduleAnalysis, PadDynamicalDecoupling
from qiskit.transpiler import PassManager
from scheduler import check_result_availability, get_result, process_simulator, get_metrics

from typing import (
    Any,
    BinaryIO,
    Callable,
    # Dict,
    Generator,
    Iterator,
    # List,
    Mapping,
    NoReturn,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
    cast,
)

conf = Config()
debug = conf.activate_debugging_time


class QEM:
    def __init__(self, 
                 runs: int = 1, 
                 user_id: int = 1,
                 token: str = conf.qiskit_token,
                 skip_db: bool = False,
                 hw_name: str = conf.hardware_name
                 ):

        self.session: Optional[Session] = None
        self.service: Optional[QiskitRuntimeService] = None
        self.real_backend: IBMBackend = None
        self.backend: Union[IBMBackend, AerSimulator] = None
        self.program: Union[Sampler, Estimator] = None
        self.program_normal: Union[Sampler, Estimator] = None

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

        self.set_service(hardware_name=hw_name, token=token)
        
        if conf.initialized_triq == 1:
            self.update_hardware_configs(hw_name)


    def open_database_connection(self) -> None:
        self.conn = mysql.connector.connect(**conf.mysql_config)
        self.cursor = self.conn.cursor()

    def close_database_connection(self):
        self.conn.commit()
        self.cursor.close()
        self.conn.close()

    def update_hardware_configs(self, hw_name = conf.hardware_name): 
        if debug: tmp_start_time  = time.perf_counter()
        # triq_wrapper.generate_recent_average_calibration_data(self, 15, True, hw_name=hw_name)
        triq_wrapper.generate_realtime_calibration_data(self, hw_name=hw_name)
        triq_wrapper.generate_average_calibration_data(self, hw_name=hw_name)
        # triq_wrapper.generate_mix_calibration_data(self, hw_name=hw_name)
        if debug: tmp_end_time = time.perf_counter()
        if debug: print("Time for update hardware configs: {} seconds".format(tmp_end_time - tmp_start_time))

    def set_service(self, hardware_name=conf.hardware_name, token=None):
        print("Connecting to quantum service...")
        if debug: tmp_start_time  = time.perf_counter()

        if token == None: token = self.token
        print("Saving IBM Account...")
        QiskitRuntimeService.save_account(channel="ibm_quantum", token=token, overwrite=True)

        if conf.use_ibm_cloud:
            print("Using IBM Cloud...")
            token = "tyF4ya7NOGlq9Ls_JM5JJ0vG0IJmdu_Ea2rc-xTauvJ_"
            self.token = "tyF4ya7NOGlq9Ls_JM5JJ0vG0IJmdu_Ea2rc-xTauvJ_"
            self.service = QiskitRuntimeService(channel="ibm_cloud", token=token, instance=conf.ibm_cloud_instance)
        else:
            self.service = QiskitRuntimeService(channel="ibm_quantum", token=token)
        
        # self.service = QiskitRuntimeService(channel="ibm_cloud", token=token, instance=conf.ibm_cloud_instance)

        print(f"Retrieving the real backend information of {hardware_name}...")
        self.real_backend = self.service.backend(hardware_name)
        
        if debug: tmp_end_time = time.perf_counter()
        if debug: print("Time for setup the services: {} seconds".format(tmp_end_time - tmp_start_time))

    def set_backend(self, 
                    program_type:str = "sampler", 
                    backend: IBMBackend | AerSimulator | None = None, 
                    shots:int = conf.shots, 
                    dd_options: DynamicalDecouplingOptions = {}, 
                    twirling_options: TwirlingOptions = {}) -> None:
        
        if debug: tmp_start_time  = time.perf_counter()

        if backend == None: 
            self.backend = self.real_backend
        else:
            self.backend = backend
        
        if program_type == "sampler":
            if isinstance(self.backend, IBMBackend):
                # TODO: check the dynamical_decoupling options
                options = SamplerOptions(
                    default_shots=shots,
                    # dynamical_decoupling=dd_options,
                    # twirling= twirling_options
                )

                self.program = Sampler(mode=self.backend, options=options) 

                options_normal = SamplerOptions(
                    default_shots=shots,
                )
                self.program_normal = Sampler(mode=self.backend, options=options_normal) 
            elif isinstance(self.backend, AerSimulator):
                self.program = SamplerAer.from_backend(self.backend, default_shots=shots)
                
        elif program_type == "estimator":
            options = EstimatorOptions(
                default_shots=shots,
                optimization_level=conf.optimization_level,
                resilience_level=conf.resilience_level,
                # dynamical_decoupling=dd_options,
                # twirling= twirling_options
            )
            self.program = Estimator(mode=self.backend,options=options)

        
        if debug: tmp_end_time = time.perf_counter()
        if debug: print("Time for setup the backends: {} seconds".format(tmp_end_time - tmp_start_time))

    def get_circuit_properties(self, 
                               qasm_source: str, 
                               skip_simulation: bool = conf.skip_update_simulator
        )->QiskitCircuit:
        if "OPENQASM" in qasm_source:
            self.circuit_name = "Circuit_" + datetime.now().strftime("%Y%m%d%H%M%S")
        else:
            self.circuit_name = qasm_source.split("/")[-1].split(".")[0]

        qc = QiskitCircuit(qasm_source, name=self.circuit_name, skip_simulation=skip_simulation)
        self.qasm = qc.qasm
        self.qasm_original = qc.qasm_original
            
        if conf.send_to_db:
            database_wrapper.update_circuit_data(self.conn, self.cursor, qc, skip_simulation)

        return qc


    def apply_qiskit(self, 
                     qasm: str = None, 
                     observable = None,
                     compilation_name: str = qiskit_compilation_enum.qiskit_3,
                     generate_props: bool = False, 
                     recent_n: int = None, 
                     noise_level: float = None,
                     cm: CouplingMap = None,
                     mp_execution_type: str = None,
                     prune_options: dict[str,bool|tuple[int|float]|int|str] = {"enable":False}
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
            calibration_type=calibration_type, generate_props=generate_props, recent_n=recent_n, cm=cm)

        if conf.send_to_backend: 
            if mp_execution_type != "final":
                database_wrapper.insert_to_result_detail(self.conn, self.cursor, self.header_id, self.circuit_name, 
                                                         conf.noisy_simulator, noise_level, compilation_name, compilation_time, 
                                                         updated_qasm, observable, initial_mapping, prune_options=prune_options)
            
        return updated_qasm, initial_mapping

    def apply_triq(self, 
                   compilation_name:str, 
                   qasm:str=None, 
                   observable=None, 
                   layout:str="sabre", 
                   generate_props:bool = False, 
                   noise_level=None,
                   cm: CouplingMap = None,
                   mp_execution_type: str = None,
                   prune_options: dict[str,bool|tuple[int|float]|int|str] = {"enable":False}):
        """
        """    
        if qasm is None:
            qasm = self.qasm

        
        
        calibration_type, hardware_name = triq_wrapper.get_compilation_config(compilation_name, hw_name=conf.hardware_name)

        tmp_start_time  = time.perf_counter()
        initial_mapping = ""
        if layout == "mapo":
            # Generate Initial Mapping from Mapomatic to a File
            initial_mapping = qiskit_wrapper.get_initial_mapping_mapomatic(
                    qasm, self.real_backend, calibration_type=calibration_type, 
                    generate_props=generate_props, recent_n=0)
        elif layout == "sabre":

            initial_mapping = qiskit_wrapper.get_initial_mapping_sabre(
                    qasm, self.real_backend, calibration_type=calibration_type, 
                    generate_props=generate_props, recent_n=0, cm=cm)
        
        triq_wrapper.generate_initial_mapping_file(initial_mapping)

           
        # print("TriQ hardware name :", hardware_name)
        updated_qasm = triq_wrapper.run(qasm, hardware_name, 0, measurement_type=conf.triq_measurement_type)
        tmp_end_time = time.perf_counter()

        final_mapping = triq_wrapper.get_mapping(qasm, hardware_name, 0)

        compilation_time = tmp_end_time - tmp_start_time
        
        compilation_name = layout + "_" + compilation_name
        if conf.send_to_backend: 
            if mp_execution_type != "final":
                database_wrapper.insert_to_result_detail(self.conn, self.cursor, self.header_id, self.circuit_name, 
                                                     conf.noisy_simulator, noise_level, compilation_name, 
                                                     compilation_time, updated_qasm, observable, initial_mapping, 
                                                     final_mapping, prune_options=prune_options)

        return updated_qasm, initial_mapping
    
    # def apply_mthree(self, backend, initial_mapping, counts, shots):
    #     mit = mthree.M3Mitigation(backend)
    #     mit.cals_from_system(initial_mapping, shots)

    #     shortened_counts = sum_last_n_digits_dict(counts, len(initial_mapping))

    #     m3_quasi = mit.apply_correction(shortened_counts, initial_mapping)
    #     probs = m3_quasi.nearest_probability_distribution()
    #     probs_int = convert_dict_binary_to_int(probs)

    #     return probs_int
    
    def apply_dd(self, 
                 circuit: QuantumCircuit, 
                 backend: IBMBackend, 
                 sequence_type: str = "XX", 
                 scheduling_method: str = "alap"):

        X = XGate()
        Y = YGate()
        Z = ZGate()
        RZ = RZGate(np.pi)
        
        if sequence_type == "XX":
            dd_sequence = [X, X]
        elif sequence_type == "XpXm":
            dd_sequence = [X, X]
        elif sequence_type == "XY4":
            dd_sequence = [X, X, RZ, X, RZ, X]

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

        
    def send_qasm_to_real_backend(self, 
                                  program_type:str, 
                                  dd_options: DynamicalDecouplingOptions = {}, 
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

                # 20250320 - Handy, remarked to avoid confusion and reduce complexity because of transpiling from basis 
                # if compilation_name not in ("qiskit_3", "qiskit_0") and "nc" not in compilation_name:
                #     circuit = qc.transpile_to_target_backend(self.real_backend)
                # else:
                #     circuit = qc.circuit_original
                circuit = qc.circuit_original

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

                        # # run the same circuit without any options
                        # self.program_normal.run(list_circuits)

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

    def get_qasm_files_from_path(self, file_path: str = conf.base_folder):
        print(file_path)
        return glob.glob(os.path.expanduser(os.path.join(file_path, "*.qasm")))

    def _get_prune_node_list(self, prune_options: dict[str,bool|tuple[int|float]|int|str] = {"enable":False}
                             )-> list[int]:
        nodes_list = []
        if "cal" in prune_options["type"]:
            cal_type = prune_options["type"].split("-")[1]

            threshold_CX = prune_options["params"][0]
            threshold_RO = prune_options["params"][1]
            nodes_list = get_qubits_by_thresholds(self.backend.name,
                                                    threshold_CX,
                                                    threshold_RO,
                                                    cal_type,
                                                    conf.mysql_calibration_config)
        elif prune_options["type"]=="lf":
            lf_num_qubits = prune_options["params"]
            nodes_list = get_qubits_by_lf(self.backend, lf_num_qubits, conf.mysql_calibration_config)

        return nodes_list

    def compile(self, 
                qasm:str, 
                compilation_name:str, 
                observable=None, 
                generate_props:bool=False, 
                noise_level:float=None,
                cm:CouplingMap=None,
                mp_execution_type: str = None,
                prune_options: dict[str,bool|tuple[int|float]|int|str] = {"enable":False}
                )-> tuple[str, list]:

        updated_qasm = ""
        initial_mapping = ""

        # this means that it is for the normal computation with the prune options on
        if cm == None and mp_execution_type == None and prune_options["enable"]:
            nodes_list = self._get_prune_node_list(prune_options)
            cm = build_idle_coupling_map(self.backend.coupling_map, nodes_list)


        if "nc" in compilation_name:
            updated_qasm = self.qasm_original
            if conf.send_to_backend: 
                database_wrapper.insert_to_result_detail(self.conn, self.cursor, self.header_id, self.circuit_name, conf.noisy_simulator, noise_level, 
                                                        compilation_name, 0, updated_qasm, observable, initial_mapping) 
        elif "qiskit" in compilation_name or "mapomatic" in compilation_name:
            updated_qasm, initial_mapping = self.apply_qiskit(qasm=qasm, observable=observable, 
                                                              compilation_name=compilation_name, 
                                                              generate_props=generate_props, 
                                                              noise_level=noise_level,
                                                              cm=cm,
                                                              mp_execution_type = mp_execution_type,
                                                              prune_options=prune_options)
        elif "triq" in compilation_name:
            tmp = compilation_name.split("_")
            layout = tmp[2]
            compilation = tmp[0] + "_" + tmp[1]
            updated_qasm, initial_mapping = self.apply_triq(qasm=qasm, 
                                                            observable=observable, 
                                                            compilation_name=compilation, 
                                                            layout=layout, 
                                                            noise_level=noise_level,
                                                            cm=cm,
                                                            mp_execution_type = mp_execution_type,
                                                            prune_options=prune_options)

        return updated_qasm, initial_mapping
    
    def get_custom_backend(self, calibration_type, hw_name, 
                         recent_n = None, start_date = None, end_date = None, 
                         generate_props = False):
        
        backend = self.service.backend(hw_name)

        custom_backend = qiskit_wrapper.get_fake_backend(calibration_type, backend, recent_n = None,
                                                         start_date=start_date, end_date=end_date,
                                                         generate_props=generate_props)

        return custom_backend

    def compile_multiprogramming(self, 
                                 qasm_files:list[str], 
                                 compilations: list[str], 
                                 exclude_qubits: list[int]= [],
                                 mp_execution_type: str = "final",
                                 prune_options: dict[str,bool|tuple[int|float]|int|str] = {"enable":False},
                                 run_simulation: bool = False,
                                 noise_levels: list[float] = [None]
                                 ):
        """
        mp_execution_type: determine how the multiprogramming create a circuit
        - all = run the circuits individually + the final merged circuit
        - partition = run the circuits individually
        - final = run only the final merged circuit
        """

        # to prevent running on the real backedn with noise levels
        if run_simulation == False:
            noise_levels = [None]

        for noise_level in noise_levels:
            compiled_circuits: dict[str, list[dict[QuantumCircuit, list[int]]]] = {}

            for compilation_name in compilations:

                tmp_start_time  = time.perf_counter()

                compiled_circuits[compilation_name] = []

                cm = self.backend.coupling_map
                prevously_used_qubits = []
                used_qubit = []

                # if there is a list in exclude_qubits
                if len(exclude_qubits) > 0:
                    for q in exclude_qubits:
                        prevously_used_qubits.append(q)
                        used_qubit.append(q)
                    
                    cm = build_idle_coupling_map(cm, used_qubit)
                
                total_qubits = 0
                for qasm in qasm_files:
                    qc = self.get_circuit_properties(qasm_source=qasm, skip_simulation=True)
                    
                    total_qubits = total_qubits + len(used_qubits(qc.circuit))
                
                total_largest_connected_qubits = len(cm.largest_connected_component())
                print(f"Total qubits: {total_qubits}, CM-Long: {total_largest_connected_qubits}" )
                # max_reps = np.floor(backend.num_qubits / len(qc.qubits))

                if total_qubits > total_largest_connected_qubits:
                    raise ValueError(f'Total number of qubits ({total_qubits}) could not be higher than the available qubits ({total_largest_connected_qubits})')
                

                mp_circuits = 0
                total_num_clbits = 0
                for qasm in qasm_files:

                    qc = self.get_circuit_properties(qasm_source=qasm, skip_simulation=True)

                    # check if the circuit has higher qubits than the existing largest connected component, then break it
                    if len(qc.circuit.qubits) > len(cm.largest_connected_component()):
                        print(f"This circuit's qubit ({len(qc.circuit.qubits)}) has higher than existing qubits({len(cm.largest_connected_component())})" )
                        break
                    
                    # compiled here for each circuits
                    updated_qasm, initial_mapping = self.compile(qasm=qc.qasm_original, 
                                                                compilation_name=compilation_name, 
                                                                noise_level=noise_level,
                                                                cm=cm,
                                                                mp_execution_type=mp_execution_type,
                                                                prune_options=prune_options)


                    tqc = QuantumCircuit.from_qasm_str(updated_qasm)

                    used_qubit = used_qubits(tqc)
                    for q in used_qubit:
                        prevously_used_qubits.append(q)

                    compiled_circuits[compilation_name].append({"circuit":tqc, "initial_layout":initial_mapping})
                    # compiled_circuits.append({"circuit":tqc, "initial_layout":tqc.layout.initial_layout})
                    
                    cm = build_idle_coupling_map(cm, used_qubit)

                    mp_circuits = mp_circuits + 1
                    
                    total_num_clbits = total_num_clbits + tqc.num_clbits

                # if the mp execution type is final, add the first compile circuit to be run, to compare as with the single run result
                if mp_execution_type == "final":
                    tmp_circuit = compiled_circuits[compilation_name][0]["circuit"]
                    tmp_qasm = dumps(tmp_circuit)

                    if conf.send_to_backend: 
                        database_wrapper.insert_to_result_detail(conn=self.conn, 
                                                                cursor=self.cursor, 
                                                                header_id=self.header_id, 
                                                                circuit_name=self.circuit_name, 
                                                                noisy_simulator=run_simulation, 
                                                                noise_level=noise_level, 
                                                                compilation_name=compilation_name, 
                                                                compilation_time=None, 
                                                                updated_qasm=tmp_qasm, 
                                                                observable=None, 
                                                                mp_circuits=None,
                                                                prune_options=prune_options) 
                    

                tmp_end_time = time.perf_counter()
                compilation_time = tmp_end_time - tmp_start_time

                if mp_execution_type != "partition":
                    final_circuit = merge_circuits(compiled_circuits[compilation_name],self.backend, num_cbits=total_num_clbits)
                    final_qasm = dumps(final_circuit)

                    if conf.send_to_backend: 
                        database_wrapper.insert_to_result_detail(conn=self.conn, 
                                                                cursor=self.cursor, 
                                                                header_id=self.header_id, 
                                                                circuit_name=self.circuit_name, 
                                                                noisy_simulator=run_simulation, 
                                                                noise_level=noise_level, 
                                                                compilation_name=compilation_name, 
                                                                compilation_time=compilation_time, 
                                                                updated_qasm=final_qasm, 
                                                                observable=None, 
                                                                mp_circuits=mp_circuits,
                                                                prune_options=prune_options) 
        
        return compiled_circuits


#region Run
    def run_simulator(self, 
                      program_type:str, 
                      qasm_files:list[str], 
                      compilations:list[str], 
                      noise_levels:list[float], 
                      shots:int, 
                      hardware_name:str = conf.hardware_name,
                      observables = None,
                      mitigation = None, 
                      send_to_db:bool = False,
                      apply_dd:bool = False, 
                      sequence_type:str = "XX", 
                      scheduling_method:str = "alap",
                      mp_options: dict[str,bool|str] = {"enable":False},
                      prune_options: dict[str,bool|tuple[int|float]|int|str] = {"enable":False},
                      seed_simulator: int = 123456
                      ):
        """
        
        """
        print("Start running the simulator...")
        # skip_simulation = False
        skip_simulation = True
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
            self.header_id = database_wrapper.init_result_header(self.cursor, self.user_id, hardware_name = hardware_name,
                                                                 token=self.token, shots=shots, program_type=program_type,
                                                                 seed_simulator=seed_simulator)
        else:
            conf.send_to_db = False

        # for multiprogramming
        if mp_options["enable"]:

            nodes_list = []

            # this is for the prune options for multiprogramming
            if prune_options["enable"]:
                nodes_list = self._get_prune_node_list(prune_options)


            compiled_circuits = self.compile_multiprogramming(qasm_files=qasm_files, 
                                                              compilations=compilations,
                                                              exclude_qubits=nodes_list,
                                                              mp_execution_type=mp_options["execution_type"],
                                                              prune_options=prune_options,
                                                              run_simulation=True,
                                                              noise_levels=noise_levels
                                                              )

        else: # for normal 

            for idx, qasm in enumerate(qasm_files):
                qc = self.get_circuit_properties(qasm_source=qasm, skip_simulation=skip_simulation)

                for comp in compilations:

                    for noise_level in noise_levels:
                        print(comp, noise_level)
                        noise_model, noisy_simulator, coupling_map = qiskit_wrapper.get_noisy_simulator(self.real_backend, noise_level)

                        # set the backend and the program
                        self.set_backend(program_type=program_type, backend=noisy_simulator, shots=shots)

                        observable = None
                        if program_type == "estimator":
                            observable = observables[idx]

                        updated_qasm, initial_mapping = self.compile(qasm=qc.qasm_original, 
                                                                     observable=observable, 
                                                                     compilation_name=comp, 
                                                                     generate_props=False, 
                                                                     noise_level=noise_level)
                    
        if send_to_db:  
            # Send to local simulator
            self.run_on_noisy_simulator_local()
                  

        # return df
    
    def send_to_real_backend(self, 
                             program_type: str, 
                             qasm_files: str, 
                             compilations: list[str], 
                             shots: int=conf.shots, 
                             hardware_name: str = conf.hardware_name,
                             dd_options: DynamicalDecouplingOptions = {"enable":False}, 
                             twirling_options: TwirlingOptions = {"enable":False},
                             mp_options: dict[str,bool|str] = {"enable":False},
                             prune_options: dict[str,bool|tuple[int|float]|int|str] = {"enable":False}
                             ):
        """
        mp_options:
        1. enable: deterimine whether using multiprogramming or not
        2. execution_type: determine how the multiprogramming create a circuit
           - all = run the circuits individually + the final merged circuit
           - partition = run the circuits individually
           - final = run only the final merged circuit

        prune_options:
        1. enable: deterimine whether using multiprogramming or not
        2. type: determine which pruning type to create coupling map
            - calibration: use the threshold of the two-qubit gates and readout. Params: (cx,ro): tuple
            - lf: use the qubits from LF benchmark. Params: lf: int, number qubits
        """
        # Update the
        conf.send_to_db = True
        conf.hardware_name = hardware_name

        # init header
        self.header_id = database_wrapper.init_result_header(self.cursor, self.user_id, hardware_name=hardware_name, token=self.token, shots=shots, 
                                                             dd_options=dd_options)
        
        # for multiprogramming
        if mp_options["enable"]:

            nodes_list = []

            # this is for the prune options for multiprogramming
            if prune_options["enable"]:
                nodes_list = self._get_prune_node_list(prune_options)


            compiled_circuits = self.compile_multiprogramming(qasm_files=qasm_files, 
                                                              compilations=compilations,
                                                              exclude_qubits=nodes_list,
                                                              mp_execution_type=mp_options["execution_type"],
                                                              prune_options=prune_options
                                                              )

        else: # for normal 
            for qasm in qasm_files:
                skip = False
                if "polar" in qasm:
                    skip = True

                qc = self.get_circuit_properties(qasm_source=qasm, skip_simulation=skip)
                
                for comp in compilations:
                    print("Compiling circuit: {} for compilation: {}".format(self.circuit_name, comp))
                    self.compile(qasm=qc.qasm_original, 
                                 compilation_name=comp,
                                 prune_options=prune_options)

        if conf.noisy_simulator:
            # Send to local simulator, just send to the database, execution is on scheduler.py
            self.run_on_noisy_simulator_local()
        else:
            # Send to backend
            self.send_qasm_to_real_backend(program_type, dd_options=dd_options, twirling_options=twirling_options)


                
#endregion

    def get_qiskit_result(self, type=None, noisy_simulator=None):
        pending_jobs = database_wrapper.get_pending_jobs()
            
        tmp_qiskit_token = ""
        header_id, job_id, qiskit_token = None, None, None
        service = None
        
        print('Pending jobs: ', len(pending_jobs))
        for result in pending_jobs:
            header_id, job_id, qiskit_token, hw_name = result

            # print("processing...", header_id, job_id, qiskit_token)

            if type == "simulator" and job_id != "simulator":
                continue

            if type == "real" and job_id == "simulator":
                continue

            if tmp_qiskit_token == "" or tmp_qiskit_token != qiskit_token:
                if conf.use_ibm_cloud:
                    print("Using IBM Cloud...")
                    token = "tyF4ya7NOGlq9Ls_JM5JJ0vG0IJmdu_Ea2rc-xTauvJ_"
                    self.token = "tyF4ya7NOGlq9Ls_JM5JJ0vG0IJmdu_Ea2rc-xTauvJ_"
                    service = QiskitRuntimeService(channel="ibm_cloud", token=token, instance=conf.ibm_cloud_instance)
                else:
                    QiskitRuntimeService.save_account(channel="ibm_quantum", token=qiskit_token, overwrite=True)
                    service = QiskitRuntimeService(channel="ibm_quantum", token=token)

            if job_id == "simulator":
                process_simulator(service, header_id, job_id, hw_name, noisy_simulator=noisy_simulator)
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
