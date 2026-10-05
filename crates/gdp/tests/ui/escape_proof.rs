use gdp::{define_proof, name};

enum Admin {}

fn escape() {
    let issuer = define_proof::<Admin>("Admin").unwrap();
    let _proof = name("project", |project| issuer.prove(&project).unwrap());
}
