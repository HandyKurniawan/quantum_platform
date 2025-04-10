from qiskit.transpiler.passes import ALAPScheduleAnalysis, ASAPScheduleAnalysis, PadDynamicalDecoupling, PadDelay
from qiskit.transpiler import PassManager
from commons import used_qubits


def convert_dt_to_us(backend, time_dt):
    dt_us = backend.dt * 1e6  # Convert to microseconds
    return round(dt_us * time_dt, 3)

def count_delay_durations(qc):
    total_delay_dt = {}

    used_qbs = used_qubits(qc)
    
    for qb in used_qbs:    
        total_delay_dt[qb] = 0

    for gate in qc:
        if gate.name == "delay":
            qb = gate.qubits[0]._index 
            if qb in used_qbs:
                # print(gate.qubits[0]._index)
                total_delay_dt[qb] = total_delay_dt[qb] + gate.duration

    return total_delay_dt

def apply_pad_delay(qc, backend):
    target = backend.target
    
    delay_pm = PassManager(
        [
            ALAPScheduleAnalysis(target=target),
            PadDelay(target=target),
        ]
        )

    return delay_pm.run(qc)

def get_delay_information(qc, backend):
    qc_delay = apply_pad_delay(qc, backend)
    total_delay_dt = count_delay_durations(qc_delay)

    return qc_delay, total_delay_dt

def get_dd_information(qc, backend, seq_type):
    from wrappers.qiskit_wrapper import apply_dd
    
    qc_dd = apply_dd(qc, backend, sequence_type=seq_type)
    total_dd_delay_dt = count_delay_durations(qc_dd)

    return qc_dd, total_dd_delay_dt

def get_delay_and_dd_information_us(qc, backend, seq_type):
    qc_delay, total_qc_delay_dt = get_delay_information(qc, backend)
    qc_dd, total_qc_dd_dt = get_dd_information(qc, backend, seq_type)

    total_qc_delay_us = {key : convert_dt_to_us(backend, total_qc_delay_dt[key]) for key in total_qc_delay_dt}
    total_qc_dd_us = {key : convert_dt_to_us(backend, total_qc_dd_dt[key]) for key in total_qc_dd_dt}
    
    return (qc_delay, qc_dd), (total_qc_delay_us, total_qc_dd_us)