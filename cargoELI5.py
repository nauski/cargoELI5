import subprocess
import os
import json
import requests
import re

import os
import wandb
from openai import OpenAI

client = OpenAI()

gpt_assistant_prompt = "You are an expert Rust developer" 
gpt_user_prompt = "Explain these errors to me like I'm 5" 
gpt_prompt = gpt_assistant_prompt, gpt_user_prompt
    
message=[{"role": "assistant", "content": gpt_assistant_prompt}, {"role": "user", "content": gpt_user_prompt}]
temperature=0.2
max_tokens=256
frequency_penalty=0.0

def read_settings():
    with open('settings.json', 'r') as file:
        return json.load(file)

def run_cargo():
    result = subprocess.run(["cargo", "run"], capture_output=True, text=True)
    return result.stdout + result.stderr

#def extract_errors(cargo_output):
#    # Regular expression to capture multiline error messages
#    error_pattern = re.compile(r'error:.*?(?=\n\n|\Z)', re.DOTALL)
#    errors = error_pattern.findall(cargo_output)
#    return [error.strip() for error in errors]

def extract_errors(cargo_output):
    # Regular expression to capture individual error messages
    error_pattern = re.compile(r'error:.*?(?=\n\nerror:|\n\nFor more information about this error, try|\Z)', re.DOTALL)
    errors = error_pattern.findall(cargo_output)

    # Filter out the summary error message and empty matches
    filtered_errors = [error.strip() for error in errors if "could not compile" not in error and error.strip()]

    return filtered_errors


def explain_errors(errors):
    query = ""
    for ele in errors:
        query += ele

    # Updating the user message content with the query
    message[1]["content"] = gpt_user_prompt + "\n\n" + query

    response = client.chat.completions.create(
        model="gpt-4",
        messages=message,
        temperature=temperature,
        max_tokens=max_tokens,
        frequency_penalty=frequency_penalty
    )

    explanations = []

    # Extracting the content from the response
    if response.choices:
        explanation_message = response.choices[0].message
        if explanation_message:
            explanations.append(explanation_message.content)

    return explanations

def main():
    settings = read_settings()
    api_key = os.environ.get("CARGOELI5_API_KEY")
    if not api_key:
        print("Error: CARGOELI5_API_KEY environment variable not set.")
        return

    cargo_output = run_cargo()
    errors = extract_errors(cargo_output)
    if errors:
        explanations = explain_errors(errors)
        for error, explanation in zip(errors, explanations):
            print("\nError Message:")
            print(error)
            print("\nSimplified Explanation:")
            print(explanation)
            print("\n" + "-" * 40 + "\n")
    else:
        print("No errors found.")

if __name__ == "__main__":
    main()

