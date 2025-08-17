from email.mime import text
import os
import json
import sys
from xml.parsers.expat import model
from dotenv import load_dotenv
from openai import OpenAI
from collections import defaultdict
import pandas as pd


# Load .env from the parent directory (adjust path if needed)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../.env'))
#api_key = os.getenv("OPENAI_API_KEY")    

output_file_with_terms = '../files/processed_rules_with_terms.json'


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



key1 = 'V.1.2'  # Example key to extract
key2 = "rollover stability"

result1 = extract_information(output_file_with_terms, key1, "definition")
print(result1)
result2 = extract_information(output_file_with_terms, key2, "rule_numbers")
print(result2)

def invoke_llm(model, text, prompt):
    """
    Find technical terms in the extracted definitions.
    Args:
        extracted_definitions (dict): The extracted definitions dictionary.
    Returns:
        dict: A dictionary containing the found technical terms.
    """
    # If the input is a string, treat it as a single text block
    text = text.strip()
    #print(context)

    # Initialize the OpenAI client (API key is automatically picked up from OPENAI_API_KEY environment variable)
    client = OpenAI()
    results = {}
     # Define default prompt if none is provided
    if prompt is None:
        prompt = """You are a knowledgeable assistant specializing in technical terms and definitions.
            Your task is to extract key terms from the provided text. Here are some examples of key terms:
            "Aerodynamic, Tractive System, Shutdown System, Accelerator Pedal Position Sensor, Brake Pedal,
            Material properties, material, External Item, Impact Attenuator, Accumulator, Firewall, Powertrain,
            Catch Cans, Thermal Protection, Scatter Shields, Coolant, Butt Joints/Butt Joint, Inertia Switch, Transponder,
            Brake Over Travel Switch, Wiring, Grounded Low Voltage, Grounding, Lighting, Light". After extracting the key terms,
            write them in json format. {terms}: key terms separated by comma in a list
            """

    # Create a chat completion
    try:
        response = client.responses.create(
            model=model,  # Specify the model to use
            input=prompt + "\n\n" + text,  # Combine prompt and context
        )

        # Access and print the model's response
        #print(f'response is {response}')
        results = response.output_text
        print(f"Extracted results are {results}")
        try:
            results_dict = json.loads(results)
            print(f'results_dict is {results_dict}')
        except json.JSONDecodeError:
            print("Warning: Could not decode results as JSON.")
            results_dict = {}

    except Exception as e:
        print(f"An error occurred: {e}")

    return results


def read_csv_to_dataframe_with_filename(file_path):
    """
    Reads a CSV file into a pandas DataFrame and returns both the DataFrame and the file name.

    Args:
        file_path (str): The path to the CSV file.

    Returns:
        tuple: A tuple containing the pandas DataFrame and file name.
               If there's an error, returns an error message and file name.
    """
    try:
        # Read the CSV file into a pandas DataFrame
        df = pd.read_csv(file_path)
        # Extract the file name from the file_path
        file_name = file_path.split('/')[-1]  # Works for both Windows and Unix-style paths
        print(f'extracted file name: {file_name}')
        return df, file_name
    except FileNotFoundError:
        file_name = file_path.split('/')[-1]
        return f"Error: File not found at the specified path '{file_path}'.", file_name


def retrieve_context(model, question):
    """
    Retrieves context relevant to the provided question from the language model.

    Args:
        question (str): The question for which context needs to be retrieved.
        model (object): The LLM (Language Model) instance that supports generating context.

    Returns:
        str: The model-generated context for the question.
    """
    
    prompt = """
    We are a student engineering team designing a vehicle for the FSAE competition. 
    Attached is a question regarding FASE specification. Summarize the quesiton ask
    based on the instructions 
    below and format the output strictly as `{"key_to_extract": [...], "information_to_extract": ...}`.

    Instruction Type 1 (Specific Rule Query):
    - When provided with a rule such as `V.1`, extract the exact text of the rule.
    - Format the output as `{"key_to_extract": "V.1", "information_to_extract": "definition"}`.

    Instruction Type 2 (Term-Based Rule List Query):
    - When provided with search terms, such as `Aerodynamic` or `Aerodynamics`, list all relevant rule numbers separated by commas.
    - Format the output strictly as `{"key_to_extract": ["Aerodynamic", "Aerodynamics"], information_to_extract: "rule_number"}`.

    Important:
    1. Return output only in the required format. No extra words or explanations.
    2. Ensure rules and terms are extracted precisely from the FSAE rules document.

    Examples:

    Input 1:
    What does rule `V.1` state exactly?

    Expected Output 1:
    `{"key_to_extract": "V.1", information_to_extract: "definition"}`

    Input 2:
    List all rules relevant to `Aerodynamic/Aerodynamics`.

    Expected Output 2:
    `{"key_to_extract": ["Aerodynamic", "Aerodynamics"], "information_to_extract": "rule_number"}`
    """
    answer = invoke_llm(model, question, prompt)
    if isinstance(answer, str):
        try:
            answer = json.loads(answer)
        except json.JSONDecodeError:
            print(f"Warning: Could not decode terms for {answer}")
            
    print(f'answer is {answer}')
    key_to_extract = answer.get("key_to_extract")
    information_to_extract = answer.get("information_to_extract")
    print(f'output_file_with_terms is {output_file_with_terms}')
    print(f'key_to_extract is {key_to_extract}, information_to_extract is {information_to_extract}')
    context = extract_information(output_file_with_terms, str(key_to_extract), str(information_to_extract))
    result = {"key_to_extract": key_to_extract, "information_extracted": context}
    print(f'result is {result}')
    return result



def generate_answers_and_update_df(file_path, question_column, llm_model):
    """
    Generates answers for questions in a DataFrame and writes predictions into a new column.

    Args:
        df (pandas.DataFrame): The input DataFrame containing a column with questions.
        question_column (str): The column name in the DataFrame where the questions are stored.
        context (str): The context to provide to the AI model for answering the questions.
        llm_model (object): The AI model or handler to generate predictions (e.g., OpenAI GPT).

    Returns:
        pandas.DataFrame: The updated DataFrame with a new column `[model prediction]`.
    """
    df, filename = read_csv_to_dataframe_with_filename(file_path)
    # Initialize an empty list to store model predictions
    predictions = []
    df_test = df.copy().head(1)  # Create a copy of the DataFrame to avoid modifying the original

    # Iterate through each row of the DataFrame
    for index, row in df_test.iterrows():
        question = row[question_column]
        retrieved_context = retrieve_context(llm_model, question)
        text = f"{retrieved_context}\n{question}"
        prompt = """
                You are an accurate and precise assistant. The user has asked the following question:
                {question}
                To help you respond appropriately, here is the provided context for reference:
                {retrieved_context}

                Instructions:
                1. Use the exact context provided above to form your response for the given key or term.
                2. Your answer **must only include the text from the provided context**, verbatim.
                3. Do not add explanations, preambles, formatting, or any additional text to your response.

                Simply return the exact context related to the key as the answer.

                Example Input:
                - Question: "What does rule V.1 state exactly?"
                - Provided Context: {V.1: "CONFIGURATION\nThe vehicle must be open wheeled and open cockpit (a formula style body) with four wheels."}

                Example Output:
                "CONFIGURATION\nThe vehicle must be open wheeled and open cockpit (a formula style body) with four wheels"""

        # Generate model prediction
        try:
            prediction = invoke_llm(llm_model, text, prompt=prompt)
        except Exception as e:
            prediction = f"Error: {e}"

        # Append the prediction to the list
        predictions.append(prediction)

        # Optionally print progress
        print(f"Row {index}: Question: {question} | Prediction: {prediction}")

    # Add the predictions as a new column in the DataFrame
    df['model prediction'] = predictions
    file_path = "../eval/"
    new_filename = file_path + f"{filename}_{llm_model}.csv"
    # Save the DataFrame to CSV
    df.to_csv(new_filename, index=False)  # Save without the row indices
    print(f"DataFrame successfully saved to '{new_filename}'")

    return df


file_path = '../../dataset/rule_extraction/rule_retrieval_qa.csv'
df, filename = read_csv_to_dataframe_with_filename(file_path)

# Process the DataFrame with the questions and update it with predictions
updated_df = generate_answers_and_update_df(file_path=file_path, question_column="question", llm_model='gpt-5-nano')

# Print updated DataFrame
print(updated_df['model prediction'])


"""
python eval/full_evaluation.py --path_to_retrieval eval/rule_extraction/retrieval_evaluation_gpt-4-1106-vision-preview.csv --path_to_compilation eval/rule_extraction/compilation_evaluation_gpt-4-1106-vision-preview.csv --path_to_definition eval/rule_comprehension/definition_evaluation_gpt-4-1106-vision-preview.csv --path_to_presence eval/rule_comprehension/presence_evaluation_gpt-4-1106-vision-preview.csv --path_to_dimension eval/rule_compliance/dimension_context_evaluation_gpt-4-1106-vision-preview.csv --path_to_functional_performance eval/rule_compliance/dimension_functional_performance_evaluation_gpt-4-1106-vision-preview.csv
"""

"""
retrying llama_index.llms.openai.base.OpenAI._chat in 1.0 seconds as it raised RateLimitError: 
Error code: 429 - {'error': {'message': 'Request too large for gpt-4-turbo-preview in organization 
org-beMasKKpVbaaCH4QeDDChZaF on tokens per min (TPM): Limit 30000, Requested 78891. The input or 
output tokens must be reduced in order to run successfully. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}.
"""

