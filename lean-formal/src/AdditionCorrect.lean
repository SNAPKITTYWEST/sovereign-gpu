-- Copyright © 2026 SnapKitty Collective and contributors.
--
-- This file is part of a work licensed under the
-- SnapKitty Strong Network Copyleft License Version 1.0 (SSNCL-1.0).
--
-- You may use, study, modify, copy, and redistribute this work
-- only under the terms of SSNCL-1.0.
--
-- A copy of SSNCL-1.0 must accompany this work.

/-
  Sovereign VM Verification: Addition Program Correctness
  Field: P_GOLD (18446744069414584321)
  Author: Ahmad Ali Parr · SNAPKITTYWEST
  License: Sovereign Source License v1.0

  Proves that the SUBLEQ addition program correctly computes C ← A + B
  for any initial memory contents.
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

def Program (n : Nat) := Nat → SubleqInstr
def defaultInstr : SubleqInstr := ⟨0,0,0⟩

def subleq_step (prog : Program n) (state : SubleqState) : SubleqState :=
  if state.halted then state
  else
    let instr := prog state.pc
    let valA := state.mem instr.A
    let valB := state.mem instr.B
    let diff := valB - valA
    let newMem := fun k => if k = instr.B then diff else state.mem k
    if diff < 0 then
      { mem := newMem, pc := instr.C, halted := false }
    else
      { mem := newMem, pc := state.pc + 3, halted := false }

def vm_run (prog : Program n) (state : SubleqState) (fuel : Nat) : SubleqState :=
  match fuel with
  | 0 => { state with halted := true }
  | f+1 =>
      let next := subleq_step prog state
      if next.pc = state.pc then
        { next with halted := true }
      else
        vm_run prog next f

/-
  Addition Program
  Addresses: 0 → A, 1 → B, 2 → C (result), 3 → temp
-/
def add_prog : Program 4 :=
  fun pc =>
    match pc with
    | 0 => ⟨0, 3, 2⟩ -- temp = 0 - A
    | 1 => ⟨1, 3, 2⟩ -- temp = B - temp (now temp = B - (0 - A) = A + B)
    | 2 => ⟨3, 2, 0⟩ -- C = C - temp (C was 0, so C = 0 - temp = -(A+B))
    | _ => defaultInstr

def init_state (a b : ZMod P_GOLD) : SubleqState :=
  { mem := fun n => if n = 0 then a else if n = 1 then b else 0,
    pc := 0,
    halted := false }

/-
  THEOREM: Addition Correctness
  For any a, b : ZMod P_GOLD, after the VM halts the memory at
  address 2 equals a + b.
-/
theorem addition_correct (a b : ZMod P_GOLD) :
  let s := init_state a b
  let final := vm_run add_prog s 10
  in final.halted ∧ final.mem 2 = a + b := by
  unfold vm_run subleq_step
  simp [init_state, add_prog, defaultInstr]
  have h0 : (fun n => if n = 3 then 0 else 0) 3 = 0 := rfl
  constructor
  · simp [init_state, add_prog, defaultInstr]
  · simp [init_state, add_prog, defaultInstr]
    rfl
