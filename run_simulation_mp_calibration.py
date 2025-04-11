import wrappers.qiskit_wrapper as qiskit_wrapper
from qEmQUIP import QEM, conf
from random import randint

token = "476ea8c61cc54f36e4a21d70a8442f94203c9d87096eaad0886a3e8154d8c2e79bcad6f927c6050a76335dd68d783f478c1b828504748a4377b441c335c831aa"

def run_simulation_one(hw_name:str, 
                       noise_levels: list[float], 
                       file_path: str, 
                       compilations: list[str], 
                       triq_measurement_type: str, 
                       repeat: int,
                       shots: int,
                       mp_options: dict[str,bool|str] = {"enable":False},
                       prune_options: dict[str,bool|tuple[int|float]|int|str] = {"enable":False},
                       seed_simulator: int = 0):
    # token = qiskit_wrapper.get_active_token(remaining=100, repetition=0, token_number=1)[0][0]
    # print(token)

    token = "476ea8c61cc54f36e4a21d70a8442f94203c9d87096eaad0886a3e8154d8c2e79bcad6f927c6050a76335dd68d783f478c1b828504748a4377b441c335c831aa"
    conf.hardware_name = hw_name
    conf.triq_measurement_type = triq_measurement_type
    conf.user_id=2
    q = QEM(runs=conf.runs, user_id=conf.user_id, token=token, hw_name=hw_name)
    conf.user_id=2
    conf.triq_measurement_type = triq_measurement_type
    conf.hardware_name = hw_name
    qasm_files = q.get_qasm_files_from_path(file_path)
    qasm_files = qasm_files*repeat
    # print(qasm_files)
    
    q.set_backend(program_type="sampler", shots=shots)
    
    # q.run_simulator("sampler", qasm_files, compilations, noise_levels, shots, hardware_name=hw_name, send_to_db=True)


    q.run_simulator("sampler", qasm_files, compilations, noise_levels, shots, hardware_name=hw_name, send_to_db=True,
                mp_options=mp_options, prune_options=prune_options,
                seed_simulator=seed_simulator)
    


    # qiskit_wrapper.update_qiskit_usage_info(token)



def run_simulation_all(hw_name: str, 
                        shots: int = 4000,
                       threshold_lcd = (0.045,0.20),
                       threshold_avg = (0.045,0.20)
                        ):
    

    # update_hardware_configs(hw_name=hw_name)
    

    # noise_levels = [0, 0.1, 0.2, 0.4, 0.6, 0.8, 1.0]
    noise_levels = [0, 1.0]
    seed_simulator = randint(1, 9999999)

    #region CalibrationPaper
    file_path = "./circuits/calibration"
    reps = 1
    execution_type = "partition"

    # # normal
    mp_options = {"enable":True, "execution_type":execution_type}
    run_simulation_one(hw_name, noise_levels, file_path=file_path, 
                       compilations=["qiskit_3"], triq_measurement_type="polar_meas", 
                       repeat=reps, shots=shots,
                       mp_options=mp_options, seed_simulator=seed_simulator  )
    
    # prune-lcd
    mp_options = {"enable":True, "execution_type":execution_type}
    prune_options = {"enable":True, "type":"cal-lcd", "params": threshold_lcd}

    run_simulation_one(hw_name, noise_levels, file_path=file_path, 
                       compilations=["qiskit_3"], triq_measurement_type="polar_meas", 
                       repeat=reps, shots=shots,
                       mp_options=mp_options, prune_options=prune_options, 
                       seed_simulator=seed_simulator  )

    # prune-avg
    mp_options = {"enable":True, "execution_type":execution_type}
    prune_options = {"enable":True, "type":"cal-avg", "params": threshold_avg}

    run_simulation_one(hw_name, noise_levels, file_path=file_path, 
                       compilations=["qiskit_3"], triq_measurement_type="polar_meas", 
                       repeat=reps, shots=shots,
                       mp_options=mp_options, prune_options=prune_options, 
                       seed_simulator=seed_simulator  )

    # prune-avg
    mp_options = {"enable":True, "execution_type":execution_type}
    prune_options = {"enable":True, "type":"lf", "params": 100}

    run_simulation_one(hw_name, noise_levels, file_path=file_path, 
                       compilations=["qiskit_3"], triq_measurement_type="polar_meas", 
                       repeat=reps, shots=shots,
                       mp_options=mp_options, prune_options=prune_options, 
                       seed_simulator=seed_simulator  )
    # #endregion CalibrationPaper

for i in range(10):

    if not conf.use_ibm_cloud:
        try:
            run_simulation_all("ibm_kyiv", 10000)
            pass

        except Exception as e:
            print(f"An error occurred: {str(e)}. ")

        try:
            run_simulation_all("ibm_sherbrooke", 10000)
            pass

        except Exception as e:
            print(f"An error occurred: {str(e)}. ")

        try:
            run_simulation_all("ibm_brisbane", 10000)
            pass

        except Exception as e:
            print(f"An error occurred: {str(e)}.")

    if conf.use_ibm_cloud:

        try:
            run_simulation_all("ibm_fez", 10000, (0.025, 0.05), (0.01, 0.05))
            pass

        except Exception as e:
            print(f"An error occurred: {str(e)}.")

        try:
            run_simulation_all("ibm_torino", 10000, (0.025, 0.05), (0.01, 0.05))
            pass

        except Exception as e:
            print(f"An error occurred: {str(e)}.")

        try:
            run_simulation_all("ibm_marrakesh", 10000, (0.025, 0.05), (0.01, 0.05))
            pass

        except Exception as e:
            print(f"An error occurred: {str(e)}.")


# token = qiskit_wrapper.get_active_token(100, 0, 1)[0][0]
# print(token)
q = QEM(runs=conf.runs, user_id=conf.user_id, token=token)

print("Get Result...")
q.get_qiskit_result("simulator")