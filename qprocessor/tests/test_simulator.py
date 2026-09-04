"""Tests for quantum simulator."""
import unittest
import math
from ..circuit import QuantumCircuit, Qubit
from ..simulator import QuantumSimulator

class TestSimulator(unittest.TestCase):
    def test_initialize_state(self):
        sim = QuantumSimulator()
        sim.reset(2)
        self.assertEqual(len(sim.state), 4)
        self.assertAlmostEqual(sim.state[0], 1.0)
        self.assertAlmostEqual(sim.state[1], 0.0)
        self.assertAlmostEqual(sim.state[2], 0.0)
        self.assertAlmostEqual(sim.state[3], 0.0)

    def test_apply_h_gate(self):
        sim = QuantumSimulator()
        sim.reset(1)
        sim.state = [1.0, 0.0]
        from ..simulator import apply_h
        sim.state = apply_h(sim.state, 0, 1)
        self.assertAlmostEqual(sim.state[0], math.sqrt(0.5))
        self.assertAlmostEqual(sim.state[1], math.sqrt(0.5))

    def test_bell_state(self):
        sim = QuantumSimulator()
        sim.reset(2)
        sim.state = [1.0, 0.0, 0.0, 0.0]
        from ..simulator import apply_h, apply_cx
        sim.state = apply_h(sim.state, 0, 2)
        sim.state = apply_cx(sim.state, 0, 1, 2)
        self.assertAlmostEqual(sim.state[0], math.sqrt(0.5))
        self.assertAlmostEqual(sim.state[1], 0.0)
        self.assertAlmostEqual(sim.state[2], 0.0)
        self.assertAlmostEqual(sim.state[3], math.sqrt(0.5))

    def test_run_circuit(self):
        sim = QuantumSimulator()
        circuit = QuantumCircuit(2)
        circuit.add_gate('H', [Qubit(0)])
        circuit.add_gate('CX', [Qubit(0), Qubit(1)])
        results = sim.run_circuit(circuit)
        self.assertIn(results, [[0,0], [1,1]])

if __name__ == '__main__':
    unittest.main()
