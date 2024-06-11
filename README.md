# Quantum Platform
A platform for experimenting with and applying various quantum compilation techniques across multiple quantum computing backends.

## Table of contents

- [Setup](#setup)
- [Optimization levels](#optimization-levels)
  - [Qiskit](#qiskit)
  - [TriQ](#triq)
  - [Mirage](#mirage)
- [Included optimizations](#included-optimizations)
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



## Optimization levels

### Qiskit (0.44.3)

| Level | Initial mapping| Routing                  | Optimizations                            | Error-aware            |
|--- |------------------ |------------------------- |----------------------------------------- |----------------------- |
| 0  | Trivial           | Stochastic               | None                                     | No                     |
| 1  | VF2 > Sabre       | Sabre (5 swap trials)    | Adjacent gate collapsing                 | Yes (VF2), No (Sabre)  |
| 2  | VF2 > Sabre       | Sabre (10 swap trials)   | Gate cancellation                        | Yes (VF2), No (Sabre)  |
| 3  | VF2 > Sabre       | Sabre (20 swap trials)   | Gate cancellation and unitary synthesis  | Yes (VF2), No (Sabre)  |

#### Initial mapping methods (layout)

First, Qiskit tries to find the perfect initial mapping (no need to add swaps):

- **[Trivial]((https://qiskit.org/documentation/stubs/qiskit.transpiler.passes.TrivialLayout.html)):** Map the *i-th* virtual qubit to the *i-th* physical qubit.
- **[VF2](https://qiskit.org/documentation/stubs/qiskit.transpiler.passes.VF2Layout.html):** Find a subgraph of the connectivity graph isomorphic to the circuit's qubit interaction graph.

If it cannot find the perfect initial mapping, it uses heuristic passes:

- **[Sabre]((https://qiskit.org/documentation/stubs/qiskit.transpiler.passes.SabreLayout.html)):** Use the Reverse Trasversal Technique several times to find a good initial mapping.
- **[Dense]((https://qiskit.org/documentation/stubs/qiskit.transpiler.passes.DenseLayout.html)):** Map the qubits to the most connected part of the chip and lower error rate (considering 2q and readout error rates).

#### Routing methods

- **[Stochastic]((https://qiskit.org/documentation/stubs/qiskit.transpiler.passes.StochasticSwap.html)):** Use a random algorithm to insert swap gates.
- **[SabreSwap]((https://qiskit.org/documentation/stubs/qiskit.transpiler.passes.SabreSwap.html)):** Divide the circuit into layers (resolved, front and extended) and inset swap gates consideing prevoius gates (to increase parallelization) and future gates (extended layer) (to reduce circuit depth). More information [here](https://arxiv.org/pdf/1809.02573.pdf).

### TriQ

TriQ uses a reliability matrix that stores the cost of performing a CNOT gate between any qubit pair. The following routing alternatives build this matrix in a different way. More information [here](https://doi.org/10.1145/3307650.3322273).

| Level  | Initial mapping                    | Routing                                         | Error aware                        |
|------- |----------------------------------- |------------------------------------------------ |----------------------------------- |
| 0      | Map communicating qubits together  |                                                 | Yes (initial mapping)              |
| 1      | Map communicating qubits together  | Insert swap gates with the lowest hop count     | Yes (initial mapping)              |
| 2      | Map communicating qubits together  | Insert swap gates with the highest reliability  | Yes (initial mapping and routing)  |

## Acknowledgments

This work is supported by the QuantERA grant EQUIP with the grant numbers PCI2022-133004 and PCI2022-132922, funded by Agencia Estatal de Investigación, Ministerio de Ciencia e Innovación, Gobierno de España, MCIN/AEI/10.13039/501100011033, and by the European Union “NextGenerationEU/PRTR”.
