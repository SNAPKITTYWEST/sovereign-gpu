# Copyright © 2026 SnapKitty Collective and contributors.
#
# This file is part of a work licensed under the
# SnapKitty Strong Network Copyleft License Version 1.0 (SSNCL-1.0).
#
# You may use, study, modify, copy, and redistribute this work
# only under the terms of SSNCL-1.0.
#
# A copy of SSNCL-1.0 must accompany this work.

"""Multidimensional quantum array abstraction."""
from typing import List, Tuple, Optional, Union
import math

class QuantumShape:
    def __init__(self, dims: List[int]):
        self.dims = dims
        self.rank = len(dims)
        self.size = 1
        for d in dims:
            self.size *= d

    def __eq__(self, other):
        return isinstance(other, QuantumShape) and self.dims == other.dims

    def __repr__(self):
        return f"QuantumShape({self.dims})"

class QuantumStride:
    def __init__(self, shape: QuantumShape):
        self.shape = shape
        self.strides = []
        stride = 1
        for dim in reversed(shape.dims):
            self.strides.insert(0, stride)
            stride *= dim

    def offset(self, indices: List[int]) -> int:
        if len(indices) != self.shape.rank:
            raise ValueError(f"Expected {self.shape.rank} indices, got {len(indices)}")
        offset = 0
        for i, idx in enumerate(indices):
            if idx < 0 or idx >= self.shape.dims[i]:
                raise ValueError(f"Index {idx} out of bounds for dimension {i} (size {self.shape.dims[i]})")
            offset += idx * self.strides[i]
        return offset

class QuantumIndex:
    def __init__(self, indices: List[int]):
        self.indices = indices

class QuantumSliceObj:
    def __init__(self, start: int, stop: int, step: int = 1):
        self.start = start
        self.stop = stop
        self.step = step

class QuantumArray:
    def __init__(self, name: str, shape: QuantumShape, data: Optional[List[complex]] = None):
        self.name = name
        self.shape = shape
        self.stride = QuantumStride(shape)
        if data is None:
            self.data = [0+0j] * shape.size
        else:
            if len(data) != shape.size:
                raise ValueError(f"Data length {len(data)} does not match array size {shape.size}")
            self.data = data

    def __getitem__(self, indices: Union[int, List[int], Tuple[int, ...], QuantumSliceObj]) -> Union[complex, 'QuantumArray']:
        if isinstance(indices, int):
            indices = [indices]
        elif isinstance(indices, tuple):
            indices = list(indices)
        elif isinstance(indices, QuantumSliceObj):
            return self.slice(indices.start, indices.stop, indices.step, 0)
        if len(indices) == 1 and self.shape.rank == 1:
            return self.data[self.stride.offset(indices)]
        elif len(indices) < self.shape.rank:
            new_shape_dims = self.shape.dims[len(indices):]
            new_shape = QuantumShape(new_shape_dims)
            new_array = QuantumArray(f"{self.name}_slice", new_shape)
            indices_list = indices + [0] * (self.shape.rank - len(indices))
            for i in range(new_shape.size):
                multi_index = []
                temp = i
                for dim in reversed(new_shape.dims):
                    multi_index.insert(0, temp % dim)
                    temp //= dim
                full_index = indices_list[:-len(new_shape.dims)] + multi_index
                new_array.data[i] = self.data[self.stride.offset(full_index)]
            return new_array
        else:
            return self.data[self.stride.offset(indices)]

    def __setitem__(self, indices: Union[int, List[int], Tuple[int, ...]], value: complex):
        if isinstance(indices, int):
            indices = [indices]
        elif isinstance(indices, tuple):
            indices = list(indices)
        if len(indices) == 1 and self.shape.rank == 1:
            self.data[self.stride.offset(indices)] = value
        elif len(indices) < self.shape.rank:
            indices_list = indices + [0] * (self.shape.rank - len(indices))
            for i in range(self.shape.size):
                multi_index = []
                temp = i
                for dim in reversed(self.shape.dims):
                    multi_index.insert(0, temp % dim)
                    temp //= dim
                if multi_index[len(indices):] == [0] * (self.shape.rank - len(indices)):
                    self.data[i] = value
        else:
            self.data[self.stride.offset(indices)] = value

    def reshape(self, new_dims: List[int]) -> 'QuantumArray':
        new_shape = QuantumShape(new_dims)
        if new_shape.size != self.shape.size:
            raise ValueError(f"Cannot reshape array of size {self.shape.size} to shape {new_dims}")
        return QuantumArray(f"{self.name}_reshape", new_shape, self.data.copy())

    def transpose(self, axes: Optional[List[int]] = None) -> 'QuantumArray':
        if axes is None:
            axes = list(reversed(range(self.shape.rank)))
        if len(axes) != self.shape.rank:
            raise ValueError(f"Transpose axes must have length {self.shape.rank}")
        if sorted(axes) != list(range(self.shape.rank)):
            raise ValueError("Transpose axes must be a permutation of [0, 1, ..., rank-1]")
        new_shape_dims = [self.shape.dims[i] for i in axes]
        new_shape = QuantumShape(new_shape_dims)
        new_array = QuantumArray(f"{self.name}_transpose", new_shape)
        for i in range(new_shape.size):
            multi_index = []
            temp = i
            for dim in reversed(new_shape.dims):
                multi_index.insert(0, temp % dim)
                temp //= dim
            original_index = [multi_index[axes.index(i)] for i in range(self.shape.rank)]
            new_array.data[i] = self.data[self.stride.offset(original_index)]
        return new_array

    def flatten(self) -> 'QuantumArray':
        return self.reshape([self.shape.size])

    def slice(self, start: int, stop: int, step: int, axis: int) -> 'QuantumArray':
        if axis < 0 or axis >= self.shape.rank:
            raise ValueError(f"Axis {axis} out of bounds for rank {self.shape.rank}")
        if step == 0:
            raise ValueError("Slice step cannot be zero")
        new_shape_dims = self.shape.dims.copy()
        if step > 0:
            actual_stop = min(stop, self.shape.dims[axis])
            new_shape_dims[axis] = max(0, (actual_stop - start + step - 1) // step)
        else:
            actual_stop = max(stop, -1)
            new_shape_dims[axis] = max(0, (start - actual_stop - step - 1) // (-step))
        new_shape = QuantumShape(new_shape_dims)
        new_array = QuantumArray(f"{self.name}_slice", new_shape)
        for i in range(new_shape.size):
            multi_index = []
            temp = i
            for dim in reversed(new_shape.dims):
                multi_index.insert(0, temp % dim)
                temp //= dim
            original_index = multi_index.copy()
            original_index[axis] = start + multi_index[axis] * step
            new_array.data[i] = self.data[self.stride.offset(original_index)]
        return new_array

    def broadcast_to(self, shape: QuantumShape) -> 'QuantumArray':
        if len(shape.dims) < self.shape.rank:
            raise ValueError("Cannot broadcast to lower rank")
        for i, dim in enumerate(reversed(self.shape.dims)):
            if dim != 1 and dim != shape.dims[-(i+1)]:
                raise ValueError(f"Incompatible shapes for broadcasting: {self.shape.dims} and {shape.dims}")
        new_shape = shape
        new_array = QuantumArray(f"{self.name}_broadcast", new_shape)
        for i in range(new_shape.size):
            multi_index = []
            temp = i
            for dim in reversed(new_shape.dims):
                multi_index.insert(0, temp % dim)
                temp //= dim
            original_index = []
            for j, dim in enumerate(multi_index):
                if j < len(self.shape.dims) and self.shape.dims[j] == 1:
                    original_index.append(0)
                elif j < len(self.shape.dims):
                    original_index.append(dim)
                else:
                    original_index.append(0)
            new_array.data[i] = self.data[self.stride.offset(original_index)]
        return new_array

    def dot(self, other: 'QuantumArray') -> 'QuantumArray':
        if self.shape.rank != 1 or other.shape.rank != 1:
            raise ValueError("Dot product only defined for 1D arrays")
        if self.shape.dims[0] != other.shape.dims[0]:
            raise ValueError("Arrays must have same length for dot product")
        result = 0+0j
        for i in range(self.shape.dims[0]):
            result += self.data[i] * other.data[i]
        return QuantumArray(f"{self.name}_dot", QuantumShape([1]), [result])

    def matmul(self, other: 'QuantumArray') -> 'QuantumArray':
        if self.shape.rank != 2 or other.shape.rank != 2:
            raise ValueError("Matrix multiplication only defined for 2D arrays")
        if self.shape.dims[1] != other.shape.dims[0]:
            raise ValueError(f"Incompatible shapes for matrix multiplication: {self.shape.dims} and {other.shape.dims}")
        m, n = self.shape.dims
        p = other.shape.dims[1]
        result_data = [0+0j] * (m * p)
        for i in range(m):
            for j in range(p):
                for k in range(n):
                    result_data[i * p + j] += self.data[i * n + k] * other.data[k * p + j]
        return QuantumArray(f"{self.name}_matmul", QuantumShape([m, p]), result_data)

    def reduce(self, op: str, axis: Optional[int] = None) -> 'QuantumArray':
        if axis is not None and (axis < 0 or axis >= self.shape.rank):
            raise ValueError(f"Axis {axis} out of bounds for rank {self.shape.rank}")
        if op == 'sum':
            if axis is None:
                total = sum(self.data)
                return QuantumArray(f"{self.name}_sum", QuantumShape([1]), [total])
            else:
                new_shape_dims = self.shape.dims[:axis] + self.shape.dims[axis+1:]
                new_shape = QuantumShape(new_shape_dims)
                new_array = QuantumArray(f"{self.name}_sum_axis{axis}", new_shape)
                for i in range(new_shape.size):
                    multi_index = []
                    temp = i
                    for dim in reversed(new_shape.dims):
                        multi_index.insert(0, temp % dim)
                        temp //= dim
                    full_indices = []
                    for pos in range(self.shape.rank):
                        if pos < axis:
                            full_indices.append(multi_index[pos])
                        elif pos == axis:
                            full_indices.append(0)
                        else:
                            full_indices.append(multi_index[pos-1])
                    total = 0+0j
                    for k in range(self.shape.dims[axis]):
                        full_indices[axis] = k
                        total += self.data[self.stride.offset(full_indices)]
                    new_array.data[i] = total
                return new_array
        elif op == 'prod':
            if axis is None:
                total = 1+0j
                for val in self.data:
                    total *= val
                return QuantumArray(f"{self.name}_prod", QuantumShape([1]), [total])
            else:
                new_shape_dims = self.shape.dims[:axis] + self.shape.dims[axis+1:]
                new_shape = QuantumShape(new_shape_dims)
                new_array = QuantumArray(f"{self.name}_prod_axis{axis}", new_shape)
                for i in range(new_shape.size):
                    multi_index = []
                    temp = i
                    for dim in reversed(new_shape.dims):
                        multi_index.insert(0, temp % dim)
                        temp //= dim
                    total = 1+0j
                    for k in range(self.shape.dims[axis]):
                        full_index = multi_index[:axis] + [k] + multi_index[axis:]
                        total *= self.data[self.stride.offset(full_index)]
                    new_array.data[i] = total
                return new_array
        else:
            raise ValueError(f"Unsupported reduction operation: {op}")

    def __repr__(self):
        return f"QuantumArray({self.name}, shape={self.shape.dims})"
