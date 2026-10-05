use std::path::Path;
use std::process::Command;

use gdp as _;

#[test]
fn invalid_contracts_do_not_compile() {
    let executable = std::env::current_exe().unwrap();
    let dependencies = executable.parent().unwrap();
    let library = std::fs::read_dir(dependencies)
        .unwrap()
        .filter_map(Result::ok)
        .map(|entry| entry.path())
        .find(|path| {
            path.file_name()
                .unwrap()
                .to_string_lossy()
                .starts_with("libgdp-")
                && path.extension().is_some_and(|ext| ext == "rlib")
        })
        .unwrap();
    let fixtures = Path::new(env!("CARGO_MANIFEST_DIR")).join("tests/ui");
    for fixture in std::fs::read_dir(fixtures).unwrap().map(Result::unwrap) {
        let result = Command::new("rustc")
            .arg("--edition=2024")
            .arg("--crate-type=lib")
            .arg("--emit=metadata")
            .arg("--extern")
            .arg(format!("gdp={}", library.display()))
            .arg("-L")
            .arg(format!("dependency={}", dependencies.display()))
            .arg("--out-dir")
            .arg(dependencies)
            .arg(fixture.path())
            .output()
            .unwrap();
        let diagnostic = String::from_utf8_lossy(&result.stderr);
        assert!(
            !result.status.success(),
            "{} unexpectedly compiled",
            fixture.path().display()
        );
        assert!(!diagnostic.contains("can't find crate"), "{diagnostic}");
        assert!(!diagnostic.contains("unresolved import"), "{diagnostic}");
        assert!(
            diagnostic.contains("mismatched types")
                || diagnostic.contains("lifetime")
                || diagnostic.contains("private")
                || diagnostic.contains("argument"),
            "{diagnostic}"
        );
    }
}
