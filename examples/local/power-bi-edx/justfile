default:
    echo "Hello, Justfile!"

trim_rows csvfile csvout:
    tail -n +4 {{csvfile}} | head -n -5 | {{csvfile}} > {{csvout}}
