import os
import re
from dotenv import load_dotenv


load_dotenv()


def get_secret(name):
    if os.environ[name]:
        return os.environ[name]
    return os.getenv(name)


def filter_content(names_bodies):
    for name, body in names_bodies:
        if len(name.split()) > 1:
            if 'function' in name and len(name.split('function')[-1].split()) == 1:
                name = name.split('function')[-1]
            else:
                continue
        before_open_paranthesis = body.split('(', 1)[0]
        if len(before_open_paranthesis.split()) > 2:
            if body.split('(', 1)[0].split()[-2] == 'function':
                name = before_open_paranthesis.split()[-1]
                body = f"function {name}({body.split('(', 1)[1]}"
            else:
                continue
        elif len(body.split('(', 1)) == 1:
            continue
        if not body.startswith('function'):
            print(f'body doesnt start with "function", body: {body}, name: {name}')

        if len(body.split('(', 1)[0].split()) != 2:
            print(f'text before opening parenthesis must be 2 words, body: {body}, name: {name}')
        yield name, body


def get_functions_dict(text):
    # Regex pattern to match function definitions
    pattern = r"(function\s+[^\(]+\([^\)]*\)\s*(public|external|internal|private)*\s*(?:pure|constant|view|payable)*\s*(?:returns)*\s*\(*[^\)]*\)*\s*\{[^}]+\})"
    matches = re.findall(pattern, text, re.MULTILINE)
    # Get a list of function names
    function_names = [re.search(r"(function\s+)([^\(]+)", match[0]).group(2).strip() for match in matches]
    # Get a list of function bodies
    function_bodies = [match[0] for match in matches]
    # Zip the function names and bodies into a dictionary
    names_bodies = zip(function_names, function_bodies)
    names_bodies = list(filter_content(names_bodies))
    functions_dict = dict(names_bodies)
    return functions_dict
