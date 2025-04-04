import wrappers.qiskit_wrapper as qiskit_wrapper
from qEmQUIP import QEM, conf

# token = "476ea8c61cc54f36e4a21d70a8442f94203c9d87096eaad0886a3e8154d8c2e79bcad6f927c6050a76335dd68d783f478c1b828504748a4377b441c335c831aa"

def update_hardware_configs(hw_name):
    token = qiskit_wrapper.get_active_token(remaining=100, repetition=0, token_number=1)[0][0]
    print(token)

    conf.hardware_name = hw_name
    conf.user_id=2
    q = QEM(runs=conf.runs, user_id=conf.user_id, token=token, hw_name=hw_name)
    conf.user_id=2
    conf.hardware_name = hw_name
    conf.triq_measurement_type = "polar_meas"
    
    # # update TriQ configs from calibration data
    # q.update_hardware_configs(hw_name=hw_name)

    # # update IBM FakeBackend configuration
    # shots = 1000
    # q.set_backend(program_type="sampler", shots=shots)
    # qiskit_wrapper.generate_new_props(q.backend, "avg")
    # qiskit_wrapper.generate_new_props(q.backend, "mix")
    # qiskit_wrapper.generate_new_props(q.backend, "recent_15_adjust")

def run_simulation_one(hw_name:str, 
                       noise_levels: list[float], 
                       file_path: str, 
                       compilations: list[str], 
                       triq_measurement_type: str, 
                       repeat: int,
                       shots: int,
                       mp_options: dict[str,bool|str] = {"enable":False},
                       prune_options: dict[str,bool|tuple[int|float]|int|str] = {"enable":False} ):
    token = qiskit_wrapper.get_active_token(remaining=100, repetition=0, token_number=1)[0][0]
    print(token)

    conf.hardware_name = hw_name
    conf.triq_measurement_type = triq_measurement_type
    conf.user_id=4
    q = QEM(runs=conf.runs, user_id=conf.user_id, token=token, hw_name=hw_name)
    conf.user_id=4
    conf.triq_measurement_type = triq_measurement_type
    conf.hardware_name = hw_name
    qasm_files = q.get_qasm_files_from_path(file_path)
    qasm_files = qasm_files*repeat
    print(qasm_files)
    
    q.set_backend(program_type="sampler", shots=shots)
    # q.run_simulator("sampler", qasm_files, compilations, noise_levels, shots, hardware_name=hw_name, send_to_db=True)
    
#     dd_options: DynamicalDecouplingOptions = {
#     'enable':True, 
# #    'sequence_type':'XpXm',
#     'sequence_type':'XY4',
#     'scheduling_method': 'alap'
# } 

    # q.send_to_real_backend("sampler", qasm_files, compilations, hardware_name=hw_name, shots=shots, dd_options = dd_options)

    q.send_to_real_backend("sampler", qasm_files, compilations, hardware_name=hw_name, shots=shots,
                       mp_options=mp_options,
                       prune_options=prune_options)

    qiskit_wrapper.update_qiskit_usage_info(token)



def run_simulation_all(hw_name:str, 
                       shots:int = 4000,
                       threshold_lcd = (0.045,0.20),
                       threshold_avg = (0.045,0.20)):
    
    

    noise_levels = [0.1, 0.2, 0.4, 0.6, 0.8, 1.0]

    #region CalibrationPaper
    file_path = "./circuits/calibration"
    reps = 1
    execution_type = "all"

    # # normal
    mp_options = {"enable":True, "execution_type":execution_type}
    run_simulation_one(hw_name, noise_levels, file_path=file_path, 
                       compilations=["qiskit_3"], triq_measurement_type="polar_meas", 
                       repeat=reps, shots=shots,
                       mp_options=mp_options)
    
    # prune-lcd
    mp_options = {"enable":True, "execution_type":execution_type}
    prune_options = {"enable":True, "type":"cal-lcd", "params": threshold_lcd}


    run_simulation_one(hw_name, noise_levels, file_path=file_path, 
                       compilations=["qiskit_3"], triq_measurement_type="polar_meas", 
                       repeat=reps, shots=shots,
                       mp_options=mp_options, prune_options=prune_options, 
                        )

    # prune-avg
    mp_options = {"enable":True, "execution_type":execution_type}
    prune_options = {"enable":True, "type":"cal-avg", "params": threshold_avg}

    run_simulation_one(hw_name, noise_levels, file_path=file_path, 
                       compilations=["qiskit_3"], triq_measurement_type="polar_meas", 
                       repeat=reps, shots=shots,
                       mp_options=mp_options, prune_options=prune_options, 
                        )

    # prune-lf
    mp_options = {"enable":True, "execution_type":execution_type}
    prune_options = {"enable":True, "type":"lf", "params": 100}

    run_simulation_one(hw_name, noise_levels, file_path=file_path, 
                       compilations=["qiskit_3"], triq_measurement_type="polar_meas", 
                       repeat=reps, shots=shots,
                       mp_options=mp_options, prune_options=prune_options, 
                       )
    #endregion CalibrationPaper

for i in range(1):

    if not conf.use_ibm_cloud:
        try:
            run_simulation_all("ibm_kyiv", 4000)
            pass

        except Exception as e:
            print(f"An error occurred: {str(e)}. ")

        try:
            run_simulation_all("ibm_sherbrooke", 4000)
            pass

        except Exception as e:
            print(f"An error occurred: {str(e)}. ")

        try:
            run_simulation_all("ibm_brisbane", 4000)
            pass

        except Exception as e:
            print(f"An error occurred: {str(e)}.")

    if conf.use_ibm_cloud:
        # try:
        #     run_simulation_all("ibm_fez", 4000, (0.025, 0.05), (0.01, 0.05))
        #     pass

        # except Exception as e:
        #     print(f"An error occurred: {str(e)}.")

        try:
            run_simulation_all("ibm_torino", 4000, (0.035, 0.08), (0.01, 0.05))
            pass

        except Exception as e:
            print(f"An error occurred: {str(e)}.")

        # try:
        #     run_simulation_all("ibm_marrakesh", 4000, (0.025, 0.05), (0.01, 0.05))
        #     pass

        # except Exception as e:
        #     print(f"An error occurred: {str(e)}.")

# token = qiskit_wrapper.get_active_token(100, 0, 1)[0][0]
# print(token)
# q = QEM(runs=conf.runs, user_id=conf.user_id, token=token)

# print("Get Result...")
# q.get_qiskit_result("real")