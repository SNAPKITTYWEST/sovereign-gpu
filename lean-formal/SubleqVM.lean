/-
  Sovereign VM Implementation: SUBLEQ Recursive Execution Engine
  Field: P_GOLD (18446744069414584321)
  Author: Ahmad Ali Parr · SNAPKITTYWEST
  License: Sovereign Source License v1.0
-/

import Mathlib.Data.ZMod.Basic

def P_GOLD : Nat := 18446744069414584321
def Memory := Nat → ZMod P_GOLD

structure SubleqState where
  mem : Memory
  pc : Nat
  halted : Bool

structure SubleqInstr where
  A : Nat
  B : Nat
  C : Nat

def Program := Nat → SubleqInstr

def subleq_step (prog : Program) (state : SubleqState) : SubleqState :=
  if state.halted then state
  else
    let instr := prog (state.pc)
    let valA := state.mem (instr.A)
    let valB := state.mem (instr.B)
    let diff := valB - valA
    let newMem := fun n => if n = instr.B then diff else state.mem n
    if diff < 0 then
      { mem := newMem, pc := instr.C, halted := false }
    else
      { mem := newMem, pc := state.pc + 3, halted := false }

/-
  VM Execution Engine with Fuel to guarantee termination
  and avoid 'sorry' in recursive proofs.
-/
def vm_run (prog : Program) (state : SubleqState) (fuel : Nat) : SubleqState :=
  match fuel with
  | 0 => { state with halted := true }
  | f + 1 =>
      let next_state := subleq_step prog state
      if next_state.pc = state.pc then
        { next_state with halted := true }
      else
        vm_run prog next_state f

/-
  PROOF 4: Fuel Exhaustion
  Ensures that the VM always terminates regardless of the program.
-/
theorem proof_vm_terminates (prog : Program) (s : SubleqState) (f : Nat) :
  (vm_run prog s f).halted = true ∨ (f = 0) := by
  induction f with
  | zero => rfl
  | succ f ih =>
      simp [vm_run]
      split
      · rfl
      · split
        · rfl
        · apply ih
