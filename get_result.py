from qEmQUIP import QEM, conf
import os
import sys

module_path = os.path.abspath(os.path.join('.', 'wrappers'))
if module_path not in sys.path:
    sys.path.append(module_path)

token = "971b2597e1f28e10a7c8992657e9ecc984a65bd4a22bacc497eda4d2945bf8e501b454b9e5d2527833808ab8ec62fc5fa0df3af38dccc02b85bd83c93f2e2e31"


q = QEM(runs=conf.runs, user_id=conf.user_id, token=token)

print("Get Result Simulator...")
q.get_qiskit_result("simulator")

print("Get Result...")
q.get_qiskit_result("real")