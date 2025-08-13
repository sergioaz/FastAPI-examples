import subprocess

# Example: 100 requests, 10 concurrent, to http://127.0.0.1:8000//with_pool/{user_id}


cmd = [
    "ab",
    "-n", "1000",
    "-c", "10",
    "http://127.0.0.1:8000/with_pool/1"
]

try:
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    print(result.stdout)
except subprocess.CalledProcessError as e:
    print("Error running ab:", e.stderr)