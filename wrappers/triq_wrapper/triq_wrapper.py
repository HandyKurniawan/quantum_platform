"""
file name: triq_wrapper.py
author: Handy, Laura, Fran
date: 14 September 2023

This module provides all the function necesary to run TriQ

Functions:
- run(qasm_path, hardware_name, triq_optimization): run the optimization from TriQ

Example:
"""
import subprocess as sp
import sys
import os
from datetime import datetime
from .ir2dag import parse_ir
import time, json
import mysql.connector
from commons import calibration_type_enum, sql_query, normalize_counts, Config

conf = Config()

triq_path = os.path.expanduser(conf.triq_path)
# triq_path = os.path.expanduser("/Users/handy/Github/quantum_platform/wrappers/triq_wrapper")

out_path = os.path.expanduser("./")
dag_path = os.path.expanduser("./")
map_path = os.path.expanduser("./")
base_name = "output"
map_name = "init_mapo.map"
dag_name = base_name + ".in"
out_name = base_name + ".qasm"
dag_file_path = os.path.join(dag_path, dag_name)
out_file_path = os.path.join(out_path, out_name)
map_file_path = os.path.join(map_path, map_name)


def read_file(file_path):
    success = False
    while not success:
        try:
            with open(file_path, "r") as file:
                # Read the contents of the file and store them in the variable
                file_contents = file.read()
        except FileNotFoundError:
            print(f"File not found: {file_path}")
        except Exception as e:
            print(f"An error occurred: {str(e)}")

        success = True

    return file_contents

def create_dir(path):
    isExist = os.path.exists(path)
    if not isExist:
        # Create a new directory because it does not exist
        os.makedirs(path)

def generate_qasm(qasm_str, hardware_name, triq_optimization, measurement_type):
    tmp_hw_name = hardware_name

    # parse qasm into .in
    parse_ir(qasm_str, os.path.join(dag_path, dag_name))

    # call triq
    call_triq = [os.path.join(triq_path, "triq"), 
                dag_file_path, 
                out_file_path, tmp_hw_name, str(triq_optimization), map_file_path, measurement_type]

    out_file=open("log/output.log",'w+')

    p = sp.Popen(call_triq, stdout=out_file, text=True, shell=False)    
    p.communicate()
    p.terminate()
    p.wait()
    p.kill()

    # print(out_file_path)
    result_qasm = read_file(out_file_path)

    return result_qasm

def run(qasm_str, hardware_name, triq_optimization, measurement_type = "normal"):
    """
    Parameters:
        qasm_path:
        hardware_name:
        triq_optimization:
    """
    
    result_qasm = generate_qasm(qasm_str, hardware_name, triq_optimization, measurement_type)

    if (os.path.isfile(dag_file_path)):
        os.remove(dag_file_path)

    if (os.path.isfile(out_file_path)):
        os.remove(out_file_path)


    return result_qasm

def get_mapping(qasm_str, hardware_name, triq_optimization):
    """
    Parameters:
        qasm_path:
        hardware_name:
        triq_optimization:
    """
    # result_qasm = generate_qasm(qasm_str, hardware_name, triq_optimization)

    log_path = os.path.expanduser("./log/output.log")

    mapping_dict = None
    with open(log_path, "r") as file:
        mapping_dict = json.load(file)

    # if (os.path.isfile(log_path)):
    #     os.remove(log_path)

    return mapping_dict

def generate_initial_mapping_file(init_maps):
    string_maps = ', '.join(map(str, init_maps))
    # print("Initial mapping path :", string_maps)
    f = open(map_file_path, "w+")
    f.write(string_maps)
    f.close()

def get_compilation_config(compilation_name, hw_name = conf.hardware_name):
    calibration_type = calibration_type_enum.lcd.value

    if compilation_name == "triq_lcd":
        calibration_type = calibration_type_enum.lcd.value
    elif compilation_name == "triq_avg":
        calibration_type = calibration_type_enum.average.value
    elif compilation_name == "triq_mix":
        calibration_type = calibration_type_enum.mix.value
    elif compilation_name == "triq_w15_adj":
        calibration_type = calibration_type_enum.recent_15_adjust.value

    hardware_name = ""
    if compilation_name == "triq_lcd":
        hardware_name = hw_name + "_" + "real"
    elif compilation_name == "triq_avg":
        hardware_name = hw_name + "_" + "avg"
    elif compilation_name == "triq_mix":
        hardware_name = hw_name + "_" + "mix"
    elif compilation_name == "triq_w15_adj":
        hardware_name = hw_name + "_" + "recent_15_adj"

    return calibration_type, hardware_name

#region Calibration Config

def generate_realtime_calibration_data(qem, hw_name = conf.hardware_name):
    # Connect to the MySQL database
    conn = mysql.connector.connect(**conf.mysql_calibration_config)
    cursor = conn.cursor()

    # get last calibration id
    cursor.execute('''SELECT calibration_id, 2q_native_gates FROM calibration_data.ibm i
INNER JOIN calibration_data.hardware h ON i.hw_name = h.hw_name
WHERE i.hw_name = %s ORDER BY calibration_datetime DESC LIMIT 0, 1;
                    ''', (hw_name, ))
    results = cursor.fetchall()
    calibration_id, native_gates_2q = results[0]

    # get 1 qubit gate error
    cursor.execute('''SELECT calibration_id, qubit, 1 - x_error as fidelity_1q 
                   FROM calibration_data.ibm_one_qubit_gate_spec 
                   WHERE calibration_id = %s;
                    ''', (calibration_id, ))
    # print(calibration_id)
    results = cursor.fetchall()
    count = len(results)
    if count > 0:
        f = open("./config/" + hw_name + "_real_S.rlb", "w+")
        f.write("{}\n".format(count))
        for res in results:
            calibration_id, qubit, fidelity_1q = res
            f.write("{} {} \n".format(qubit, fidelity_1q))

        f.close()

    # get 2 qubit gate error
    cursor.execute('''SELECT calibration_id, qubit_control, qubit_target, ROUND(1 - ''' + native_gates_2q + '''_error, 6) as fidelity_2q
                   FROM calibration_data.ibm_two_qubit_gate_spec 
                   WHERE calibration_id = %s ;
                    ''', (calibration_id, ))
    # AND ''' + native_gates_2q + '''_error != 1
    results = cursor.fetchall()
    count = len(results)
    if count > 0:
        f = open("./config/" + hw_name + "_real_T.rlb", "w+")
        f.write("{}\n".format(count))
        for res in results:
            calibration_id, qubit_control, qubit_target, fidelity_2q = res

            if fidelity_2q <= 0:
                fidelity_2q = 0.001

            f.write("{} {} {} \n".format(qubit_control, qubit_target, fidelity_2q))

        f.close()

    # get readout error
    cursor.execute('''SELECT calibration_id, qubit, 1 - readout_error as readout_fidelity
                   FROM calibration_data.ibm_qubit_spec 
                   WHERE calibration_id = %s;
                    ''', (calibration_id, ))
    results = cursor.fetchall()
    count = len(results)
    if count > 0:
        f = open("./config/" + hw_name + "_real_M.rlb", "w+")
        f.write("{}\n".format(count))
        for res in results:
            calibration_id, qubit, readout_fidelity = res
            f.write("{} {}\n".format(qubit, readout_fidelity))

        f.close()

    conn.close()

def generate_average_calibration_data(qem, hw_name = conf.hardware_name):
    # Connect to the MySQL database
    conn = mysql.connector.connect(**conf.mysql_calibration_config)
    cursor = conn.cursor()

    # get last calibration id
    cursor.execute('''SELECT calibration_id, 2q_native_gates FROM calibration_data.ibm i
INNER JOIN calibration_data.hardware h ON i.hw_name = h.hw_name
WHERE i.hw_name = %s ORDER BY calibration_datetime DESC LIMIT 0, 1;
                    ''', (hw_name, ))
    results = cursor.fetchall()
    calibration_id, native_gates_2q = results[0]

    # get 1 qubit gate error
    cursor.execute('''
SELECT qubit, AVG(x_fidelity), STDDEV(x_fidelity), MAX(x_fidelity), MIN(x_fidelity) FROM (
SELECT DISTINCT qubit, 1 - x_error AS x_fidelity, x_date 
FROM calibration_data.ibm_one_qubit_gate_spec q
WHERE q.hw_name = %s
) X GROUP BY qubit;
                    ''', (hw_name, ))
    results = cursor.fetchall()
    count = len(results)
    if count > 0:
        f = open("./config/{}_avg_S.rlb".format(hw_name), "w+")
        f.write("{}\n".format(count))
        for res in results:
            qubit, fidelity_1q, fidelity_1q_std, fidelity_1q_max, fidelity_1q_min = res
            f.write("{} {} \n".format(qubit, fidelity_1q))

        f.close()

    # get 2 qubit gate error
    cursor.execute('''
SELECT qubit_control, qubit_target, AVG(''' + native_gates_2q + '''_fidelity), STDDEV(''' + native_gates_2q + '''_fidelity), 
MAX(''' + native_gates_2q + '''_fidelity), MIN(''' + native_gates_2q + '''_fidelity) FROM (
SELECT DISTINCT qubit_control, qubit_target, 1 - ''' + native_gates_2q + '''_error AS ''' + native_gates_2q + '''_fidelity, 
''' + native_gates_2q + '''_date 
FROM calibration_data.ibm_two_qubit_gate_spec q
WHERE q.hw_name = %s 
) X GROUP BY qubit_control, qubit_target;
                    ''', (hw_name, ))
    results = cursor.fetchall()
    count = len(results)
    if count > 0:
        f = open("./config/{}_avg_T.rlb".format(hw_name), "w+")
        f.write("{}\n".format(count))
        for res in results:
            qubit_control, qubit_target, fidelity_2q, fidelity_2q_std, fidelity_2q_max, fidelity_2q_min = res

            if fidelity_2q <= 0:
                fidelity_2q = 0.001

            f.write("{} {} {} \n".format(qubit_control, qubit_target, fidelity_2q))

        f.close()

    # get readout error
    cursor.execute('''
SELECT qubit, AVG(readout_fidelity), STDDEV(readout_fidelity), MAX(readout_fidelity), MIN(readout_fidelity) FROM (
SELECT DISTINCT qubit, 1 - readout_error AS readout_fidelity, readout_error_date FROM calibration_data.ibm_qubit_spec q
INNER JOIN calibration_data.ibm i ON q.calibration_id = i.calibration_id 
WHERE i.hw_name = %s 
) X GROUP BY qubit;
                    ''', (hw_name, ))
    results = cursor.fetchall()
    count = len(results)
    if count > 0:
        f = open("./config/{}_avg_M.rlb".format(hw_name), "w+")
        f.write("{}\n".format(count))
        for res in results:
            qubit, readout_fidelity, readout_fidelity_std, readout_fidelity_max, readout_fidelity_min = res
            f.write("{} {}\n".format(qubit, readout_fidelity))

        f.close()

    conn.close()

def generate_recent_average_calibration_data(qem, days, adjust = False, hw_name = conf.hardware_name):
    # Connect to the MySQL database
    conn = mysql.connector.connect(**conf.mysql_calibration_config)
    cursor = conn.cursor()

    # get last calibration id
    cursor.execute('''SELECT calibration_id, 2q_native_gates, number_of_qubit FROM calibration_data.ibm i
INNER JOIN calibration_data.hardware h ON i.hw_name = h.hw_name
WHERE i.hw_name = %s ORDER BY calibration_datetime DESC LIMIT 0, 1;
                    ''', (hw_name, ))
    results = cursor.fetchall()
    calibration_id, native_gates_2q, number_of_qubit = results[0]

    std_1q_error = {}
    avg_1q_error = {}
    if adjust:
        # get STD of 1 qubit gate error
        sql = """SELECT qubit, STDDEV(x_error), AVG(x_error) FROM (
        SELECT DISTINCT qubit, x_error, x_date 
        FROM calibration_data.ibm_one_qubit_gate_spec q
        WHERE q.hw_name = %s
        ) X GROUP BY qubit;"""
        cursor.execute(sql, (hw_name,))
        results = cursor.fetchall()
        count = len(results)
        if count > 0:
            for res in results:
                qubit, error, avg_error = res
                std_1q_error[qubit] = float(error)
                avg_1q_error[qubit] = float(avg_error) + float(error) + float(error)

    # get 1 qubit gate error
    cursor.execute('''
SELECT qubit, AVG(x_fidelity), STDDEV(x_fidelity), MAX(x_fidelity), MIN(x_fidelity) FROM (
SELECT DISTINCT qubit, 1 - x_error AS x_fidelity, x_date 
FROM calibration_data.ibm_one_qubit_gate_spec q
WHERE q.hw_name = %s
AND x_date BETWEEN date_add(now(), INTERVAL %s DAY) AND now()
) X GROUP BY qubit;
                    ''', (hw_name, days * -1))
    results = cursor.fetchall()
    count = len(avg_1q_error)
    if count > 0:
        file_name = "./config/{}_recent_{}_S.rlb".format(hw_name, days)
        if adjust:
            file_name = "./config/{}_recent_{}_adj_S.rlb".format(hw_name, days)

        f = open(file_name, "w+")
        f.write("{}\n".format(count))

        fidelity_dict = {}
        # initialized with avg error + 2 std error, to solve the problem with uncalibrated qubit
        for qubit, fidelity_1q in avg_1q_error.items():
            fidelity_dict[qubit] = fidelity_1q

        for res in results:
            qubit, fidelity_1q, fidelity_1q_std, fidelity_1q_max, fidelity_1q_min = res

            if adjust:
                fidelity_1q = float(fidelity_1q) - std_1q_error[qubit]

            if fidelity_1q <= 0:
                fidelity_1q = 0.001

            fidelity_dict[qubit] = fidelity_1q

        for qubit, fidelity_1q in fidelity_dict.items():   
            f.write("{} {} \n".format(qubit, fidelity_1q))

        f.close()

    std_2q_error = {}
    avg_2q_error = {}
    if adjust:
        # get STD of 2 qubit gate error
        sql = '''SELECT qubit_control, qubit_target, STDDEV(''' + native_gates_2q + '''_error), AVG(''' + native_gates_2q + '''_error)
        FROM (
SELECT DISTINCT qubit_control, qubit_target, ''' + native_gates_2q + '''_error, 
''' + native_gates_2q + '''_date 
FROM calibration_data.ibm_two_qubit_gate_spec q
WHERE q.hw_name = %s 
) X GROUP BY qubit_control, qubit_target;'''
        cursor.execute(sql, (hw_name,))
        results = cursor.fetchall()
        count = len(results)
        if count > 0:
            for res in results:
                qubit_control, qubit_target, error, avg_error = res
                qubits = (qubit_control, qubit_target)
                std_2q_error[qubits] = float(error)
                avg_2q_error[qubits] = float(avg_error) + float(error) + float(error)

    # get 2 qubit gate error
    cursor.execute('''
SELECT qubit_control, qubit_target, AVG(''' + native_gates_2q + '''_fidelity), STDDEV(''' + native_gates_2q + '''_fidelity), 
MAX(''' + native_gates_2q + '''_fidelity), MIN(''' + native_gates_2q + '''_fidelity) FROM (
SELECT DISTINCT qubit_control, qubit_target, 1 - ''' + native_gates_2q + '''_error AS ''' + native_gates_2q + '''_fidelity, 
''' + native_gates_2q + '''_date 
FROM calibration_data.ibm_two_qubit_gate_spec q
WHERE q.hw_name = %s 
AND ''' + native_gates_2q + '''_date BETWEEN date_add(now(), INTERVAL %s DAY) AND now()
) X GROUP BY qubit_control, qubit_target;
                    ''', (hw_name, days * -1))
    results = cursor.fetchall()
    count = len(avg_2q_error)
    if count > 0:
        file_name = "./config/{}_recent_{}_T.rlb".format(hw_name, days)
        if adjust:
            file_name = "./config/{}_recent_{}_adj_T.rlb".format(hw_name, days)

        f = open(file_name, "w+")
        f.write("{}\n".format(count))

        fidelity_dict = {}
        
        # initialized with avg error + 2 std error, to solve the problem with uncalibrated qubit
        for qubits, fidelity_2q in avg_2q_error.items():
            fidelity_dict[qubits] = fidelity_2q

        for res in results:
            qubit_control, qubit_target, fidelity_2q, fidelity_2q_std, fidelity_2q_max, fidelity_2q_min = res
            qubits = (qubit_control, qubit_target)

            if adjust:    
                fidelity_2q = float(fidelity_2q) - std_2q_error[qubits]

            if fidelity_2q <= 0:
                fidelity_2q = 0.001

            fidelity_dict[qubits] = fidelity_2q

        for qubits, fidelity_2q in fidelity_dict.items():  
            qubit_control = qubits[0]
            qubit_target = qubits[1]
            f.write("{} {} {} \n".format(qubit_control, qubit_target, fidelity_2q))

        f.close()

    std_readout_error = {}
    avg_readout_error = {}
    if adjust:
        # get STD of 1 qubit gate error
        sql = """SELECT qubit, STDDEV(readout_error), AVG(readout_error) FROM (
SELECT DISTINCT qubit, readout_error, readout_error_date FROM calibration_data.ibm_qubit_spec q
INNER JOIN calibration_data.ibm i ON q.calibration_id = i.calibration_id 
WHERE i.hw_name = %s
) X GROUP BY qubit;"""
        cursor.execute(sql, (hw_name,))
        results = cursor.fetchall()
        count = len(results)
        if count > 0:
            for res in results:
                qubit, error, avg_error = res
                std_readout_error[qubit] = float(error)
                avg_readout_error[qubit] = float(avg_error) + float(error) + float(error)

    # get readout error
    cursor.execute('''
SELECT qubit, AVG(readout_fidelity), STDDEV(readout_fidelity), MAX(readout_fidelity), MIN(readout_fidelity) FROM (
SELECT DISTINCT qubit, 1 - readout_error AS readout_fidelity, readout_error_date FROM calibration_data.ibm_qubit_spec q
INNER JOIN calibration_data.ibm i ON q.calibration_id = i.calibration_id 
WHERE i.hw_name = %s AND readout_error_date BETWEEN date_add(now(), INTERVAL %s DAY) AND now()
) X GROUP BY qubit;
                    ''', (hw_name, days * -1))
    results = cursor.fetchall()
    count = len(avg_readout_error)
    if count > 0:
        file_name = "./config/{}_recent_{}_M.rlb".format(hw_name, days)
        if adjust:
            file_name = "./config/{}_recent_{}_adj_M.rlb".format(hw_name, days)

        f = open(file_name, "w+")
        f.write("{}\n".format(count))

        fidelity_dict = {}
        # initialized with avg error + 2 std error, to solve the problem with uncalibrated qubit
        for qubit, readout_fidelity in avg_readout_error.items():
            fidelity_dict[qubit] = readout_fidelity

        # update with chosen calculated days
        for res in results:
            qubit, readout_fidelity, readout_fidelity_std, readout_fidelity_max, readout_fidelity_min = res
            
            if adjust:
                readout_fidelity = float(readout_fidelity) - std_readout_error[qubit]

            if readout_fidelity <= 0:
                readout_fidelity = 0.001

            fidelity_dict[qubit] = readout_fidelity

        for qubit, readout_fidelity in fidelity_dict.items():
            f.write("{} {}\n".format(qubit, readout_fidelity))

        f.close()

    conn.close()

def generate_mix_calibration_data(qem, hw_name = conf.hardware_name):
    # Connect to the MySQL database
    conn = mysql.connector.connect(**conf.mysql_calibration_config)
    cursor = conn.cursor()

    # get last calibration id
    cursor.execute('''SELECT calibration_id, 2q_native_gates, DATE_FORMAT(calibration_datetime, '%Y%m%d') 
FROM calibration_data.ibm i
INNER JOIN calibration_data.hardware h ON i.hw_name = h.hw_name
WHERE i.hw_name = %s ORDER BY calibration_datetime DESC LIMIT 0, 1;
''', (hw_name, ))
    results = cursor.fetchall()
    calibration_id, native_gates_2q, calibration_date = results[0]

    # get readout fidelity
    cursor.execute('''SELECT calibration_id, q.qubit, 
CASE WHEN DATE_FORMAT(q.readout_error_date , '%Y%m%d') = %s 
THEN 1 - readout_error ELSE readout_fidelity_avg - readout_fidelity_std END AS readout_fidelity
FROM calibration_data.ibm_qubit_spec q
INNER JOIN (SELECT qubit, AVG(readout_fidelity) AS readout_fidelity_avg, 
STDDEV(readout_fidelity) AS readout_fidelity_std, 
MAX(readout_fidelity) AS readout_fidelity_max, 
MIN(readout_fidelity) AS readout_fidelity_min FROM (
SELECT DISTINCT qubit, 1 - readout_error AS readout_fidelity, readout_error_date FROM calibration_data.ibm_qubit_spec q
INNER JOIN calibration_data.ibm i ON q.calibration_id = i.calibration_id 
WHERE i.hw_name = %s) X GROUP BY qubit) a ON q.qubit = a.qubit
WHERE q.calibration_id = %s;
''', (calibration_date, hw_name, calibration_id, ))
    results = cursor.fetchall()
    count = len(results)
    if count > 0:
        f = open("./config/" + hw_name + "_mix_M.rlb", "w+")
        f.write("{}\n".format(count))
        for res in results:
            calibration_id, qubit, readout_fidelity = res
            f.write("{} {} \n".format(qubit, readout_fidelity))

        f.close()

    # get 1 qubit gate error
    cursor.execute('''SELECT calibration_id, q.qubit, 
CASE WHEN DATE_FORMAT(q.x_date , '%Y%m%d') = %s 
THEN 1 - x_error ELSE x_fidelity_avg - x_fidelity_std END AS fidelity_2q
FROM calibration_data.ibm_one_qubit_gate_spec q
INNER JOIN (SELECT qubit, AVG(x_fidelity) AS x_fidelity_avg, 
STDDEV(x_fidelity) AS x_fidelity_std, 
MAX(x_fidelity) AS x_fidelity_max, 
MIN(x_fidelity) AS x_fidelity_min FROM (
SELECT DISTINCT qubit, 1 - x_error AS x_fidelity, x_date FROM calibration_data.ibm_one_qubit_gate_spec q
INNER JOIN calibration_data.ibm i ON q.calibration_id = i.calibration_id 
WHERE i.hw_name = %s) X GROUP BY qubit) a ON q.qubit = a.qubit
WHERE q.calibration_id = %s;
''', (calibration_date, hw_name, calibration_id, ))
    results = cursor.fetchall()
    count = len(results)
    if count > 0:
        f = open("./config/" + hw_name + "_mix_S.rlb", "w+")
        f.write("{}\n".format(count))
        for res in results:
            calibration_id, qubit, fidelity_1q = res
            f.write("{} {}\n".format(qubit, fidelity_1q))

        f.close()

# - ''' + native_gates_2q + '''_fidelity_std

    # get 2 qubit gate error
    cursor.execute('''SELECT calibration_id, q.qubit_control, q.qubit_target, 
CASE WHEN DATE_FORMAT(q.''' + native_gates_2q + '''_date , '%Y%m%d') = %s 
THEN 1 - ''' + native_gates_2q + '''_error ELSE ''' + native_gates_2q + '''_fidelity_avg END AS ''' + native_gates_2q + '''_fidelity
FROM calibration_data.ibm_two_qubit_gate_spec q
INNER JOIN (SELECT qubit_control, qubit_target, AVG(''' + native_gates_2q + '''_fidelity) AS ''' + native_gates_2q + '''_fidelity_avg, 
STDDEV(''' + native_gates_2q + '''_fidelity) AS ''' + native_gates_2q + '''_fidelity_std, 
MAX(''' + native_gates_2q + '''_fidelity) AS ''' + native_gates_2q + '''_fidelity_max, 
MIN(''' + native_gates_2q + '''_fidelity) AS ''' + native_gates_2q + '''_fidelity_min FROM (
SELECT DISTINCT qubit_control, qubit_target, 1 - ''' + native_gates_2q + '''_error AS ''' + native_gates_2q + '''_fidelity, ''' + native_gates_2q + '''_date FROM calibration_data.ibm_two_qubit_gate_spec q
INNER JOIN calibration_data.ibm i ON q.calibration_id = i.calibration_id 
WHERE i.hw_name = %s) X GROUP BY qubit_control, qubit_target) a ON q.qubit_control = a.qubit_control AND q.qubit_target = a.qubit_target
WHERE q.calibration_id = %s;
''', (calibration_date, hw_name, calibration_id, ))
    results = cursor.fetchall()
    count = len(results)
    if count > 0:
        f = open("./config/" + hw_name + "_mix_T.rlb", "w+")
        f.write("{}\n".format(count))
        for res in results:
            calibration_id, qubit_control, qubit_target, fidelity_2q = res

            if fidelity_2q <= 0:
                fidelity_2q = 0.001

            f.write("{} {} {} \n".format(qubit_control, qubit_target, fidelity_2q))
            

        f.close()

    conn.close()

#endregion