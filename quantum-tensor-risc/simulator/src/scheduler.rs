use serde::{Deserialize, Serialize};

pub const MAX_PRIO: u32 = 7;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum SchedEvt {
    Spawn(u32),
    Join(u32),
    Barrier(u32),
    Sync,
    None,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Task {
    pub label: u32,
    pub prio: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SchedState {
    pub pending_tasks: Vec<Task>,
    pub barrier_cnt: std::collections::HashMap<u32, u32>,
    pub sm_count: usize,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Action {
    Run(usize),
    Spawn(u32),
    Join(u32),
    BarrierRelease(u32),
    Sync,
    NoOp,
}

impl SchedState {
    pub fn new(sm_count: usize) -> Self {
        SchedState {
            pending_tasks: Vec::new(),
            barrier_cnt: std::collections::HashMap::new(),
            sm_count,
        }
    }

    pub fn valid_actions(&self, halted: &[bool]) -> Vec<Action> {
        let mut actions: Vec<Action> = Vec::new();

        for i in 0..self.sm_count {
            if i < halted.len() && !halted[i] {
                actions.push(Action::Run(i));
            }
        }

        if !self.pending_tasks.is_empty() {
            let max_p = self.pending_tasks.iter().map(|t| t.prio).max().unwrap_or(0);
            for t in &self.pending_tasks {
                if t.prio == max_p {
                    actions.push(Action::Spawn(t.label));
                }
            }
        }

        for (&id, &cnt) in &self.barrier_cnt {
            if cnt == self.sm_count as u32 {
                actions.push(Action::BarrierRelease(id));
            }
        }

        actions.push(Action::NoOp);
        actions
    }

    pub fn map_action(&self, q: u64, halted: &[bool]) -> Action {
        let actions = self.valid_actions(halted);
        if actions.is_empty() {
            return Action::NoOp;
        }
        let idx = (q as usize) % actions.len();
        actions[idx]
    }

    pub fn apply(&mut self, action: Action) {
        match action {
            Action::Spawn(label) => {
                self.pending_tasks.retain(|t| t.label != label);
            }
            Action::BarrierRelease(id) => {
                self.barrier_cnt.insert(id, 0);
            }
            _ => {}
        }
    }
}
