use gdp::runtime::{self, ProofError};
use gdp::{define_proof, name, name2, name3};

enum Admin {}
enum Plan {}

#[test]
fn typed_contract_accepts_exact_subjects_and_independent_facts() {
    let admin = define_proof::<Admin>("Admin").unwrap();
    let impostor = define_proof::<Admin>("Admin").unwrap();
    let plan = define_proof::<Plan>("Plan").unwrap();
    let result = name2("user", "project", |user, project| {
        let admin_proof = admin.prove((&user, &project)).unwrap();
        let plan_proof = plan.prove(&project).unwrap();
        let foreign_proof = impostor.prove((&user, &project)).unwrap();
        assert_eq!(
            admin.verifier().require(&foreign_proof, (&user, &project)),
            Err(ProofError::WrongKind)
        );
        admin
            .verifier()
            .require(&admin_proof, (&user, &project))
            .unwrap();
        plan.verifier().require(&plan_proof, &project).unwrap();
        format!("{}:{}", user.value(), project.value())
    });
    assert_eq!(result, "user:project");
    name3(1, 2, 3, |a, b, c| {
        let proof = admin.prove((&a, &b, &c)).unwrap();
        assert_eq!(admin.verifier().require(&proof, (&a, &b, &c)), Ok(()));
    });
    name("one", |value| {
        let proof = plan.prove(&value).unwrap();
        assert_eq!(proof.kind(), "Plan");
    });
}

#[test]
fn dynamic_contract_rejects_wrong_issuer_order_identity_and_arity() {
    let authority = runtime::Prover::new("Admin").unwrap();
    let impostor = runtime::Prover::new("Admin").unwrap();
    let user = runtime::Name::fresh();
    let project = runtime::Name::fresh();
    let other = runtime::Name::fresh();
    let proof = authority.prove(&[user.clone(), project.clone()]).unwrap();
    let verifier = authority.verifier();
    assert_eq!(
        verifier.require(&proof, &[user.clone(), project.clone()]),
        Ok(())
    );
    assert_eq!(
        verifier.require(&proof, &[project.clone(), user.clone()]),
        Err(ProofError::WrongSubjects)
    );
    assert_eq!(
        verifier.require(&proof, &[user.clone(), other]),
        Err(ProofError::WrongSubjects)
    );
    assert_eq!(
        verifier.require(&proof, &[user]),
        Err(ProofError::WrongSubjects)
    );
    assert_eq!(
        impostor.verifier().require(&proof, &[project]),
        Err(ProofError::WrongKind)
    );
}

#[test]
fn closed_scopes_reject_existing_proofs_and_new_names() {
    let authority = runtime::Prover::new("Admin").unwrap();
    let scope = runtime::Scope::new();
    let value = scope.name().unwrap();
    let proof = authority.prove(std::slice::from_ref(&value)).unwrap();
    scope.close();
    scope.close();
    assert!(matches!(scope.name(), Err(ProofError::ClosedScope)));
    assert_eq!(
        authority
            .verifier()
            .require(&proof, std::slice::from_ref(&value)),
        Err(ProofError::ClosedScope)
    );
    assert!(matches!(
        authority.prove(&[value]),
        Err(ProofError::ClosedScope)
    ));
}

#[test]
fn contracts_are_thread_safe_and_errors_are_value_free() {
    let scope = runtime::Scope::new();
    let value = scope.name().unwrap();
    let authority = runtime::Prover::new("Admin").unwrap();
    let proof = authority.prove(std::slice::from_ref(&value)).unwrap();
    let verifier = authority.verifier();
    let thread_scope = scope.clone();
    std::thread::spawn(move || thread_scope.close())
        .join()
        .unwrap();
    assert_eq!(
        verifier.require(&proof, &[value]),
        Err(ProofError::ClosedScope)
    );
    for kind in ["", "private-secret!", "9bad", "α", &"a".repeat(129)] {
        let error = runtime::Prover::new(kind).err().unwrap();
        assert_eq!(error, ProofError::InvalidKind);
        assert!(!error.to_string().contains("private-secret"));
    }
    let names: Vec<_> = (0..=runtime::MAX_SUBJECTS)
        .map(|_| runtime::Name::fresh())
        .collect();
    assert!(authority.prove(&names[..runtime::MAX_SUBJECTS]).is_ok());
    assert!(matches!(
        authority.prove(&names),
        Err(ProofError::TooManySubjects)
    ));
    let global_proof = authority.prove(&[]).unwrap();
    assert_eq!(verifier.require(&global_proof, &[]), Ok(()));
}
