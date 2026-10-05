use gdp::{Identity, Named, Proof, name};

enum Admin {}

fn sensitive<'a>(_project: &Named<'a, &str>, _proof: &Proof<Admin, Identity<'a>>) {}

fn omission() {
    name("project", |project| sensitive(&project));
}
