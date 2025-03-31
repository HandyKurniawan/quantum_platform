from qiskit import QuantumCircuit, ClassicalRegister
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit.transpiler import CouplingMap
from qiskit.circuit import Clbit
from qiskit.circuit.library import RZZGate, RZGate, XGate, IGate
from qiskit.converters import circuit_to_dag, dag_to_circuit
from qiskit_ibm_runtime import IBMBackend

from pathlib import Path

from commons import used_qubits, neighbours, CNOT_used, neighbours_CNOT_used
# from qiskit_wrapper import get_initial_layout_from_circuit

def avoid_simultaneous_cnot(tqc, backend, type="ctrl"):
    dag = circuit_to_dag(tqc)
    layers = dag.layers()
    new_dag = dag.copy_empty_like()
    cm = backend.configuration().coupling_map
    used_qubit_prev_layer = []

    list_neighbours_qubits={}
    for i in range(127):
        list_neighbours_qubits[i] = neighbours(i,cm)

    
    for lay in layers:
        g = lay["graph"]

        tmp_circ = dag_to_circuit(g)
        cx_q = CNOT_used(tmp_circ, cm)

        list_neighbours_CNOT={}
        for qb_ctrl,qb_trgt in cx_q:
            list_neighbours_CNOT[qb_ctrl,qb_trgt]=neighbours_CNOT_used(qb_ctrl,qb_trgt,tmp_circ,cm)

        dict_neighbour_cx = {}
        unique_data = {}
        
        if len(g.collect_2q_runs()) > 0:
           
            for i in g.collect_2q_runs():
                op = i[0]
                op_name = op.op.name
                qb_ctrl = op.qargs[0]
                qb_trgt = op.qargs[1]
            
                if op_name == "ecr":
                    for qb_pairs, qb_nghrs in list_neighbours_CNOT.items():
                        if qb_ctrl._index in qb_nghrs: 
                            if qb_pairs[0] in list_neighbours_qubits[qb_ctrl._index]:
                                dict_neighbour_cx[qb_ctrl] = dag.qubits[qb_pairs[0]]
                            elif qb_pairs[1] in list_neighbours_qubits[qb_ctrl._index]:
                                dict_neighbour_cx[qb_ctrl] = dag.qubits[qb_pairs[1]]
                        
                        elif qb_trgt._index in qb_nghrs:
                            if qb_pairs[0] in list_neighbours_qubits[qb_trgt._index]:
                                dict_neighbour_cx[qb_trgt] = dag.qubits[qb_pairs[0]]
                            elif qb_pairs[1] in list_neighbours_qubits[qb_trgt._index]:
                                dict_neighbour_cx[qb_trgt] = dag.qubits[qb_pairs[1]]

        for key, value in dict_neighbour_cx.items():
            if key not in unique_data.values() and key not in unique_data.keys():
                unique_data[value] = key  # This ensures only the last key with the same value is kept

        
        
        # print(unique_data)
        for dn in g.topological_op_nodes():
            if dn.name == "ecr":
                
                qb_ctrl = dn.qargs[0]
                qb_trgt = dn.qargs[1]

        
                if qb_ctrl in unique_data.keys() or qb_trgt in unique_data.keys():
                    if qb_ctrl._index in used_qubit_prev_layer:
                        # new_dag.apply_operation_back(XGate(), [qb_ctrl])
                        # new_dag.apply_operation_back(XGate(), [qb_ctrl])
                        new_dag.apply_operation_back(IGate(), [qb_ctrl])
                    elif qb_trgt._index in used_qubit_prev_layer:
                        # new_dag.apply_operation_back(XGate(), [qb_trgt])
                        # new_dag.apply_operation_back(XGate(), [qb_trgt])
                        new_dag.apply_operation_back(IGate(), [qb_trgt])
                        
        
            new_dag.apply_operation_back(dn.op, dn.qargs, dn.cargs)

        tmp_circ = dag_to_circuit(g)
        used_qubit_prev_layer = used_qubits(tmp_circ)
        
    new_qc = dag_to_circuit(new_dag)
    
    return new_qc


def add_zz_on_simultaneous_cnot(tqc, backend):
    dag = circuit_to_dag(tqc)
    layers = dag.layers()
    new_dag = dag.copy_empty_like()
    cm = backend.configuration().coupling_map

    list_neighbours_qubits={}
    for i in range(127):
        list_neighbours_qubits[i] = neighbours(i,cm)
    
    for lay in layers:
        g = lay["graph"]
    
        # put back all the operations in the nodes
        for dn in g.topological_op_nodes():
            new_dag.apply_operation_back(dn.op, dn.qargs, dn.cargs)

        tmp_circ = dag_to_circuit(g)
        cx_q = CNOT_used(tmp_circ, cm)

        list_neighbours_CNOT={}
        for qb_ctrl,qb_trgt in cx_q:
            list_neighbours_CNOT[qb_ctrl,qb_trgt]=neighbours_CNOT_used(qb_ctrl,qb_trgt,tmp_circ,cm)
    
        if len(g.collect_2q_runs()) > 0:
           
            dict_neighbour_cx = {}
            
            for i in g.collect_2q_runs():
                op = i[0]
                op_name = op.op.name
                qb_ctrl = op.qargs[0]
                qb_trgt = op.qargs[1]
            
                if op_name == "ecr":
                    for qb_pairs, qb_nghrs in list_neighbours_CNOT.items():
                        if qb_ctrl._index in qb_nghrs: 
                            if qb_pairs[0] in list_neighbours_qubits[qb_ctrl._index]:
                                dict_neighbour_cx[qb_ctrl] = dag.qubits[qb_pairs[0]]
                            elif qb_pairs[1] in list_neighbours_qubits[qb_ctrl._index]:
                                dict_neighbour_cx[qb_ctrl] = dag.qubits[qb_pairs[1]]
                        
                        elif qb_trgt._index in qb_nghrs:
                            if qb_pairs[0] in list_neighbours_qubits[qb_trgt._index]:
                                dict_neighbour_cx[qb_trgt] = dag.qubits[qb_pairs[0]]
                            elif qb_pairs[1] in list_neighbours_qubits[qb_trgt._index]:
                                dict_neighbour_cx[qb_trgt] = dag.qubits[qb_pairs[1]]
            
            unique_data = {}
            for key, value in dict_neighbour_cx.items():
                if key not in unique_data.values() and key not in unique_data.keys():
                    unique_data[value] = key  # This ensures only the last key with the same value is kept
            
            # print(unique_data)
            
            for key, value in unique_data.items():
                # print(key,value)
                new_dag.apply_operation_back(RZZGate(100 * 1), [key, value])
        
        
    new_qc = dag_to_circuit(new_dag)
    
    return new_qc
    
def build_idle_coupling_map(cm: CouplingMap, used_qubit: list
)->CouplingMap:
    qubit_idle = []
    for source, target in cm:
        if source not in used_qubit and target not in used_qubit:
            qubit_idle.append((source,target))
        
    return CouplingMap(qubit_idle)

def build_active_coupling_map(cm, selected_qubit):
    qubit_active = []
    for source, target in cm:
        if source in selected_qubit and target in selected_qubit:
            qubit_active.append((source,target))
        
    return CouplingMap(qubit_active)
    
def multiprogram_compilation_qiskit(circuits, backend, opt_level=3, exclude_qubits=[], presets_cm=[]): 
    pass
    # cm = backend.coupling_map
    # prevously_used_qubits = []
    # used_qubit = []
    # compiled_circuits = []

    # # if there is a list in exclude_qubits
    # if len(exclude_qubits) > 0:
    #     for q in exclude_qubits:
    #         prevously_used_qubits.append(q)
    #         used_qubit.append(q)
        
    #     cm = build_idle_coupling_map(cm, used_qubit)
    
    # total_qubits = 0
    # for qc in circuits:
    #     total_qubits = total_qubits + len(used_qubits(qc))
    
    # # max_reps = np.floor(backend.num_qubits / len(qc.qubits))

    # if total_qubits > backend.num_qubits - len(exclude_qubits):
    #     raise ValueError(f'Total number of qubits ({total_qubits}) could not be higher than the maximum qubits ({backend.num_qubits})')

    # # for i in range(reps):
    # if len(presets_cm) == 0:
    #     for qc in circuits:
    #         pm = generate_preset_pass_manager(
    #             optimization_level=opt_level, backend=backend, coupling_map=cm
    #         )
    
    #         tqc = pm.run(qc)
    
    #         used_qubit = used_qubits(tqc)
    #         for q in used_qubit:
    #             prevously_used_qubits.append(q)
    
    #         compiled_circuits.append({"circuit":tqc, "initial_layout":get_initial_layout_from_circuit(tqc)})
    #         # compiled_circuits.append({"circuit":tqc, "initial_layout":tqc.layout.initial_layout})
            
    #         cm = build_idle_coupling_map(cm, used_qubit)
    # else:
    #     for idx, qc in enumerate(circuits):
    #         cm = presets_cm[idx]
            
    #         pm = generate_preset_pass_manager(
    #             optimization_level=opt_level, backend=backend, coupling_map=cm
    #         )
    
    #         tqc = pm.run(qc)
    
    #         used_qubit = used_qubits(tqc)
    #         for q in used_qubit:
    #             prevously_used_qubits.append(q)
    
    #         compiled_circuits.append({"circuit":tqc, "initial_layout":get_initial_layout_from_circuit(tqc)})
    #         # compiled_circuits.append({"circuit":tqc, "initial_layout":tqc.layout.initial_layout})
            
    # return compiled_circuits
    
def merge_circuits(compiled_circuits:dict[str, list[dict[QuantumCircuit, list[int]]]], 
                   backend: IBMBackend, 
                   num_cbits: int = 0):
    try:
        num_qbits = backend.num_qubits

        if num_cbits == 0:
            num_cbits = num_qbits
        
        final_circuit = QuantumCircuit(num_qbits, num_cbits)
        creg = ClassicalRegister(num_cbits, 'c')
        dag = circuit_to_dag(final_circuit)
        
        new_dag = dag.copy_empty_like()
        m_idx = 0
        for i in compiled_circuits: 
            
            dag = circuit_to_dag(i["circuit"])
            
            for dn in dag.topological_op_nodes():
                if dn.name == "barrier":
                    continue
                    
                if len(dn.cargs) >0 :

                    if dn.name == "measure":
                        # print(dn.cargs, dn.op, dn.qargs, dn.name)
                        
                        upd_cargs = [Clbit(creg, m_idx),]
                        m_idx = m_idx + 1
            
                        new_dag.apply_operation_back(dn.op, dn.qargs, upd_cargs)            
                    elif dn.name == "if_else":
                        # # print(dn.cargs, dn.op, dn.qargs, dn.name)
                        # new_dag.apply_operation_back(dn.op, dn.qargs, dn.cargs, dn.params)    
                        # # print(dn.params)
                        pass
                else:
                    new_dag.apply_operation_back(dn.op, dn.qargs, dn.cargs)

        final_circuit = dag_to_circuit(new_dag)
    except Exception as e:
            print(f"An error occurred in merge_circuits: {str(e)}.")
            raise ValueError(f'merge_circuits: {str(e)}')

    return final_circuit

def build_active_coupling_map(cm, selected_qubit):
    qubit_active = []
    for source, target in cm:
        if source in selected_qubit and target in selected_qubit:
            qubit_active.append((source,target))
        
    return CouplingMap(qubit_active)

def divide_list_by_number(lst, num):
    result = []
    total = int(len(lst)//num)

    start_index = 0
    end_index = 0
    for i in range(total):

        end_index = start_index + num
        
        result.append(lst[start_index:end_index])

        start_index = end_index

    return result

def get_LF_presets_cm(backend, LF_qubits, num_partition):
    cm = backend.coupling_map
    presets_cm = []
    selected_qubits = divide_list_by_number(LF_qubits,num_partition)

    for i in selected_qubits:
        presets_cm.append(build_active_coupling_map(cm, i))

    return presets_cm
