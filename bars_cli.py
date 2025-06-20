import subprocess

# Loads the instruction
with open("bars_system_prompt.txt", "r", encoding="utf-8") as f:
    system_prompt = f.read()

# Load Bars memory
with open("bars_chat_history.txt", "r", encoding="utf-8") as f:
    memory = f.read()

with open("test_code.txt", "r") as f:
    code = f.read()

# Chat loop
print("🧠 Bars is online (phi model)")
while True:
    user_input = input("You > ")
    if user_input.lower() in ['exit', 'quit']:
        break

    # Merge memory + user input
    full_prompt = (
        f"{system_prompt}\n\n"
        f"{memory}\n\n"
        f"{code}\n\n"
        f"Aditya: {user_input}\n"
        f"Bars:"
    )

    # Run phi with prompt
    process = subprocess.Popen(
        ["ollama", "run", "llama3.2"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    output, error = process.communicate(input=full_prompt)
    print(f"Bars > {output.strip()}")
