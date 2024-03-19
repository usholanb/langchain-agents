import json
from langchain import Anthropic

from utils.camel_agent import CAMELAgent
from utils.helpers import get_secret, get_functions_dict
from langchain.chat_models import ChatAnthropic
from langchain.prompts.chat import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.schema import (
    HumanMessage,
)

Anthropic.anthropic_api_key = get_secret('ANTHROPIC_API_KEY')


class AgentsLlmApiCaller:

    def __init__(self, data):
        self.refresh = False
        self.user_role_name = "Solidity Developer"
        self.assistant_role_name = "Web3 Security Expert"
        self.variables = data['complete_example']
        self.example = data['complete_example_answer']
        self.assistant_inception_prompt = data['assistant_inception_prompt']
        self.user_inception_prompt = data['user_inception_prompt']
        self.user_task = data['user_task']

    def get_sys_msgs(self, assistant_role_name: str, user_role_name: str, task: str):
        assistant_sys_template = SystemMessagePromptTemplate.from_template(template=self.assistant_inception_prompt)
        assistant_sys_msg = \
            assistant_sys_template.format_messages(assistant_role_name=assistant_role_name,
                                                   user_role_name=user_role_name,
                                                   task=task)[0]

        user_sys_template = SystemMessagePromptTemplate.from_template(template=self.user_inception_prompt)
        user_sys_msg = \
            user_sys_template.format_messages(assistant_role_name=assistant_role_name,
                                              user_role_name=user_role_name,
                                              task=task)[0]

        return assistant_sys_msg, user_sys_msg

    def get_answer_query(self, contract_code, test_contract_code, function):
        user_task = self.user_task.format(
            contract_code=contract_code, test_contract_code=test_contract_code, function=function)
        word_limit = 10000  # word limit for task brainstorming
        task_specifier_prompt = (
            """Here is a task that {assistant_role_name} will help {user_role_name} to complete: {task}.
            Please make it more specific. Be creative and imaginative.
            Please reply with the specified task in {word_limit} words or less. Do not add anything else."""
        )
        task_specifier_template = HumanMessagePromptTemplate.from_template(template=task_specifier_prompt)
        task_specifier_msg = task_specifier_template.format_messages(assistant_role_name=self.assistant_role_name,
                                                                     user_role_name=self.user_role_name,
                                                                     task=user_task, word_limit=word_limit)[0]
        assistant_sys_msg, user_sys_msg = self.get_sys_msgs(self.assistant_role_name, self.user_role_name,
                                                            task_specifier_msg.content)
        assistant_agent = CAMELAgent(assistant_sys_msg, ChatAnthropic(model="claude-v1-100k", temperature=0., max_tokens_to_sample=4096, verbose=True))
        user_agent = CAMELAgent(user_sys_msg, ChatAnthropic(model="claude-v1-100k", temperature=0., max_tokens_to_sample=4096, verbose=True))

        # Reset agents
        assistant_agent.reset()
        user_agent.reset()

        # Initialize chats
        assistant_msg = HumanMessage(
            content=(f"{user_sys_msg.content}. "
                     "Now start to give me introductions one by one. "
                     "Only reply with Instruction and Input."))

        user_msg = HumanMessage(content=f"{assistant_sys_msg.content}")
        assistant_agent.step(user_msg)

        print(f"Original task prompt:\n{user_task}\n")

        chat_turn_limit = 8
        functions = {}
        for n in range(chat_turn_limit):
            user_ai_msg = user_agent.step(assistant_msg)
            user_msg = HumanMessage(content=user_ai_msg.content)
            print(f"AI User ({self.user_role_name}):\n\n{user_msg.content}\n\n")
            assistant_ai_msg = assistant_agent.step(user_msg)
            assistant_msg = HumanMessage(content=assistant_ai_msg.content)
            print(f"AI Assistant ({self.assistant_role_name}):\n\n{assistant_msg.content}\n\n")
            if 'Solution: ' in assistant_msg.content:
                new_functions = get_functions_dict(assistant_msg.content)
                if new_functions:
                    functions.update(new_functions)
                    print(f'assistant returned these functions: {new_functions}')

            if "<CAMEL_TASK_DONE>" in assistant_msg.content or "<CAMEL_TASK_DONE>" in user_msg.content:
                break
        return functions


if __name__ == '__main__':
    with open('data/e2e_suggest_test_from_tests_example.json', 'r') as f_in:
        example = json.load(f_in)
    agent = AgentsLlmApiCaller(example)
    result = agent.get_answer_query(**example['incomplete_example'])
    print(f'\nfinal result is:\n{result}')
    print(f'\nresult functions:\n{result.keys()}')