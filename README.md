# Quantum Compilations Platform
A platform for experimenting with and applying various quantum compilation techniques across multiple quantum computing backends.

## Table of contents

- [Setup](#setup)
- [Compilation Techniques](#compilation-techniques)
  - [Initial Mapping](#initial-mapping)
  - [Routing](#routing)
- [Simulators](#simulators)
- [Tutorial](#tutorial)
- [Acknowledgments](#acknowledgments)

## Setup

### Installation

First, we need to install the necessary library

``` terminal
sudo apt-get update
sudo apt-get install libmuparser2v5
```

Then, we need to create a Python environment to have a clean installation

``` terminal
python3 -m venv .venv
. .venv/bin/activate
```

Then activate it

``` terminal
. .venv/bin/activate
```
Last, install the required libraries:

``` terminal
pip install -r requirements.txt
```
Now, it is ready to go! 

### Example in Python

```python
from qEmQUIP import QEM, conf
q = QEM(runs=conf.runs, fixed_initial_layout = False, run_in_simulator=conf.run_in_simulator, user_id=conf.user_id, token=token)
qasm_text = """OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0];
cx q[0], q[1];
barrier q[0], q[1];
measure q[0] -> c[0];
measure q[1] -> c[1];
"""
qc = q.get_circuit_properties(qasm_source=qasm_text)
updated_qasm = q.compile(qasm=qc.qasm_original, compilation_name="triq_avg_na")
```

**Results**
```text
OPENQASM 2.0;
include "qelib1.inc";
qreg q[127];
creg c[127];
u2(0,3.14159265358979) q[104];
cx q[104],q[103];
measure q[104] -> c[0];
measure q[103] -> c[1];
```

## Compilation Techniques

We integrated several compilation techniques that differ in the awareness of the error information from the calibration data. As you can see from the image below:

![compilations](https://github.com/HandyKurniawan/quantum_platform/blob/main/img/compilations.png)

### Initial Mapping 

- **Noise-adaptive (NA)**: noise-aware initial mapping based on reliability matrix. More information [here](https://arxiv.org/pdf/1901.11054) 
- **Mapomatic (Mapo)**: noise-aware initial mapping as a subgraph isomorphism problem based on the lowest error rate. More information [here](https://arxiv.org/pdf/2209.15512)
- **SABRE**: non-noise-aware initial mapping. More information [here](https://arxiv.org/pdf/1809.02573.pdf)


### Routing

- **TriQ**: noise-aware routing uses a reliability matrix that stores the cost of performing a CNOT gate between any qubit pair. The following routing alternatives build this matrix differently. More information [here](https://doi.org/10.1145/3307650.3322273).
- **[SabreSwap]((https://qiskit.org/documentation/stubs/qiskit.transpiler.passes.SabreSwap.html)):** Divide the circuit into layers (resolved, front and extended) and inset swap gates considering previous gates (to increase parallelization) and future gates (extended layer) (to reduce circuit depth). More information [here](https://arxiv.org/pdf/1809.02573.pdf).

## Simulators

We included the noisy simulator embedded with noise coming from the real IBM's backends
- IBM Brisbane
- IBM Sherbrooke

We also provided scaled noise from 0 (noiseless) to 1 (real backend) in the simulator.

## Tutorial

See this jupyter notebook file for more in-depth examples: [here](https://github.com/HandyKurniawan/quantum_platform/blob/main/tutorial.ipynb)

## Acknowledgments

This work is supported by the QuantERA grant EQUIP with the grant numbers PCI2022-133004 and PCI2022-132922, funded by Agencia Estatal de Investigación, Ministerio de Ciencia e Innovación, Gobierno de España, MCIN/AEI/10.13039/501100011033, and by the European Union “NextGenerationEU/PRTR”.



