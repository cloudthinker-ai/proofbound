use gdp::{Identity, Proof};

enum Admin {}

fn forge() {
    let _proof = Proof::<Admin, Identity<'static>> {};
}
