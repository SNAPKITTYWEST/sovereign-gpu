mod isa;
mod sm;
mod scheduler;
mod qrng;
mod engine;

use clap::Parser;
use std::fs;
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "sovereign-gpu-simulator")]
#[command(about = "Quantum-Tensor RISC processor reference simulator")]
struct Args {
    #[arg(short, long)]
    program: PathBuf,

    #[arg(short, long, default_value = "8")]
    sms: usize,

    #[arg(short, long)]
    entropy: Option<PathBuf>,

    #[arg(short, long)]
    trace: Option<PathBuf>,

    #[arg(long, default_value = "10000")]
    max_cycles: usize,
}

fn main() {
    let args = Args::parse();

    println!("[SIM] Sovereign GPU Simulator");
    println!("[SIM] Program: {:?}", args.program);
    println!("[SIM] SMs: {}", args.sms);
    println!("[SIM] Max cycles: {}", args.max_cycles);

    let program = fs::read(&args.program).expect("Failed to read program");

    let entropy_stream: Vec<u64> = match &args.entropy {
        Some(path) => {
            let data = fs::read(path).expect("Failed to read entropy file");
            data.chunks_exact(8)
                .map(|c| u64::from_le_bytes(c.try_into().unwrap()))
                .collect()
        }
        None => {
            use rand::Rng;
            let mut rng = rand::thread_rng();
            (0..args.max_cycles).map(|_| rng.gen()).collect()
        }
    };

    let mut eng = engine::Engine::new(args.sms, program);
    let mut trace = Vec::new();

    for (cycle, &entropy_word) in entropy_stream.iter().enumerate().take(args.max_cycles) {
        let snapshot = eng.step(entropy_word);

        if let Some(ref path) = args.trace {
            trace.push(snapshot);
        }

        if eng.all_halted() {
            println!("[SIM] All SMs halted at cycle {}", cycle);
            break;
        }
    }

    if let Some(path) = &args.trace {
        let json = serde_json::to_string_pretty(&trace).unwrap();
        fs::write(path, json).expect("Failed to write trace");
        println!("[SIM] Trace written to {:?}", path);
    }

    println!("[SIM] Simulation complete");
    println!("[SIM] Cycles executed: {}", trace.len());
}
