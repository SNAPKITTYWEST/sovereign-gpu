fn test_scheduler_no_op_always_valid() {
    // PO9: NoOp is always in valid_actions
    let halted = vec![false, false, false, false];
    let sched = scheduler::SchedState::new(4);
    let actions = sched.valid_actions(&halted);
    assert!(actions.contains(&scheduler::Action::NoOp));
}

fn test_scheduler_run_when_active() {
    let halted = vec![false, true, true, true];
    let sched = scheduler::SchedState::new(4);
    let actions = sched.valid_actions(&halted);
    assert!(actions.contains(&scheduler::Action::Run(0)));
}

fn test_scheduler_no_run_when_all_halted() {
    let halted = vec![true, true, true, true];
    let sched = scheduler::SchedState::new(4);
    let actions = sched.valid_actions(&halted);
    assert!(!actions.iter().any(|a| matches!(a, scheduler::Action::Run(_))));
}

fn test_scheduler_spawn() {
    let halted = vec![false, false, false, false];
    let mut sched = scheduler::SchedState::new(4);
    sched.pending_tasks.push(scheduler::Task { label: 0x100, prio: 5 });
    let actions = sched.valid_actions(&halted);
    assert!(actions.contains(&scheduler::Action::Spawn(0x100)));
}

fn test_scheduler_priority() {
    let halted = vec![false, false, false, false];
    let mut sched = scheduler::SchedState::new(4);
    sched.pending_tasks.push(scheduler::Task { label: 0x100, prio: 3 });
    sched.pending_tasks.push(scheduler::Task { label: 0x200, prio: 7 });
    sched.pending_tasks.push(scheduler::Task { label: 0x300, prio: 5 });
    let actions = sched.valid_actions(&halted);
    assert!(actions.contains(&scheduler::Action::Spawn(0x200)));
    assert!(!actions.contains(&scheduler::Action::Spawn(0x100)));
    assert!(!actions.contains(&scheduler::Action::Spawn(0x300)));
}

fn test_scheduler_deterministic() {
    let halted = vec![false, false, false, false];
    let sched = scheduler::SchedState::new(4);
    let a1 = sched.map_action(42, &halted);
    let a2 = sched.map_action(42, &halted);
    assert!(a1 == a2);
}

fn test_scheduler_apply_spawn() {
    let mut sched = scheduler::SchedState::new(4);
    sched.pending_tasks.push(scheduler::Task { label: 0x100, prio: 5 });
    sched.pending_tasks.push(scheduler::Task { label: 0x200, prio: 3 });
    sched.apply(scheduler::Action::Spawn(0x100));
    assert!(sched.pending_tasks.len() == 1);
    assert!(sched.pending_tasks[0].label == 0x200);
}

fn main() {
    test_scheduler_no_op_always_valid();
    test_scheduler_run_when_active();
    test_scheduler_no_run_when_all_halted();
    test_scheduler_spawn();
    test_scheduler_priority();
    test_scheduler_deterministic();
    test_scheduler_apply_spawn();
    println!("All scheduler tests passed!");
}
