# Copyright © 2026 SnapKitty Collective and contributors.
#
# This file is part of a work licensed under the
# SnapKitty Strong Network Copyleft License Version 1.0 (SSNCL-1.0).
#
# You may use, study, modify, copy, and redistribute this work
# only under the terms of SSNCL-1.0.
#
# A copy of SSNCL-1.0 must accompany this work.

"""Tests for quantum array functionality."""
import unittest
from ..arrays import QuantumArray, QuantumShape

class TestArrays(unittest.TestCase):
    def test_quantum_shape(self):
        shape = QuantumShape([2, 3])
        self.assertEqual(shape.rank, 2)
        self.assertEqual(shape.dims, [2, 3])
        self.assertEqual(shape.size, 6)

    def test_quantum_array_creation(self):
        shape = QuantumShape([2, 2])
        arr = QuantumArray("test", shape)
        self.assertEqual(arr.name, "test")
        self.assertEqual(arr.shape.dims, [2, 2])
        self.assertEqual(len(arr.data), 4)
        for val in arr.data:
            self.assertEqual(val, 0+0j)

    def test_array_indexing(self):
        arr = QuantumArray("test", QuantumShape([2, 2]), [1+0j, 2+0j, 3+0j, 4+0j])
        self.assertEqual(arr[0, 0], 1+0j)
        self.assertEqual(arr[0, 1], 2+0j)
        self.assertEqual(arr[1, 0], 3+0j)
        self.assertEqual(arr[1, 1], 4+0j)

    def test_array_reshape(self):
        arr = QuantumArray("test", QuantumShape([4]), [1+0j, 2+0j, 3+0j, 4+0j])
        reshaped = arr.reshape([2, 2])
        self.assertEqual(reshaped.shape.dims, [2, 2])
        self.assertEqual(reshaped.data, [1+0j, 2+0j, 3+0j, 4+0j])

    def test_array_transpose(self):
        arr = QuantumArray("test", QuantumShape([2, 3]), 
                           [1+0j, 2+0j, 3+0j, 4+0j, 5+0j, 6+0j])
        transposed = arr.transpose()
        self.assertEqual(transposed.shape.dims, [3, 2])
        self.assertEqual(transposed[0, 0], 1+0j)
        self.assertEqual(transposed[0, 1], 4+0j)
        self.assertEqual(transposed[1, 0], 2+0j)
        self.assertEqual(transposed[1, 1], 5+0j)
        self.assertEqual(transposed[2, 0], 3+0j)
        self.assertEqual(transposed[2, 1], 6+0j)

    def test_array_flatten(self):
        arr = QuantumArray("test", QuantumShape([2, 3]), 
                           [1+0j, 2+0j, 3+0j, 4+0j, 5+0j, 6+0j])
        flattened = arr.flatten()
        self.assertEqual(flattened.shape.dims, [6])
        self.assertEqual(flattened.data, [1+0j, 2+0j, 3+0j, 4+0j, 5+0j, 6+0j])

    def test_array_dot(self):
        arr1 = QuantumArray("a", QuantumShape([3]), [1+0j, 2+0j, 3+0j])
        arr2 = QuantumArray("b", QuantumShape([3]), [4+0j, 5+0j, 6+0j])
        dot_result = arr1.dot(arr2)
        self.assertEqual(dot_result.shape.dims, [1])
        self.assertEqual(dot_result.data[0], (1*4 + 2*5 + 3*6)+0j)

    def test_array_matmul(self):
        arr1 = QuantumArray("a", QuantumShape([2, 3]), 
                            [1+0j, 2+0j, 3+0j, 4+0j, 5+0j, 6+0j])
        arr2 = QuantumArray("b", QuantumShape([3, 2]), 
                            [7+0j, 8+0j, 9+0j, 10+0j, 11+0j, 12+0j])
        matmul_result = arr1.matmul(arr2)
        self.assertEqual(matmul_result.shape.dims, [2, 2])
        self.assertAlmostEqual(matmul_result[0, 0].real, 58)
        self.assertAlmostEqual(matmul_result[0, 1].real, 64)
        self.assertAlmostEqual(matmul_result[1, 0].real, 139)
        self.assertAlmostEqual(matmul_result[1, 1].real, 154)

    def test_array_reduce_sum(self):
        arr = QuantumArray("test", QuantumShape([3, 4]), 
                           [float(i+1) for i in range(12)])
        total = arr.reduce('sum')
        self.assertEqual(total.shape.dims, [1])
        self.assertAlmostEqual(total.data[0].real, 78.0)
        sum_axis0 = arr.reduce('sum', axis=0)
        self.assertEqual(sum_axis0.shape.dims, [4])
        self.assertAlmostEqual(sum_axis0.data[0].real, 15.0)
        self.assertAlmostEqual(sum_axis0.data[1].real, 18.0)
        self.assertAlmostEqual(sum_axis0.data[2].real, 21.0)
        self.assertAlmostEqual(sum_axis0.data[3].real, 24.0)
        sum_axis1 = arr.reduce('sum', axis=1)
        self.assertEqual(sum_axis1.shape.dims, [3])
        self.assertAlmostEqual(sum_axis1.data[0].real, 10.0)
        self.assertAlmostEqual(sum_axis1.data[1].real, 26.0)
        self.assertAlmostEqual(sum_axis1.data[2].real, 42.0)

    def test_array_reduce_prod(self):
        arr = QuantumArray("test", QuantumShape([2, 3]), 
                           [1+0j, 2+0j, 3+0j, 4+0j, 5+0j, 6+0j])
        total = arr.reduce('prod')
        self.assertEqual(total.shape.dims, [1])
        self.assertAlmostEqual(total.data[0].real, 720.0)
        prod_axis0 = arr.reduce('prod', axis=0)
        self.assertEqual(prod_axis0.shape.dims, [3])
        self.assertAlmostEqual(prod_axis0.data[0].real, 4.0)
        self.assertAlmostEqual(prod_axis0.data[1].real, 10.0)
        self.assertAlmostEqual(prod_axis0.data[2].real, 18.0)

if __name__ == '__main__':
    unittest.main()
