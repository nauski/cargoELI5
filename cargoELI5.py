#!/usr/bin/env python3

import subprocess
import requests
import os
import re
import threading
import time
import random

from termcolor import colored
from openai import OpenAI

client = OpenAI()

temperature=0.2
max_tokens=256
frequency_penalty=0.0

def run_cargo():
    result = subprocess.run(["cargo", "run"], capture_output=True, text=True)
    return result.stdout + result.stderr

def extract_errors(cargo_output):
    # parsing the individual errors into an array
    error_pattern = re.compile(r'error.*?(?=\n(?=error|$))', re.DOTALL)
    matches = error_pattern.findall(cargo_output)

    # filter out the summary error message and empty matches
    errors = [error.strip() for error in matches if "could not compile" not in error]

    return errors

def explain_errors(errors):
    explained_errors = []


    for error in errors:
        query = "Please explain the following in short but very compassionate way, preferably under 50 words, don't print code examples." + error

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": query}],
            temperature=temperature,
            max_tokens=max_tokens,
            frequency_penalty=frequency_penalty
        )

        # extracting the explanation
        explanation = ""
        if response.choices:
            explanation_message = response.choices[0].message
            if explanation_message:
                explanation = explanation_message.content

        # appending the error and its explanation to the array
        explained_errors.append({"error": error, "explanation": explanation})

    
    return explained_errors

def spinner(stop_signal):
    spinner_chars = "|/-\\"
    while not stop_signal.is_set():
        for char in spinner_chars:
            if stop_signal.is_set():
                break
            print(char, end="\r", flush=True)
            time.sleep(0.1)


def display_random_aphorism():

    aphorisms = [
        "The only way to do great work is to love what you do. - Steve Jobs",
        "Life is 10% what happens to us and 90% how we react to it. - Charles R. Swindoll",
        "Do not take life too seriously. You will never get out of it alive. - Elbert Hubbard",
        "To succeed in life, you need two things: ignorance and confidence. - Mark Twain",
    ]
    selected_aphorism = random.choice(aphorisms)
    print(colored("Aphorism while waiting:", 'cyan'))
    print(colored(selected_aphorism, 'cyan'))


def main():
    api_key = os.environ.get("CARGOELI5_API_KEY")
    if not api_key:
        print("Error: CARGOELI5_API_KEY environment variable not set.")
        return

    cargo_output = run_cargo()
    errors = extract_errors(cargo_output)

    if errors:
        display_random_aphorism()
        stop_spinner = threading.Event()
        spinner_thread = threading.Thread(target=spinner, args=(stop_spinner,))
        spinner_thread.start()
        
        explained_errors = explain_errors(errors)
        
        stop_spinner.set()
        spinner_thread.join()
        
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

