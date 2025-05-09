"""
file name: triq_wrapper.py
author: Handy
date: 13 June 2024

This module provides all the function necesary dealing with database

Functions:


Example:
"""
import subprocess as sp
import sys
import os
from datetime import datetime
import time, json
import mysql.connector

from commons import (Config, convert_utc_to_local, calculate_time_diff, convert_to_json)
from ..qiskit_wrapper import QiskitCircuit

conf = Config()
debug = conf.activate_debugging_time

def init_result_header(cursor, 
                       user_id: int, 
                       hardware_name: str = conf.hardware_name, 
                       token: str=conf.qiskit_token, 
                       program_type: str = "sampler", 
                       shots: int = conf.shots,
                       dd_options: dict = {"enable":False},
                       seed_simulator: int = None
                       ):
    if debug: tmp_start_time  = time.perf_counter()

    dd_enable = None
    dd_sequence_type = None
    dd_scheduling_method = None

    if dd_options["enable"]:
        dd_enable = 1
        dd_sequence_type = dd_options["sequence_type"]
        dd_scheduling_method = dd_options["scheduling_method"]

    now_time = datetime.now().strftime("%Y%m%d%H%M%S")
    cursor.execute("""INSERT INTO result_header (user_id, hw_name, qiskit_token, program_type,
                   dd_enable, dd_sequence_type, dd_scheduling_method, 
                   shots, runs, seed, created_datetime) 
    VALUES (%s, %s, %s, %s, 
            %s, %s, %s,
            %s, %s, %s, %s)""",
    (user_id, hardware_name, token, program_type, 
     dd_enable, dd_sequence_type, dd_scheduling_method,
     shots, conf.runs, seed_simulator, now_time))

    header_id = cursor.lastrowid

    if debug: tmp_end_time = time.perf_counter()
    if debug: print("Time for running the init header: {} seconds".format(tmp_end_time - tmp_start_time))

    return header_id
    
def insert_to_result_detail(conn, 
                            cursor, 
                            header_id: int, 
                            circuit_name: str, 
                            noisy_simulator:bool, 
                            noise_level:float, 
                            compilation_name: str, 
                            compilation_time, 
                            updated_qasm, 
                            observable=None, 
                            initial_mapping = "", 
                            final_mapping = "",
                            mp_circuits=None,
                            prune_options: dict[str,bool|tuple[int|float]|int|str] = {"enable":False}
                            ):
        now_time = datetime.now().strftime("%Y%m%d%H%M%S")
        
        noisy_simulator_flag = None
        if noisy_simulator: 
            noisy_simulator_flag = 1
            # noise_level = 1
        else:
            noise_level = None
        
            
        sql = """
        INSERT INTO result_detail
        (header_id, circuit_name, observable, compilation_name, compilation_time, 
        initial_mapping, final_mapping, noisy_simulator, noise_level, mp_circuits, 
        prune_type, prune_parameters, created_datetime)
        VALUES (%s, %s, %s, %s, %s, 
        %s, %s, %s, %s, %s,
        %s, %s, %s);
        """

        str_initial_mapping = None
        if initial_mapping != None:
            str_initial_mapping = ', '.join(str(x) for x in initial_mapping)

        str_observable = None
        if observable != None:
            str_observable = ",".join(observable)

        json_final_mapping = ""
        if final_mapping != "":
            json_final_mapping = json.dumps(final_mapping, default=str)

        prune_type = None
        prune_parameters = None
        if prune_options["enable"]:
            prune_type = prune_options["type"]
            prune_parameters = str(prune_options["params"])


        params = (header_id, circuit_name, str_observable, compilation_name, compilation_time, 
                  str_initial_mapping, json_final_mapping, noisy_simulator_flag, noise_level, mp_circuits,
                  prune_type, prune_parameters, now_time)

        cursor.execute(sql, params)
        detail_id = cursor.lastrowid

        sql = """
        INSERT INTO result_updated_qasm
        (detail_id, updated_qasm)
        VALUES (%s, %s);
        """

        cursor.execute(sql, (detail_id, updated_qasm))

        conn.commit()

def update_circuit_data(conn, cursor, qc: QiskitCircuit, skip):
    gates_json = convert_to_json(qc.gates)
    circuit_name = qc.name
    correct_output = ""

    # check if the metric is already there, just update
    sql = 'SELECT name FROM circuit WHERE name = %s'
    param = (circuit_name,)
    cursor.execute(sql, param)
    existing_row = cursor.fetchone()
    
    if existing_row:
        sql = 'SELECT name, correct_output FROM circuit WHERE name = %s'
        param = (circuit_name,)
        cursor.execute(sql, param)
        results = cursor.fetchall()
        name, correct_output = results[0]

    if skip:
        correct_output_json = correct_output
    else:
        correct_output_json = convert_to_json(qc.correct_output)

    # insert to the table
    if not existing_row:

        if skip:
            cursor.execute("""INSERT INTO circuit (name, qasm, depth, total_gates, gates)
            VALUES (%s, %s, %s, %s, %s)""",
            (circuit_name, qc.qasm, qc.depth, qc.total_gate, gates_json))
        else:
            cursor.execute("""INSERT INTO circuit (name, qasm, depth, total_gates, gates, correct_output)
            VALUES (%s, %s, %s, %s, %s, %s)""",
            (circuit_name, qc.qasm, qc.depth, qc.total_gate, gates_json, correct_output_json))

        conn.commit()

        # print(circuit_name, "has been registered to the database.")
    else:
        if skip:
            cursor.execute("""UPDATE circuit SET qasm = %s, depth  = %s, total_gates  = %s, gates = %s 
                                WHERE name = %s""",
            (qc.qasm, qc.depth, qc.total_gate, gates_json, circuit_name))
        else:
            cursor.execute("""UPDATE circuit SET qasm = %s, depth  = %s, total_gates  = %s, gates = %s, correct_output = %s 
                                WHERE name = %s""",
            (qc.qasm, qc.depth, qc.total_gate, gates_json, correct_output_json, circuit_name))

        conn.commit()
        # print(circuit_name, "already exist.")

def get_header_with_null_job(cursor):

    cursor.execute('SELECT id, qiskit_token, shots, runs FROM result_header WHERE job_id IS NULL;')

    return cursor.fetchall()

def get_detail_with_header_id(cursor, header_id):
    cursor.execute('''SELECT d.id, q.updated_qasm, d.compilation_name 
FROM result_detail d
INNER JOIN result_header h ON d.header_id = h.id
INNER JOIN result_updated_qasm q ON d.id = q.detail_id 
WHERE h.job_id IS NULL AND d.header_id = %s  ''', (header_id,)
)
    
    return cursor.fetchall()

def get_pending_jobs():
    '''
    Returns job_id if the status in the calibration_data.result_detail table is pending (job has been sent to backend and we are waiting for the result)
    '''
    
    try:
        conn = mysql.connector.connect(**conf.mysql_config)
        cursor = conn.cursor()
        
        cursor.execute('''SELECT distinct h.id, h.job_id, qiskit_token, hw_name 
                       FROM framework.result_header h 
                        INNER JOIN framework.result_detail d ON h.id = d.header_id 
                        WHERE h.status = %s ''', ("pending",))
        
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()

    except Exception as e:
        print("An error occurred:", str(e))
        
    return results

def get_executed_jobs():
    '''
    Returns job_id if the status in the result_detail table is executed (job has been executed in the backend and we have to compute metrics)
    '''
    
    try:
        conn = mysql.connector.connect(**conf.mysql_config)
        cursor = conn.cursor()

        cursor.execute('''SELECT id, job_id FROM result_header WHERE status = %s;''', ("executed", ))

        results = cursor.fetchall()
        cursor.close()
        conn.close()

    except Exception as e:
        print("An error occurred:", str(e))
        
    return results

def update_result_header_status_by_header_id(header_id, new_status):
    '''
    Updates result_header entries that contained prev_status to new_status by header_id
    '''
    conn = mysql.connector.connect(**conf.mysql_config)
    cursor = conn.cursor()
    cursor.execute('UPDATE result_header SET status = %s, updated_datetime = NOW() WHERE id = %s', (new_status, header_id))
    conn.commit()
    cursor.close()
    conn.close()

def update_result_header_job_id_by_header_id(header_id, new_job_id):
    '''
    Updates result_header entries that contained prev_status to new_status by header_id
    '''
    conn = mysql.connector.connect(**conf.mysql_config)
    cursor = conn.cursor()
    cursor.execute('UPDATE result_header SET job_id = %s, updated_datetime = NOW() WHERE id = %s', (new_job_id, header_id))
    conn.commit()
    cursor.close()
    conn.close()

def update_result_header(cursor, job):
    execution_time = job.metrics()["usage"]["quantum_seconds"]
    job_time = job.metrics()["timestamps"]
    created_datetime = convert_utc_to_local(job_time["created"])
    running_datetime = convert_utc_to_local(job_time["running"])
    completed_datetime = convert_utc_to_local(job_time["finished"])
    in_queue_second = calculate_time_diff(job_time["created"], job_time["running"])
    job_id = job.job_id()

    cursor.execute("""UPDATE result_header SET status = %s, execution_time = %s, job_created_datetime = %s, 
    job_in_queue_second = %s, job_running_datetime = %s, job_completed_datetime = %s, updated_datetime = NOW()  
    WHERE job_id = %s""", ("executed", execution_time, created_datetime, 
                            in_queue_second, running_datetime, completed_datetime, job_id))
