use cbindgen;
use std::path::Path;
use cargo_metadata::{MetadataCommand, CargoOpt};

fn main() {
    let metadata = MetadataCommand::new()
        .manifest_path("./Cargo.toml")
        .features(CargoOpt::AllFeatures)
        .exec()
        .unwrap();
    let cavc_ffi_package =
        metadata.packages.iter().find(|&p| p.name == "cavalier_contours_ffi")
        .unwrap();
    let cavc_ffi_path = cavc_ffi_package.manifest_path.parent().unwrap();

    // Generate bindings from both the upstream FFI crate and our local extensions
    let bindings = cbindgen::Builder::new()
        .with_no_includes()
        .with_language(cbindgen::Language::C)
        .with_crate(cavc_ffi_path)
        .with_src("src/lib.rs")
        .generate()
        .unwrap();
    bindings.write_to_file(Path::new("target").join("header.h"));
}
