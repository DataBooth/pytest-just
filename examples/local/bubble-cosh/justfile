default:
    @just --list

# Run the original bubble-cosh code
run-original-code:
    python bubble-cosh.py 

# Run new class-based bubble-cosh code (with input parameters)
run-new-code diameter="1.068" length="0.6":
    python community/bubble_cosh_databooth.py {{diameter}} {{length}}

# Edit the Marimo notebook version of bubble-cosh 
mo-edit:
    marimo edit community/bubble_cosh_databooth_mo.py

# Run the Marimo notebook version of bubble-cosh 
mo-run:
    marimo run community/bubble_cosh_databooth_mo.py