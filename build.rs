use std::ffi::OsStr;
use std::path::{Path, PathBuf};

use cargo_metadata::{CargoOpt, MetadataCommand};

fn target_dir_from_out_dir(out_dir: &Path, target: &OsStr) -> PathBuf {
    // OUT_DIR is either:
    //   <target-dir>/<profile>/build/<package-hash>/out
    // or, when --target is used:
    //   <target-dir>/<target-triple>/<profile>/build/<package-hash>/out
    let profile_dir = out_dir
        .ancestors()
        .nth(3)
        .expect("Cargo OUT_DIR did not contain the expected profile directory");
    let profile_parent = profile_dir
        .parent()
        .expect("Cargo profile directory did not have a parent");

    if profile_parent.file_name() == Some(target) {
        profile_parent
            .parent()
            .expect("Cargo target-triple directory did not have a parent")
            .to_path_buf()
    } else {
        profile_parent.to_path_buf()
    }
}

fn main() {
    println!("cargo:rerun-if-changed=Cargo.toml");
    println!("cargo:rerun-if-changed=src/lib.rs");
    println!("cargo:rerun-if-env-changed=CARGO_TARGET_DIR");

    let metadata = MetadataCommand::new()
        .manifest_path("./Cargo.toml")
        .features(CargoOpt::AllFeatures)
        .exec()
        .unwrap();
    let cavc_ffi_package = metadata
        .packages
        .iter()
        .find(|&p| p.name == "cavalier_contours_ffi")
        .unwrap();
    let cavc_ffi_path = cavc_ffi_package.manifest_path.parent().unwrap();
    let out_dir = PathBuf::from(std::env::var_os("OUT_DIR").expect("Cargo did not set OUT_DIR"));
    let target = std::env::var_os("TARGET").expect("Cargo did not set TARGET");
    let header_path = target_dir_from_out_dir(&out_dir, &target).join("header.h");

    // Generate bindings from both the upstream FFI crate and our local extensions
    let bindings = cbindgen::Builder::new()
        .with_no_includes()
        .with_language(cbindgen::Language::C)
        .with_crate(cavc_ffi_path)
        .with_src("src/lib.rs")
        .generate()
        .unwrap();
    bindings.write_to_file(header_path);
}
