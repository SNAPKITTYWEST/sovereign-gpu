NB. Copyright © 2026 SnapKitty Collective and contributors.
NB.
NB. This file is part of a work licensed under the
NB. SnapKitty Strong Network Copyleft License Version 1.0 (SSNCL-1.0).
NB.
NB. You may use, study, modify, copy, and redistribute this work
NB. only under the terms of SSNCL-1.0.
NB.
NB. A copy of SSNCL-1.0 must accompany this work.

// Array operations example
a = [1, 2, 3, 4]
b = [5, 6, 7, 8]
c = a + b
d = reshape(a, [2, 2])
e = reshape(b, [2, 2])
f = d +.× e // Element-wise multiplication
g = +/ f // Sum all elements
h = reshape(f, [4])
i = h * 2 // Scalar multiplication
