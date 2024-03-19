from langchain.agents import tool
from pydantic import BaseModel, Field
from solcx import install_solc, compile_source


@tool(return_direct=True)
def compile_solidity(solidity_code_str):
    """
    This function compiles Solidity files using a specific version of solc.
    :return: Dict, the compiled contracts.
    """
    solidity_code_str = solidity_code_str.strip('`')
    solc_version = '0.8.2'
    # Install the specified version of solc
    install_solc(solc_version)
    try:
        result = compile_source(solidity_code_str)
    except Exception as e:
        print(f"couldn't compile {solidity_code_str}\n{str(e)}")
        return f'Compilation Failed. Either the code is invalid or current compiler({solc_version}) didnt match'
    print(result)
    return 'Compilation Successful. It is a valid solidity code.'


class SolidityCompilerInput(BaseModel):
    question: str = Field(description="Should be pure solidity code without surrounded backticks")
