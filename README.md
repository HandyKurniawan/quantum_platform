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
cd quantum_platform
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
mysql -u user_1 -p framework < mariadb/framework_structure.sql
mysql -u user_1 -p framework < mariadb/data.sql
```
Note: These commands need to be run one by one, and the password for user_1 is 1234

Now your database is ready.

#### Platform

First, we need to go to the home folder of the project (\quantum_platform)

Note: If you have an older version (or if you don't have it) of Python please upgrade (install) it first:

``` terminal
sudo add-apt-repository ppa:deadsnakes/ppa    
sudo apt update  
sudo apt install python3.12
```

Install dependencies and set up the Python environment:

``` terminal
sudo apt-get update
sudo apt-get install python3.xx-venv 
sudo apt-get install libmuparser2v5
sudo apt-get install libz3-dev
python3.xx -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
`Python3.xx` is depends on what Python3.xx version you have)

#### Config

Now, we need to update the `config.ini` file to change the config for the database, and the path for the TriQ before continue

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
Now, we are good to go 🚀

## Tutorial

To run them on jupyter notebook,  we need to create a kernel 

``` terminal
pip install ipykernel
python -m ipykernel install --user --name .venv --display-name "platform"
jupyter notebook
``` 

When you open jupyter notebook, don't forget to change the kernel to `platform`

![screen](https://github.com/HandyKurniawan/quantum_platform/blob/main/img/screen.png)

**In order to see that everything is going well, please execute this jupyter notebook file with in-depth examples:** [here](https://github.com/HandyKurniawan/quantum_platform/blob/main/tutorial.ipynb)

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

## Example in Python

First, we need to set the object

```python
# Setup the object
from qEmQUIP import QEM, conf
token = "<qiskit_token>"
q = QEM(runs=conf.runs, user_id=conf.user_id, token=token)
```

Note: `<qiskit_token>` needs to be changed with the real one.

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

## Acknowledgments

This work was supported by the QuantERA project EQUIP (grants PCI2022-133004 and PCI2022-132922, funded by the Agencia Estatal de Investigación, Ministerio de Ciencia e Innovación, Gobierno de España, MCIN/AEI/10.13039/501100011033, and  ANR-22-QUA2-0005-01, funded by the Agence Nationale de la Recherche, France), and by the European Union "NextGenerationEU/PRTR". This research is part of the project PID2023-147059OB-I00 funded by MCIU/AEI/10.13039/501100011033/FEDER, UE. Handy Kurniawan acknowledges support from the Comunidad de Madrid under grant number PIPF-2023/COM-30051.  

We acknowledge the use of IBM Quantum services for this work. The views expressed are those of the authors and do not reflect the official policy or position of IBM or the IBM Quantum team.

## Contact information

If you have any questions, feel free to contact handykur@ucm.es


