ROOT := justfile_directory()
SRC := ROOT + "/src/py_num_bench/implementations"

# Default list recipe
default:
    @just --list

# Run the benchmark (main)
bench:
    uv run src/py_num_bench/main.py


# Setup the py-num-bench project
create-structure:
    mkdir -p src/py_num_bench/implementations/python
    mkdir -p src/py_num_bench/implementations/cython
    mkdir -p src/py_num_bench/implementations/c
    mkdir -p src/py_num_bench/implementations/cpp
    mkdir -p src/py_num_bench/implementations/rust/sieve_rs/src
    mkdir -p src/py_num_bench/implementations/rust/trapezoid_rs/src
    touch src/py_num_bench/__init__.py
    touch src/py_num_bench/core.py
    touch src/py_num_bench/main.py
    touch src/py_num_bench/implementations/__init__.py
    touch src/py_num_bench/implementations/python/__init__.py
    touch src/py_num_bench/implementations/cython/__init__.py
    touch src/py_num_bench/implementations/python/sieve.py
    touch src/py_num_bench/implementations/python/trapezoid.py
    touch src/py_num_bench/implementations/cython/sieve_cython.pyx
    touch src/py_num_bench/implementations/cython/trapezoid_cython.pyx
    touch src/py_num_bench/implementations/cython/setup.py
    touch src/py_num_bench/implementations/c/sieve.c
    touch src/py_num_bench/implementations/c/trapezoid.c
    touch src/py_num_bench/implementations/cpp/sieve.cpp
    touch src/py_num_bench/implementations/cpp/trapezoid.cpp
    touch src/py_num_bench/implementations/rust/sieve_rs/Cargo.toml
    touch src/py_num_bench/implementations/rust/sieve_rs/src/lib.rs
    touch src/py_num_bench/implementations/rust/trapezoid_rs/Cargo.toml
    touch src/py_num_bench/implementations/rust/trapezoid_rs/src/lib.rs

# Build C shared libs
build-c:
    gcc -O3 -fPIC -shared -o {{SRC}}/c/libsieve.so {{SRC}}/c/sieve.c
    gcc -O3 -fPIC -shared -o {{SRC}}/c/libtrapezoid.so {{SRC}}/c/trapezoid.c

# Build C++ shared libs
build-cpp:
    g++ -O3 -fPIC -shared -o {{SRC}}/cpp/libsieve_cpp.so {{SRC}}/cpp/sieve.cpp
    g++ -O3 -fPIC -shared -o {{SRC}}/cpp/libtrapezoid_cpp.so {{SRC}}/cpp/trapezoid.cpp

# Build Rust shared libs
build-rust:
    cd {{SRC}}/rust/sieve_rs && cargo build --release
    cp {{SRC}}/rust/sieve_rs/target/release/libsieve_rs.dylib {{SRC}}/rust/
    cd {{SRC}}/rust/trapezoid_rs && cargo build --release
    cp {{SRC}}/rust/trapezoid_rs/target/release/libtrapezoid_rs.dylib {{SRC}}/rust/


# Build Cython
build-cython:
    cd {{SRC}}/cython && uv run setup.py build_ext --inplace

# Clean artifacts
clean:
    rm -f {{SRC}}/c/*.so {{SRC}}/cpp/*.so {{SRC}}/rust/*.dylib {{SRC}}/cython/*.so
    rm -rf {{SRC}}/cython/build

    # Clean Rust build artifacts via cargo clean for each Rust crate
    cd {{SRC}}/rust/sieve_rs && cargo clean
    cd {{SRC}}/rust/trapezoid_rs && cargo clean

# Convenience meta-targets
build-all: build-c build-cpp build-rust build-cython

# Show the root directory
show-root:
    @echo {{ROOT}}

# Show the src directory
show-src:
    @echo {{SRC}}
