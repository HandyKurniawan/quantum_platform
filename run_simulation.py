from qEmQUIP import QEM, conf
from random import randint

token = "476ea8c61cc54f36e4a21d70a8442f94203c9d87096eaad0886a3e8154d8c2e79bcad6f927c6050a76335dd68d783f478c1b828504748a4377b441c335c831aa"

def update_hardware_configs(hw_name):
    conf.hardware_name = hw_name
    q = QEM(runs=conf.runs, user_id=conf.user_id, token=token, hw_name=hw_name)
    conf.hardware_name = hw_name
    conf.triq_measurement_type = "polar_meas"
    
    # update TriQ configs from calibration data
    q.update_hardware_configs(hw_name=hw_name)

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
                       prune_options: dict[str,bool|tuple[int|float]|int|str] = {"enable":False},
                        seed_simulator: int = 0 ):
    
    conf.hardware_name = hw_name
    conf.triq_measurement_type = triq_measurement_type
    conf.user_id=1
    q = QEM(runs=conf.runs, user_id=conf.user_id, token=token, hw_name=hw_name)
    conf.user_id=1
    conf.triq_measurement_type = triq_measurement_type
    conf.hardware_name = hw_name
    qasm_files = q.get_qasm_files_from_path(file_path)
    qasm_files = qasm_files*repeat
    print(qasm_files)
    
    mp_options = {"enable":False, "execution_type":"partition"}
    prune_options = {"enable":False, "type":"cal-avg", "params": (0.045,0.20)}

    q.set_backend(program_type="sampler", shots=shots)
    # q.run_simulator("sampler", qasm_files, compilations, noise_levels, shots, hardware_name=hw_name, send_to_db=True)

    q.run_simulator("sampler", qasm_files, compilations, noise_levels, shots, hardware_name=hw_name, send_to_db=True,
                mp_options=mp_options, prune_options=prune_options,
                seed_simulator=seed_simulator)

def run_simulation_all(hw_name):
    

    update_hardware_configs(hw_name=hw_name)
    

    noise_levels = [0.1, 0.2, 0.4, 0.6, 0.8, 1.0]
    seed_simulator = randint(1, 9999999)
    # noise_levels = [0.1, 0.8, 1.0]
    # noise_levels = [0.0]

    # # #region n2
    # # # Setup the object for n2_x
    # run_simulation_one(hw_name, noise_levels, file_path="./circuits/polar_sim/n2/x", 
    #                     compilations=["qiskit_3", "triq_lcd_sabre"], triq_measurement_type="polar_meas", 
    #                     repeat=2, shots=20000 )

    # # # Setup the object for n2_z
    # run_simulation_one(hw_name, noise_levels, file_path="./circuits/polar_sim/n2/z", 
    #                    compilations=["triq_lcd_sabre"], triq_measurement_type="polar_mix", 
    #                    repeat=2, shots=20000 )
    
    # # Setup the object for n2_z_qiskit
    # run_simulation_one(hw_name, noise_levels, file_path="./circuits/polar_sim/n2/z_qiskit", 
    #                    compilations=["qiskit_3"], triq_measurement_type="polar_meas", 
    #                    repeat=2, shots=20000 )

    # # # # #end region n2

    # # # #region n3
    # # Setup the object for n3_x
    run_simulation_one(hw_name, noise_levels, file_path="./circuits/polar_sim/n3/x", 
                        compilations=["qiskit_3","triq_lcd_sabre","triq_avg_sabre"], triq_measurement_type="polar_meas", 
                        repeat=1, shots=1000, seed_simulator=seed_simulator )

    # # Setup the object for n3_z
    # run_simulation_one(hw_name, noise_levels, file_path="./circuits/polar_sim/n3/z", 
    #                    compilations=["triq_lcd_sabre"], triq_measurement_type="polar_mix", 
    #                    repeat=3, shots=3000 )
    
    # # Setup the object for n3_z_qiskit
    # run_simulation_one(hw_name, noise_levels, file_path="./circuits/polar_sim/n3/z_qiskit", 
    #                    compilations=["qiskit_3"], triq_measurement_type="polar_meas", 
    #                    repeat=3, shots=3000 )

    # #endregion n3

    # #region n4

    # # # Setup the object for n4
    # run_simulation_one(hw_name, noise_levels, file_path="./circuits/polar_sim/n4/z", 
    #                   compilations=["qiskit_3", "triq_lcd_sabre"], triq_measurement_type="polar_meas", 
    #                   repeat=3, shots=10 )
    
    # run_simulation_one(hw_name, noise_levels, file_path="./circuits/polar_sim/n4/x", 
    #                   compilations=["qiskit_3", "triq_lcd_sabre"], triq_measurement_type="polar_meas", 
    #                   repeat=3, shots=10 )

    # #endregion n4

    # #region n5
    # # # Setup the object for n5
    # run_simulation_one(hw_name, noise_levels, file_path="./circuits/polar_sim/n5", 
    #                   compilations=["qiskit_3", "triq_lcd_sabre"], triq_measurement_type="polar_meas", 
    #                   repeat=1, shots=10 )
    # #endregion n5

    # #region n6
    # # # Setup the object for n6
    # run_simulation_one(hw_name, noise_levels, file_path="./circuits/polar_sim/n6", 
    #                   compilations=["qiskit_3", "triq_lcd_sabre"], triq_measurement_type="polar_meas", 
    #                   repeat=1, shots=10 )
    # #endregion n6

    q = QEM(runs=conf.runs, user_id=conf.user_id, token=token)

    
    print("Get Result...")
    q.get_qiskit_result("simulator")

try:
    # run_simulation_all("ibm_brisbane")
    run_simulation_all("ibm_sherbrooke")
    # run_simulation_all("ibm_sherbrooke")
    # run_simulation_all("ibm_sherbrooke")
    # run_simulation_all("ibm_sherbrooke")
    pass

except Exception as e:
    print(f"An error occurred: {str(e)}. Will try again in 30 seconds...")

try:
    #run_simulation_all("ibm_brisbane")
    #run_simulation_all("ibm_sherbrooke")
    pass

except Exception as e:
    print(f"An error occurred: {str(e)}. Will try again in 30 seconds...")


# q = QEM(runs=conf.runs, user_id=conf.user_id, token=token)

# print("Get Result...")
# q.get_qiskit_result("simulator")

# q.get_qiskit_result("real")