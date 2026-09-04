/-
  Sovereign Logic Implementation: SUBLEQ State Machine
  Field: P_GOLD (18446744069414584321)
  Author: Ahmad Ali Parr · SNAPKITTYWEST
  License: Sovereign Source License v1.0
-/

import Mathlib.Data.ZMod.Basic

def P_GOLD : Nat := 18446744069414584321

-- Use a function for memory to ensure total mapping (No bounds errors = No sorries)
def Memory := Nat → ZMod P_GOLD

structure SubleqState where
  mem : Memory
  pc : Nat

structure SubleqInstr where
  A : Nat
  B : Nat
  C : Nat

def subleq_step (state : SubleqState) (instr : SubleqInstr) : SubleqState :=
  let valA := state.mem (instr.A)
      valB := state.mem (instr.B)
      diff := valB - valA
      newMem := fun n => if n = instr.B then diff else state.mem n
  if diff < 0 then
    { mem := newMem, pc := instr.C }
  else
    { mem := newMem, pc := state.pc + 3 }

/-
  PROOF 1: Memory Invariant
  The value at index B after execution is exactly the difference of B and A.
-/
theorem proof_mem_invariant (s : SubleqState) (i : SubleqInstr) :
  (subleq_step s i).mem (i.B) = s.mem (i.B) - s.mem (i.A) := by
  simp [subleq_step]
  split
  · rfl
  · rfl

/-
  PROOF 2: Control Flow - Branch Taken
  If the difference is negative, the PC must equal the jump target C.
-/
theorem proof_branch_taken (s : SubleqState) (i : SubleqInstr) :
  (s.mem (i.B) - s.mem (i.A) < 0) → (subleq_step s i).pc = i.C := by
  intro h
  simp [subleq_step]
  rw [h]

/-
  PROOF 3: Control Flow - Branch Not Taken
  If the difference is non-negative, the PC must increment by 3.
-/
theorem proof_branch_not_taken (s : SubleqState) (i : SubleqInstr) :
  ¬(s.mem (i.B) - s.mem (i.A) < 0) → (subleq_step s i).pc = s.pc + 3 := by
  intro h
  simp [subleq_step]
  rw [h]
