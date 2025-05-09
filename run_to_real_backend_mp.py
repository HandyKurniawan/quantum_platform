import wrappers.qiskit_wrapper as qiskit_wrapper

from qEmQUIP import QEM, conf

# token = "476ea8c61cc54f36e4a21d70a8442f94203c9d87096eaad0886a3e8154d8c2e79bcad6f927c6050a76335dd68d783f478c1b828504748a4377b441c335c831aa"

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
    conf.user_id=3
    q = QEM(runs=conf.runs, user_id=conf.user_id, token=token, hw_name=hw_name)
    conf.user_id=3
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
    

    # update_hardware_configs(hw_name=hw_name)
    

    noise_levels = [0.1, 0.2, 0.4, 0.6, 0.8, 1.0]

    # # #region n2
    # # Setup the object for n2_x
    # run_simulation_one(hw_name, noise_levels, file_path="./circuits/polar_sim/n2/x", 
    #                    compilations=["qiskit_3"], triq_measurement_type="polar_meas", 
    #                    repeat=1, shots=4000 )

    # # Setup the object for n2_z
    # run_simulation_one(hw_name, noise_levels, file_path="./circuits/polar_sim/n2/z", 
    #                    compilations=["triq_lcd_sabre", "triq_avg_sabre"], triq_measurement_type="polar_mix", 
    #                    repeat=1, shots=4000 )
    
    # # Setup the object for n2_z_qiskit
    # run_simulation_one(hw_name, noise_levels, file_path="./circuits/polar_sim/n2/z_qiskit", 
    #                    compilations=["qiskit_3"], triq_measurement_type="polar_meas", 
    #                    repeat=1, shots=4000 )

    #end region n2

    # #region n3
    # Setup the object for n3_x
    file_path = "./circuits/polar_sim/n3/x"

    # normal
    # mp_options = {"enable":True, "execution_type":"final"}
    # run_simulation_one(hw_name, noise_levels, file_path=file_path, 
    #                    compilations=["qiskit_3"], triq_measurement_type="polar_meas", 
    #                    repeat=10, shots=shots,
    #                    mp_options=mp_options  )
    
    # # prune-lcd
    # mp_options = {"enable":True, "execution_type":"final"}
    # prune_options = {"enable":True, "type":"cal-lcd", "params": (0.045,0.20)}

    # run_simulation_one(hw_name, noise_levels, file_path=file_path, 
    #                    compilations=["qiskit_3"], triq_measurement_type="polar_meas", 
    #                    repeat=9, shots=shots,
    #                    mp_options=mp_options, prune_options=prune_options  )

    # # prune-avg
    # mp_options = {"enable":True, "execution_type":"final"}
    # prune_options = {"enable":True, "type":"cal-avg", "params": (0.045,0.20)}

    # run_simulation_one(hw_name, noise_levels, file_path=file_path, 
    #                    compilations=["qiskit_3"], triq_measurement_type="polar_meas", 
    #                    repeat=9, shots=shots,
    #                    mp_options=mp_options, prune_options=prune_options  )

    # # prune-lf
    # mp_options = {"enable":True, "execution_type":"final"}
    # prune_options = {"enable":True, "type":"lf", "params": 100}

    # run_simulation_one(hw_name, noise_levels, file_path=file_path, 
    #                    compilations=["qiskit_3"], triq_measurement_type="polar_meas", 
    #                    repeat=8, shots=shots,
    #                    mp_options=mp_options, prune_options=prune_options  )

    
    # # # Setup the object for n3_z_qiskit
    file_path = "./circuits/polar_sim/n3/z_qiskit"

    # run_simulation_one(hw_name, noise_levels, file_path="./circuits/polar_sim/n3/z_qiskit", 
    #                    compilations=["qiskit_3"], triq_measurement_type="polar_meas", 
    #                    repeat=1, shots=shots )
    
    # normal
    mp_options = {"enable":True, "execution_type":"final"}
    run_simulation_one(hw_name, noise_levels, file_path=file_path, 
                       compilations=["qiskit_3"], triq_measurement_type="polar_meas", 
                       repeat=10, shots=shots,
                       mp_options=mp_options  )
    
    # prune-lcd
    mp_options = {"enable":True, "execution_type":"final"}
    prune_options = {"enable":True, "type":"cal-lcd", "params": (0.045,0.20)}

    run_simulation_one(hw_name, noise_levels, file_path=file_path, 
                       compilations=["qiskit_3"], triq_measurement_type="polar_meas", 
                       repeat=9, shots=shots,
                       mp_options=mp_options, prune_options=prune_options  )

    # prune-avg
    mp_options = {"enable":True, "execution_type":"final"}
    prune_options = {"enable":True, "type":"cal-avg", "params": (0.045,0.20)}

    run_simulation_one(hw_name, noise_levels, file_path=file_path, 
                       compilations=["qiskit_3"], triq_measurement_type="polar_meas", 
                       repeat=9, shots=shots,
                       mp_options=mp_options, prune_options=prune_options  )

    # prune-lf
    mp_options = {"enable":True, "execution_type":"final"}
    prune_options = {"enable":True, "type":"lf", "params": 100}

    run_simulation_one(hw_name, noise_levels, file_path=file_path, 
                       compilations=["qiskit_3"], triq_measurement_type="polar_meas", 
                       repeat=8, shots=shots,
                       mp_options=mp_options, prune_options=prune_options  )

    # #endregion n3

    # # #region n4

    file_path = "./circuits/polar_sim/n4/x"
    # # Setup the object for n4
    # run_simulation_one(hw_name, noise_levels, file_path="./circuits/polar_sim/n4/x", 
    #                    compilations=["qiskit_3"], triq_measurement_type="polar_meas", 
    #                    repeat=1, shots=shots )

    # # normal
    # mp_options = {"enable":True, "execution_type":"final"}
    # run_simulation_one(hw_name, noise_levels, file_path=file_path, 
    #                    compilations=["qiskit_3"], triq_measurement_type="polar_meas", 
    #                    repeat=5, shots=shots,
    #                    mp_options=mp_options  )
    
    # # prune-lcd
    # mp_options = {"enable":True, "execution_type":"final"}
    # prune_options = {"enable":True, "type":"cal-lcd", "params": threshold_lcd}
    # run_simulation_one(hw_name, noise_levels, file_path=file_path, 
    #                    compilations=["qiskit_3"], triq_measurement_type="polar_meas", 
    #                    repeat=3, shots=shots,
    #                    mp_options=mp_options, prune_options=prune_options  )

    # # prune-avg
    # mp_options = {"enable":True, "execution_type":"final"}
    # prune_options = {"enable":True, "type":"cal-avg", "params": threshold_avg}
    # run_simulation_one(hw_name, noise_levels, file_path=file_path, 
    #                    compilations=["qiskit_3"], triq_measurement_type="polar_meas", 
    #                    repeat=3, shots=shots,
    #                    mp_options=mp_options, prune_options=prune_options  )

    # # prune-lf
    # mp_options = {"enable":True, "execution_type":"final"}
    # prune_options = {"enable":True, "type":"lf", "params": 100}
    # run_simulation_one(hw_name, noise_levels, file_path=file_path, 
    #                    compilations=["qiskit_3"], triq_measurement_type="polar_meas", 
    #                    repeat=3, shots=shots,
    #                    mp_options=mp_options, prune_options=prune_options  )
    

    file_path = "./circuits/polar_sim/n4/z"
    # run_simulation_one(hw_name, noise_levels, file_path="./circuits/polar_sim/n4/z", 
    #                    compilations=["qiskit_3"], triq_measurement_type="polar_meas", 
    #                    repeat=1, shots=shots )

    # normal
    # mp_options = {"enable":True, "execution_type":"final"}
    # run_simulation_one(hw_name, noise_levels, file_path=file_path, 
    #                    compilations=["qiskit_3"], triq_measurement_type="polar_meas", 
    #                    repeat=5, shots=shots,
    #                    mp_options=mp_options  )
    
    # # prune-lcd
    # mp_options = {"enable":True, "execution_type":"final"}
    # prune_options = {"enable":True, "type":"cal-lcd", "params": (0.045,0.20)}
    # run_simulation_one(hw_name, noise_levels, file_path=file_path, 
    #                    compilations=["qiskit_3"], triq_measurement_type="polar_meas", 
    #                    repeat=3, shots=shots,
    #                    mp_options=mp_options, prune_options=prune_options  )

    # # prune-avg
    # mp_options = {"enable":True, "execution_type":"final"}
    # prune_options = {"enable":True, "type":"cal-avg", "params": (0.045,0.20)}
    # run_simulation_one(hw_name, noise_levels, file_path=file_path, 
    #                    compilations=["qiskit_3"], triq_measurement_type="polar_meas", 
    #                    repeat=3, shots=shots,
    #                    mp_options=mp_options, prune_options=prune_options  )

    # # prune-lf
    # mp_options = {"enable":True, "execution_type":"final"}
    # prune_options = {"enable":True, "type":"lf", "params": 100}
    # run_simulation_one(hw_name, noise_levels, file_path=file_path, 
    #                    compilations=["qiskit_3"], triq_measurement_type="polar_meas", 
    #                    repeat=3, shots=shots,
    #                    mp_options=mp_options, prune_options=prune_options  )
    

    # # #endregion n4

    # print("Get Result...")
    # q.get_qiskit_result()

    

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
        try:
            run_simulation_all("ibm_fez", 4000, (0.025, 0.05), (0.01, 0.05))
            pass

        except Exception as e:
            print(f"An error occurred: {str(e)}.")

        try:
            run_simulation_all("ibm_torino", 4000, (0.025, 0.05), (0.01, 0.05))
            pass

        except Exception as e:
            print(f"An error occurred: {str(e)}.")

        try:
            run_simulation_all("ibm_marrakesh", 4000, (0.025, 0.05), (0.01, 0.05))
            pass

        except Exception as e:
            print(f"An error occurred: {str(e)}.")



# token = qiskit_wrapper.get_active_token(100, 0, 1)[0][0]
# print(token)
# q = QEM(runs=conf.runs, user_id=conf.user_id, token=token)

# print("Get Result...")
# q.get_qiskit_result("real")