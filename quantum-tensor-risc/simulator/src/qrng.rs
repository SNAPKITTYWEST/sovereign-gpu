use serde::{Deserialize, Serialize};

pub const DOMAIN: u64 = 0x5A5A5A5A;
pub const PROC_ID: u64 = 0x01;
pub const PROG_HASH: u64 = 0xDEADBEEF;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QRNGState {
    pub seed: u64,
    pub epoch: u64,
    pub buf: Vec<u64>,
}

impl QRNGState {
    pub fn new(initial_entropy: u64) -> Self {
        let seed = Self::qseed(initial_entropy, 0);
        QRNGState {
            seed,
            epoch: 0,
            buf: Vec::new(),
        }
    }

    pub fn qseed(entropy: u64, epoch: u64) -> u64 {
        use std::collections::hash_map::DefaultHasher;
        use std::hash::{Hash, Hasher};

        let mut hasher = DefaultHasher::new();
        entropy.hash(&mut hasher);
        DOMAIN.hash(&mut hasher);
        PROC_ID.hash(&mut hasher);
        PROG_HASH.hash(&mut hasher);
        256u64.hash(&mut hasher); // TENSOR_M
        256u64.hash(&mut hasher); // TENSOR_K
        256u64.hash(&mut hasher); // TENSOR_N
        epoch.hash(&mut hasher);
        hasher.finish()
    }

    pub fn fluctuation_sample(seed: u64, t: u64) -> u64 {
        seed.wrapping_mul(6364136223846793005)
            .wrapping_add(t.wrapping_mul(1442695040888963407))
    }

    pub fn read(&mut self) -> u64 {
        if self.buf.is_empty() {
            let word = Self::fluctuation_sample(self.seed, self.epoch);
            self.epoch += 1;
            word
        } else {
            self.buf.remove(0)
        }
    }

    pub fn push(&mut self, word: u64) {
        self.buf.push(word);
    }
}
