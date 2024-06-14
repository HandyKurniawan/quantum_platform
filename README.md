# Quantum Compilations Platform
A platform for experimenting with and applying various quantum compilation techniques across multiple quantum computing backends.

## Table of contents

- [Setup](#setup)
- [Example in Python](#example-in-python)
- [Compilation Techniques](#compilation-techniques)
  - [Initial Mapping](#initial-mapping)
  - [Routing](#routing)
- [Simulators](#simulators)
- [Tutorial](#tutorial)
- [Acknowledgments](#acknowledgments)

## Setup

### Installation

#### Clone Github

First, you need to clone the project to get all the necessary files

``` terminal
git clone https://github.com/HandyKurniawan/quantum_platform.git
```

#### MariaDB

To set up the database, follow these steps:

1. Install MariaDB:
   
``` terminal
sudo apt update
sudo apt install mariadb-server
sudo systemctl start mariadb
sudo systemctl enable mariadb
```

2. Secure your MariaDB installation:

``` terminal
sudo mysql_secure_installation
```

3. Create a database and user:

Login with the root account to the database

``` terminal
mysql -u root -p
```

Then you can create a new user from here

``` mysql
CREATE USER 'user_1'@'%' IDENTIFIED BY '1234';
GRANT ALL PRIVILEGES ON *.* TO 'user_1'@'%';
GRANT ALL PRIVILEGES ON *.* TO 'user_1'@'localhost' IDENTIFIED BY '1234' WITH GRANT OPTION;
FLUSH PRIVILEGES;
CREATE DATABASE  IF NOT EXISTS `framework`;
exit;
```

4. Import table structures:

``` terminal
mysql -u user_1 -p framework < quantum_platform\mariadb\framework_structure.sql
mysql -u user_1 -p framework < quantum_platform\mariadb\calibration_data_structure.sql
mysql -u user_1 -p framework < quantum_platform\mariadb\data.sql
```
Note: These commands need to be run one by one, and the password for user_1 is 1234

Now your database is ready.

#### Platform

First, we need to go to the home folder of the project (\quantum_platform)

Note: If you have an older version (or if you don't have it) of Python please upgrade (install) it first:

``` terminal
sudo add-apt-repository ppa:deadsnakes/ppa    
sudo apt update  
sudo apt install python.3.12
```

Install dependencies and set up the Python environment:

``` terminal
sudo apt-get update
sudo apt-get install python3.xx-venv 
sudo apt-get install libmuparser2v5
python3.xx -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
`3.xx` is depends on what Python3.xx version you have)

Now, we are good to go 🚀

#### Config

Now, we need to change the config for the database, and the path for the TriQ before continue

```terminal
[MySQLConfig]
user = user_1
password = 1234
host = localhost
database = framework

...

[QuantumConfig]
...
triq_path = ~/Github/quantum_platform/wrappers/triq_wrapper/
...
```

## Example in Python

First, we need to set the object

```python
# Setup the object
from qEmQUIP import QEM, conf
token = "74076e69ed0d571c8e0ff8c0b2c912c28681d47426cf16a5d817825de16f7dbd95bf6ff7c604b706803b78b2e21d1dd5cacf9f1b0aa81d672d938bded8049a17"
q = QEM(runs=conf.runs, user_id=conf.user_id, token=token)
```

1. To run the circuit directly to the real backend with the selected compilation

```python
# prepare quantum circuit 
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

# select compilation techniques
compilations = ["qiskit_0", "qiskit_3", "triq_lcd_sabre"]

# send the circuit result to the backend and database, later to get the result we need to run a script to retrieve the result from the cloud
q.send_to_real_backend(qasm_files, compilations)
```

2. Compiled them through a series of quantum circuits, compilations and different noise_levels in the simulator

```python

df = q.run_simulator(qasm_files, compilations, noise_levels, shots, True)
```

3. Compiled using the selected compilation and retrieved the compiled QASM
   
```python
# prepare the circuit
conf.base_folder = "./circuits/testing/"
qasm_files = q.get_qasm_files_from_path()

# set the number of shots
shots = 10000

# select compilation techniques
compilations = ["qiskit_0", "qiskit_3", "triq_lcd_sabre"]

# get the circuit properties
qc = q.get_circuit_properties(qasm_source=qasm_text)

# compiled with the chosen compilation
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



