use std::env;
use std::error::Error;
use std::fs;
use std::hint::black_box;
use std::time::Instant;

use gdp::runtime::{Name, ProofError, Prover, Scope};

enum Benchmark {}

struct Sample {
    wall_ns: u128,
    cpu_ns: u128,
    checksum: u32,
}

fn cpu_time() -> Result<u128, Box<dyn Error>> {
    let source = fs::read_to_string("/proc/self/schedstat")?;
    Ok(source
        .split_whitespace()
        .next()
        .ok_or("Missing scheduler CPU time")?
        .parse()?)
}

fn batch(
    iterations: u64,
    operation: &mut impl FnMut(u32) -> Result<u32, ProofError>,
) -> Result<u32, ProofError> {
    let mut checksum = 0_u32;
    for index in 0..iterations {
        let value = black_box((index & 1023) as u32);
        checksum = checksum.wrapping_add(black_box(operation(value)?));
    }
    Ok(black_box(checksum))
}

fn measure(
    iterations: u64,
    mut operation: impl FnMut(u32) -> Result<u32, ProofError>,
) -> Result<Sample, Box<dyn Error>> {
    for _ in 0..2 {
        black_box(batch(iterations, &mut operation)?);
    }
    let cpu = cpu_time()?;
    let start = Instant::now();
    let checksum = batch(iterations, &mut operation)?;
    let wall_ns = start.elapsed().as_nanos();
    let cpu_ns = cpu_time()?.saturating_sub(cpu);
    Ok(Sample {
        wall_ns,
        cpu_ns,
        checksum,
    })
}

fn check_runtime_contract() -> Result<(), Box<dyn Error>> {
    let scope = Scope::new();
    let subjects = [scope.name()?, scope.name()?];
    let issuer = Prover::new("Benchmark")?;
    let verifier = issuer.verifier();
    let proof = issuer.prove(&subjects)?;
    verifier.require(&proof, &subjects)?;
    assert_eq!(
        verifier.require(&proof, &[subjects[1].clone(), subjects[0].clone()]),
        Err(ProofError::WrongSubjects)
    );
    let other = Prover::new("Benchmark")?;
    assert_eq!(
        verifier.require(&other.prove(&subjects)?, &subjects),
        Err(ProofError::WrongKind)
    );
    scope.close();
    assert_eq!(
        verifier.require(&proof, &subjects),
        Err(ProofError::ClosedScope)
    );
    Ok(())
}

fn run(case: &str, iterations: u64) -> Result<Sample, Box<dyn Error>> {
    let issuer = Prover::new("Benchmark")?;
    match case {
        "baseline" => measure(iterations, Ok),
        "name1" => measure(iterations, |value| {
            Ok(gdp::name(value, |named| *black_box(&named).value()))
        }),
        "name2" => measure(iterations, |value| {
            Ok(gdp::name2(value, 17_u32, |first, second| {
                *black_box(&first).value() + *black_box(&second).value()
            }))
        }),
        "name3" => measure(iterations, |value| {
            Ok(gdp::name3(value, 17_u32, 42_u32, |first, second, third| {
                *black_box(&first).value()
                    + *black_box(&second).value()
                    + *black_box(&third).value()
            }))
        }),
        "prove0" | "prove1" | "prove2" | "prove3" => {
            let count: usize = case[5..].parse()?;
            let subjects: Vec<_> = (0..count).map(|_| Name::fresh()).collect();
            let mut last = None;
            let sample = measure(iterations, |value| {
                let proof = black_box(issuer.prove(black_box(&subjects))?);
                let result = value ^ proof.kind().len() as u32;
                last = Some(proof);
                Ok(result)
            })?;
            black_box(&last);
            Ok(sample)
        }
        "typed_prove2" => {
            let issuer = gdp::define_proof::<Benchmark>("Benchmark")?;
            gdp::name2(1_u32, 7_u32, |user, project| {
                let mut last = None;
                let sample = measure(iterations, |value| {
                    let proof = black_box(issuer.prove((black_box(&user), black_box(&project)))?);
                    let result = value ^ proof.kind().len() as u32;
                    last = Some(proof);
                    Ok(result)
                })?;
                black_box(&last);
                Ok(sample)
            })
        }
        "runtime_require2" => {
            let subjects = [Name::fresh(), Name::fresh()];
            let proof = issuer.prove(&subjects)?;
            let verifier = issuer.verifier();
            measure(iterations, |value| {
                verifier.require(black_box(&proof), black_box(&subjects))?;
                Ok(value ^ 7)
            })
        }
        "typed_require2" => {
            let issuer = gdp::define_proof::<Benchmark>("Benchmark")?;
            let verifier = issuer.verifier();
            gdp::name2(1_u32, 7_u32, |user, project| {
                let proof = issuer.prove((&user, &project))?;
                measure(iterations, |value| {
                    verifier.require(black_box(&proof), (black_box(&user), black_box(&project)))?;
                    Ok(value ^ *black_box(&project).value())
                })
            })
        }
        "typed_flow2" => {
            let issuer = gdp::define_proof::<Benchmark>("Benchmark")?;
            let verifier = issuer.verifier();
            measure(iterations, |value| {
                gdp::name2(value, 17_u32, |user, project| {
                    let proof = black_box(issuer.prove((&user, &project))?);
                    verifier.require(black_box(&proof), (black_box(&user), black_box(&project)))?;
                    Ok(*black_box(&user).value() + *black_box(&project).value())
                })
            })
        }
        "runtime_scope_flow2" => {
            let verifier = issuer.verifier();
            measure(iterations, |value| {
                let scope = Scope::new();
                let subjects = [scope.name()?, scope.name()?];
                let proof = black_box(issuer.prove(black_box(&subjects))?);
                verifier.require(black_box(&proof), black_box(&subjects))?;
                scope.close();
                Ok(value + 17)
            })
        }
        _ => Err("Unknown core benchmark case".into()),
    }
}

fn main() -> Result<(), Box<dyn Error>> {
    let mut arguments = env::args().skip(1);
    let case = arguments.next().ok_or("Expected a benchmark case")?;
    let iterations: u64 = arguments
        .next()
        .ok_or("Expected iteration count")?
        .parse()?;
    if iterations == 0 || arguments.next().is_some() {
        return Err("Expected a positive iteration count and no extra arguments".into());
    }
    check_runtime_contract()?;
    let sample = run(&case, iterations)?;
    println!(
        "{{\"case\":\"{}\",\"iterations\":{},\"wall_ns\":{},\"cpu_ns\":{},\"checksum\":{},\"runtime_contract\":\"PASS\"}}",
        case, iterations, sample.wall_ns, sample.cpu_ns, sample.checksum
    );
    Ok(())
}
