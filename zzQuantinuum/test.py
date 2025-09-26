from pytket import Circuit
from pytket.extensions.quantinuum import QuantinuumBackend

circ = Circuit(2).H(0).CX(0, 1).CZ(0, 1)
backend = QuantinuumBackend('H1-1E')

# Compile the circuit in place. The optimisation level is set to 2 by default.
backend.default_compilation_pass().apply(circ)

compiled_circ = backend.get_compiled_circuit(circ)