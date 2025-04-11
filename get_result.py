from qEmQUIP import QEM, conf
import os
import sys

module_path = os.path.abspath(os.path.join('.', 'wrappers'))
if module_path not in sys.path:
    sys.path.append(module_path)

token = "476ea8c61cc54f36e4a21d70a8442f94203c9d87096eaad0886a3e8154d8c2e79bcad6f927c6050a76335dd68d783f478c1b828504748a4377b441c335c831aa"


q = QEM(runs=conf.runs, user_id=conf.user_id, token=token)

print("Get Result Simulator...")
q.get_qiskit_result("simulator")

print("Get Result...")
q.get_qiskit_result("real")