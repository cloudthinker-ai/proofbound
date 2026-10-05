use gdp::{define_proof, name2};

enum Admin {}

fn mismatch() {
    let issuer = define_proof::<Admin>("Admin").unwrap();
    name2("project", "project", |a, b| {
        let proof = issuer.prove(&a).unwrap();
        issuer.verifier().require(&proof, &b).unwrap();
    });
}
