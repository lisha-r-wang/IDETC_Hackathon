import os
import json
import sys
from dotenv import load_dotenv
from openai import OpenAI
from collections import defaultdict


# Load .env from the parent directory (adjust path if needed)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../.env'))
#api_key = os.getenv("OPENAI_API_KEY")    

def flatten_json(input_file, output_file):
    """
    Reads a JSON file with structure {page#: {rule#: {page#, rule#, definition:}}}
    and flattens it to {rule#: {page#, rule#, definition:}}.

    Args:
        input_file (str): Path to the input JSON file.
        output_file (str): Path to the output JSON file to save the flattened structure.
    """
    # Step 1: Load the input JSON file
    with open(input_file, 'r') as file:
        data = json.load(file)

    # Step 2: Initialize the flattened structure
    flattened_data = {}

    # Step 3: Iterate through the nested structure to flatten it
    for page, rules in data.items():
        if isinstance(rules, str):
            try:
                rules = json.loads(rules)
            except json.JSONDecodeError:
                print(f"Warning: Could not decode rules for page {page}")
                continue
        for rule, details in rules.items():
            # Add the rule to the flattened structure
            flattened_data[rule] = details

    # Step 4: Write the flattened JSON structure to the output
    with open(output_file, 'w') as file:
        json.dump(flattened_data, file, indent=4)
        print(f"Flattened JSON file saved as {output_file}")


def extract_terms(input_file, output_file):
    """
    This function takes a JSON file as input, processes it to:
    1. Concatenate terms across all pages and keys.
    2. Update rule# and page# into lists where terms are present on multiple pages/keys.
    3. Flatten page# structure since each key is unique.
    4. Add an entry for each term as a key to the JSON structure and write to a new JSON file.

    Arguments:
        input_file (str): Path to the input JSON file.
        output_file (str): Path where the processed JSON will be written.
    """
    # Step 1: Read the input JSON file
    with open(input_file, 'r') as file:
        data = json.load(file)

    # Step 2: Initialize default dictionary to concatenate terms
    concatenated_terms = defaultdict(lambda: {
        "page_number": set(),
        "rule_number": set(),
        "definition": "",
        "terms": "",
        "measurements": ""
    })

    # Step 3: Iterate through pages and keys to concatenate terms
    for page, keys in data.items():
        #print(f'Processing page: {page}, and rules: {keys}')
        if isinstance(keys, str):
            try:
                keys = json.loads(keys)
            except json.JSONDecodeError:
                print(f"Warning: Could not decode page data for page {page}")
                continue
            
        for key, key_data in keys.items():
            page_number = key_data.get("page_number", page)  # Default to current page
            rule_number = key_data.get("rule_number", key)  # Default to key
            terms = key_data.get("terms", {})
            definition = key_data.get("definition", "")

            # Process each term
            for term, term_rule in terms.items():
                concatenated_terms[term]["page_number"].add(page_number)  # Collect all unique pages
                concatenated_terms[term]["rule_number"].add(term_rule)    # Collect all unique rules
                if not concatenated_terms[term]["definition"]:      # Add definition if it doesn't exist
                    concatenated_terms[term]["definition"] = definition
                concatenated_terms[term]["terms"] = term  # Add the raw term name

    # Step 4: Convert `page#` and `rule#` sets to lists for serialization
    for term in concatenated_terms:
        concatenated_terms[term]["page_number"] = list(concatenated_terms[term]["page_number"])
        concatenated_terms[term]["rule_number"] = list(concatenated_terms[term]["rule_number"])

    # Step 5: Modify the original JSON to flatten the structure
    flattened_data = {}
    for page, keys in data.items():
        if isinstance(keys, str):
            try:
                keys = json.loads(keys)
            except json.JSONDecodeError:
                print(f"Warning: Could not decode page data for page {page}")
                continue
            print(f'Processing page: {page}, and rules: {type(keys)}')

        for key, value in keys.items():
            # Get rid of nested `page#` and restructure
            flattened_data[key] = {
                "rule_number": value.get("rule_number", ""),
                "definition": value.get("definition", ""),
                "terms": value.get("terms", {}),
                "measurements": {}
            }

    # Step 6: Add concatenated terms as new entries
    flattened_data.update(concatenated_terms)

    # Step 7: Write the modified data to a new JSON file
    with open(output_file, 'w') as file:
        json.dump(flattened_data, file, indent=4)


def extract_information(input_file, key_to_extract, information_to_extract):
    """
    Extracts specific information based on the input parameters:
    1. If information_to_extract is "definition", it extracts the definition for a given rule number.
    2. If information_to_extract is "rule_numbers", it extracts all associated rule numbers for a given technical term.

    Args:
        input_file (str): Path to the JSON file.
        key_to_extract (str): Rule number or technical term to extract information for.
        information_to_extract (str): Type of information to extract ("definition" or "rule_numbers").

    Returns:
        str or list: The extracted information, or a message if the key is not found or invalid.
    """
    # Step 1: Load the JSON file
    with open(input_file, 'r') as file:
        data = json.load(file)

    # Step 2: Extract definition for a rule number
    if information_to_extract == "definition":
        # Check if the key_to_extract matches any rule number
        if key_to_extract in data:
            # Extract the definition for the given key
            definition = data[key_to_extract].get("definition", "")
            if definition:
                return definition
            else:
                return f"No definition found for key: {key_to_extract}"
        else:
            return f"Key '{key_to_extract}' not found in the JSON file."
        
    # Step 3: Extract rule numbers for a technical term
    elif information_to_extract == "rule_numbers":
        # Check if the key_to_extract matches any term across the JSON
        rule_numbers = []
        for key, value in data.items():
            if isinstance(value, str):
                try:
                    value = json.loads(value)
                except json.JSONDecodeError:
                    print(f"Warning: Could not decode data for key {key}")
                    continue
                print(f'Processing key: {key}, and value: {type(value)}')
            terms = value.get("terms", {})
            if isinstance(terms, str):
                try:
                    terms = json.loads(terms)
                except json.JSONDecodeError:
                    print(f"Warning: Could not decode terms for key {key}")
                    continue
            print(f'Processing key: {key}, and terms: {type(terms)}')
            for term, rule in terms.items():
                if term.lower() == key_to_extract.lower():  # Case-insensitive matching
                    rule_numbers.append(rule)
        return rule_numbers if rule_numbers else f"Technical term '{key_to_extract}' not found in the JSON file."

    # Step 4: Handle invalid information_to_extract values
    else:
        return f"Invalid information_to_extract value: {information_to_extract}. Use 'definition' or 'rule_numbers'."
    
output_file = '../files/processed_rules.json'
output_file_with_terms = '../files/processed_rules_with_terms.json'

extract_terms(output_file, output_file_with_terms)
