use gdp::{define_proof, name};

enum Admin {}
enum Plan {}

fn mismatch() {
    let admin = define_proof::<Admin>("Admin").unwrap();
    let plan = define_proof::<Plan>("Plan").unwrap();
    name("project", |project| {
        let proof = admin.prove(&project).unwrap();
        plan.verifier().require(&proof, &project).unwrap();
    });
}
