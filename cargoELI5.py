#!/usr/bin/env python3

import subprocess
import os
import json
import requests
import re

import os
import wandb
from termcolor import colored
from openai import OpenAI

client = OpenAI()

gpt_assistant_prompt = "You are an expert Rust developer" 
gpt_user_prompt = "Explain these errors to me like I'm 5" 
gpt_prompt = gpt_assistant_prompt, gpt_user_prompt
    
#message=[{"role": "assistant", "content": gpt_assistant_prompt}, {"role": "user", "content": gpt_user_prompt}]
temperature=0.2
max_tokens=256
frequency_penalty=0.0

def read_settings():
    with open('settings.json', 'r') as file:
        return json.load(file)

def run_cargo():
    result = subprocess.run(["cargo", "run"], capture_output=True, text=True)
    return result.stdout + result.stderr

def extract_errors(cargo_output):
    # Regular expression to capture individual error messages
    error_pattern = re.compile(r'error.*?(?=\n(?=error|$))', re.DOTALL)
    matches = error_pattern.findall(cargo_output)

    # Filter out the summary error message and empty matches
    errors = [error.strip() for error in matches if "could not compile" not in error]

    return errors

def explain_errors(errors):
    explained_errors = []

    for error in errors:
        # Construct the query for ChatGPT
        query = "Please explain the following in short, preferably under 50 words, also don't print code examples." + error

        # Send the query to ChatGPT and get the explanation
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": query}],
            temperature=temperature,
            max_tokens=max_tokens,
            frequency_penalty=frequency_penalty
        )

        # Extract the explanation
        explanation = ""
        if response.choices:
            explanation_message = response.choices[0].message
            if explanation_message:
                explanation = explanation_message.content

        # Append the error and its explanation to the array
        explained_errors.append({"error": error, "explanation": explanation})

    return explained_errors


def main():
    settings = read_settings()
    api_key = os.environ.get("CARGOELI5_API_KEY")
    if not api_key:
        print("Error: CARGOELI5_API_KEY environment variable not set.")
        return

    cargo_output = run_cargo()
    errors = extract_errors(cargo_output)

    if errors:
        explained_errors = explain_errors(errors)
        for explained_error in explained_errors:
            print(colored("\nError:", 'red'))
            print(explained_error['error'])
            print(colored("\nExplanation:", 'green'))
            print(explained_error['explanation'])
            print(colored("\n" + "-" * 40 + "\n", 'yellow'))
    else:
        print("No errors found.")

if __name__ == "__main__":
    main()

