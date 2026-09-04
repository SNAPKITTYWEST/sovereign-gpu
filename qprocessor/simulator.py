"""Statevector quantum simulator."""
from typing import List, Tuple, Optional
import math
import random
from .circuit import QuantumCircuit, QuantumGate, Qubit, ClassicalBit
from .errors import SimulationError

def normalize_statevector(state: List[complex]) -> List[complex]:
    norm = math.sqrt(sum(abs(amp)**2 for amp in state))
    if norm == 0:
        raise SimulationError("Zero norm statevector")
    return [amp / norm for amp in state]

def apply_x(state: List[complex], qubit_index: int, num_qubits: int) -> List[complex]:
    new_state = [0j] * len(state)
    for i in range(len(state)):
        flipped_i = i ^ (1 << qubit_index)
        new_state[flipped_i] = state[i]
    return new_state

def apply_y(state: List[complex], qubit_index: int, num_qubits: int) -> List[complex]:
    new_state = [0j] * len(state)
    for i in range(len(state)):
        flipped_i = i ^ (1 << qubit_index)
        if (i >> qubit_index) & 1:
            new_state[flipped_i] = -1j * state[i]
        else:
            new_state[flipped_i] = 1j * state[i]
    return new_state

def apply_z(state: List[complex], qubit_index: int, num_qubits: int) -> List[complex]:
    new_state = [0j] * len(state)
    for i in range(len(state)):
        if (i >> qubit_index) & 1:
            new_state[i] = -state[i]
        else:
            new_state[i] = state[i]
    return new_state

def apply_h(state: List[complex], qubit_index: int, num_qubits: int) -> List[complex]:
    new_state = [0j] * len(state)
    for i in range(len(state)):
        if (i >> qubit_index) & 1:
            flipped_i = i ^ (1 << qubit_index)
            new_state[flipped_i] += state[i] / math.sqrt(2)
            new_state[i] -= state[i] / math.sqrt(2)
        else:
            flipped_i = i ^ (1 << qubit_index)
            new_state[flipped_i] += state[i] / math.sqrt(2)
            new_state[i] += state[i] / math.sqrt(2)
    return new_state

def apply_s(state: List[complex], qubit_index: int, num_qubits: int) -> List[complex]:
    new_state = [0j] * len(state)
    for i in range(len(state)):
        if (i >> qubit_index) & 1:
            new_state[i] = state[i] * 1j
        else:
            new_state[i] = state[i]
    return new_state

def apply_t(state: List[complex], qubit_index: int, num_qubits: int) -> List[complex]:
    new_state = [0j] * len(state)
    for i in range(len(state)):
        if (i >> qubit_index) & 1:
            new_state[i] = state[i] * (1 + 1j) / math.sqrt(2)
        else:
            new_state[i] = state[i]
    return new_state

def apply_rx(state: List[complex], qubit_index: int, num_qubits: int, angle: float) -> List[complex]:
    new_state = [0j] * len(state)
    cos_half = math.cos(angle / 2)
    sin_half = math.sin(angle / 2)
    for i in range(len(state)):
        if (i >> qubit_index) & 1:
            flipped_i = i ^ (1 << qubit_index)
            new_state[flipped_i] += -1j * sin_half * state[i]
            new_state[i] += cos_half * state[i]
        else:
            flipped_i = i ^ (1 << qubit_index)
            new_state[flipped_i] += -1j * sin_half * state[i]
            new_state[i] += cos_half * state[i]
    return new_state

def apply_ry(state: List[complex], qubit_index: int, num_qubits: int, angle: float) -> List[complex]:
    new_state = [0j] * len(state)
    cos_half = math.cos(angle / 2)
    sin_half = math.sin(angle / 2)
    for i in range(len(state)):
        if (i >> qubit_index) & 1:
            flipped_i = i ^ (1 << qubit_index)
            new_state[flipped_i] += -sin_half * state[i]
            new_state[i] += cos_half * state[i]
        else:
            flipped_i = i ^ (1 << qubit_index)
            new_state[flipped_i] += sin_half * state[i]
            new_state[i] += cos_half * state[i]
    return new_state

def apply_rz(state: List[complex], qubit_index: int, num_qubits: int, angle: float) -> List[complex]:
    new_state = [0j] * len(state)
    for i in range(len(state)):
        if (i >> qubit_index) & 1:
            new_state[i] = state[i] * complex(math.cos(angle/2), math.sin(angle/2))**2
        else:
            new_state[i] = state[i] * complex(math.cos(angle/2), -math.sin(angle/2))**2
    return new_state

def apply_cx(state: List[complex], control_index: int, target_index: int, num_qubits: int) -> List[complex]:
    new_state = [0j] * len(state)
    for i in range(len(state)):
        if (i >> control_index) & 1:
            flipped_i = i ^ (1 << target_index)
            new_state[flipped_i] = state[i]
        else:
            new_state[i] = state[i]
    return new_state

def apply_cz(state: List[complex], control_index: int, target_index: int, num_qubits: int) -> List[complex]:
    new_state = [0j] * len(state)
    for i in range(len(state)):
        if ((i >> control_index) & 1) and ((i >> target_index) & 1):
            new_state[i] = -state[i]
        else:
            new_state[i] = state[i]
    return new_state

def apply_swap(state: List[complex], index1: int, index2: int, num_qubits: int) -> List[complex]:
    new_state = [0j] * len(state)
    for i in range(len(state)):
        bit1 = (i >> index1) & 1
        bit2 = (i >> index2) & 1
        if bit1 == bit2:
            new_state[i] = state[i]
        else:
            flipped_i = i ^ (1 << index1) ^ (1 << index2)
            new_state[flipped_i] = state[i]
    return new_state

def apply_reset(state: List[complex], qubit_index: int, num_qubits: int) -> List[complex]:
    new_state = [0j] * len(state)
    zero_prob = 0.0
    for i in range(len(state)):
        if not ((i >> qubit_index) & 1):
            new_state[i] = state[i]
            zero_prob += abs(state[i])**2
    if zero_prob == 0:
        new_state[0] = 1.0
    else:
        norm = math.sqrt(zero_prob)
        new_state = [amp / norm for amp in new_state]
    return new_state

def measure(state: List[complex], qubit_index: int, num_qubits: int) -> Tuple[int, List[complex]]:
    prob_zero = 0.0
    for i in range(len(state)):
        if not ((i >> qubit_index) & 1):
            prob_zero += abs(state[i])**2
    outcome = 0 if random.random() < prob_zero else 1
    new_state = [0j] * len(state)
    norm = 0.0
    for i in range(len(state)):
        if ((i >> qubit_index) & 1) == outcome:
            new_state[i] = state[i]
            norm += abs(state[i])**2
    if norm > 0:
        norm = math.sqrt(norm)
        new_state = [amp / norm for amp in new_state]
    else:
        new_state = [0j] * len(state)
        new_state[0] = 1.0
    return outcome, new_state

class QuantumSimulator:
    def __init__(self):
        self.state: List[complex] = [1.0]
        self.num_qubits = 0
        self.num_cbts = 0
        self.measurement_results: List[int] = []

    def reset(self, num_qubits: int = 0, num_cbts: int = 0):
        self.num_qubits = num_qubits
        self.num_cbts = num_cbts
        self.state = [1.0] + [0.0] * ((1 << num_qubits) - 1)
        self.measurement_results = []

    def ensure_qubits(self, num_qubits: int):
        if num_qubits > self.num_qubits:
            old_state = self.state
            new_size = 1 << num_qubits
            self.state = [0j] * new_size
            for i in range(len(old_state)):
                self.state[i] = old_state[i]
            self.num_qubits = num_qubits

    def run_circuit(self, circuit: QuantumCircuit) -> List[int]:
        self.reset(circuit.width(), len(circuit.cbits))
        errors = circuit.validate()
        if errors:
            raise SimulationError(f"Circuit validation failed: {'; '.join(errors)}")
        self.measurement_results = []
        for moment in circuit.moments:
            for gate in moment.gates:
                self.apply_gate(gate)
        return self.measurement_results.copy()

    def apply_gate(self, gate: QuantumGate):
        if gate.name == 'H':
            for qubit in gate.qubits:
                self.state = apply_h(self.state, qubit.index, self.num_qubits)
        elif gate.name == 'X':
            for qubit in gate.qubits:
                self.state = apply_x(self.state, qubit.index, self.num_qubits)
        elif gate.name == 'Y':
            for qubit in gate.qubits:
                self.state = apply_y(self.state, qubit.index, self.num_qubits)
        elif gate.name == 'Z':
            for qubit in gate.qubits:
                self.state = apply_z(self.state, qubit.index, self.num_qubits)
        elif gate.name == 'S':
            for qubit in gate.qubits:
                self.state = apply_s(self.state, qubit.index, self.num_qubits)
        elif gate.name == 'T':
            for qubit in gate.qubits:
                self.state = apply_t(self.state, qubit.index, self.num_qubits)
        elif gate.name == 'RX':
            if len(gate.parameters) != 1:
                raise SimulationError("RX gate requires exactly one parameter")
            angle = gate.parameters[0]
            for qubit in gate.qubits:
                self.state = apply_rx(self.state, qubit.index, self.num_qubits, angle)
        elif gate.name == 'RY':
            if len(gate.parameters) != 1:
                raise SimulationError("RY gate requires exactly one parameter")
            angle = gate.parameters[0]
            for qubit in gate.qubits:
                self.state = apply_ry(self.state, qubit.index, self.num_qubits, angle)
        elif gate.name == 'RZ':
            if len(gate.parameters) != 1:
                raise SimulationError("RZ gate requires exactly one parameter")
            angle = gate.parameters[0]
            for qubit in gate.qubits:
                self.state = apply_rz(self.state, qubit.index, self.num_qubits, angle)
        elif gate.name == 'CX':
            if len(gate.qubits) != 2:
                raise SimulationError("CX gate requires exactly two qubits")
            self.state = apply_cx(self.state, gate.qubits[0].index, gate.qubits[1].index, self.num_qubits)
        elif gate.name == 'CZ':
            if len(gate.qubits) != 2:
                raise SimulationError("CZ gate requires exactly two qubits")
            self.state = apply_cz(self.state, gate.qubits[0].index, gate.qubits[1].index, self.num_qubits)
        elif gate.name == 'SWAP':
            if len(gate.qubits) != 2:
                raise SimulationError("SWAP gate requires exactly two qubits")
            self.state = apply_swap(self.state, gate.qubits[0].index, gate.qubits[1].index, self.num_qubits)
        elif gate.name == 'RESET':
            for qubit in gate.qubits:
                self.state = apply_reset(self.state, qubit.index, self.num_qubits)
        elif gate.name == 'MEASURE':
            if len(gate.qubits) != 1 or len(gate.classical_bits) != 1:
                raise SimulationError("MEASURE gate requires exactly one qubit and one classical bit")
            qubit = gate.qubits[0]
            cbit = gate.classical_bits[0]
            outcome, self.state = measure(self.state, qubit.index, self.num_qubits)
            self.measurement_results.append(outcome)
        elif gate.name == 'BARRIER':
            pass
        else:
            raise SimulationError(f"Unsupported gate: {gate.name}")

    def get_statevector(self) -> List[complex]:
        return self.state.copy()

    def get_probabilities(self) -> List[float]:
        return [abs(amp)**2 for amp in self.state]

    def measure_all(self) -> List[int]:
        results = []
        state = self.state.copy()
        for qubit_index in range(self.num_qubits):
            outcome, state = measure(state, qubit_index, self.num_qubits)
            results.append(outcome)
        return results

    def sample(self, shots: int = 1024) -> dict:
        counts = {}
        for _ in range(shots):
            state_copy = self.state.copy()
            result = self.measure_all()
            bitstring = ''.join(str(bit) for bit in result)
            counts[bitstring] = counts.get(bitstring, 0) + 1
        return counts
