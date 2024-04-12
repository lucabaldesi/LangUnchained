#!/bin/bash

import os


class CompletionRecord(object):
    def __init__(self, role, content):
        self.role = role
        self.content = content

    def from_llama2(chat_completion):
        print(len(chat_completion))
        answer = chat_completion[-1]['generation']
        return CompletionRecord(answer['role'], answer['content'])

    def from_openai(chat_completion):
        print(len(chat_completion.choices))
        answer = chat_completion.choices[0].message
        return CompletionRecord(answer.role, answer.content)

    def __str__(self):
        return f"[{self.role.upper()}] - {self.content}"

    def to_dict(self):
        return {"role": self.role, "content": self.content}


class Llama2Model(object):
    def __init__(self, stop="\n\n"):
        from llama import Llama
        self.model = Llama.build(
            ckpt_dir="../llama-2-7b-chat/",
            tokenizer_path="../tokenizer.model",
            max_seq_len=512,
            max_batch_size=6,
        )
        self.temperature = 0.6
        self.top_p = 0.9
        self.max_gen_len = None
        self.stop = stop
        self.prompts = []

    def _trim_message(self, message):
        content = message.content.split(self.stop)
        message.content = content[0]
        return message

    def generate(self, user_string):
        self.prompts.append(
            {
                "role": "user",
                "content": user_string,
            }
        )
        dialogs: List[Dialog] = [self.prompts]
        chat_completion = self.model.chat_completion(
            dialogs,  # type: ignore
            max_gen_len=self.max_gen_len,
            temperature=self.temperature,
            top_p=self.top_p,
        )
        message = CompletionRecord.from_llama2(chat_completion)
        message = self._trim_message(message)
        print(message)
        self.prompts.append(message.to_dict())
        return message

    def add_system_prompt(self, prompt):
        self.prompts.append(
            {
                "role": "system",
                "content": prompt,
            }
        )

    def clear_history(self):
        self.prompts = []


class OpenAIModel(object):

    def __init__(self, stop="\n\n"):
        from openai import OpenAI
        self.client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
        self.prompts = []
        self.stop = stop

    def generate(self, user_string):
        self.prompts.append(
            {
                "role": "user",
                "content": user_string,
            }
        )
        chat_completion = self.client.chat.completions.create(
            model="gpt-4",
            stop=self.stop,
            messages=self.prompts
        )
        message = CompletionRecord.from_openai(chat_completion)
        print(message)
        self.prompts.append(message.to_dict())
        return message

    def add_system_prompt(self, prompt):
        self.prompts.append(
            {
                "role": "system",
                "content": prompt,
            }
        )

    def clear_history(self):
        self.prompts = []


class SearchTool(object):
    def __init__(self):
        self.description = '''
            a search engine. useful for when you need to answer questions about current
            events. input should be a search query.
            '''

    def operate(self, input_str):
        return "Newcastle Temperature Yesterday. Maximum temperature yesterday:\
             56 °F (at 6:00 pm) Minimum temperature yesterday: 46 °F"


class CalculatorTool(object):
    def __init__(self):
        self.description = '''
            useful for getting the result of a math expression. The input to this
            tool should be a valid mathematical expression that could be executed
            by a simple calculator.
            '''

    def operate(self, input_str):
        import re
        pattern = r"[^0-9+\-*/().\s]"
        inp = re.sub(pattern,"", input_str)
        if len(inp):
            val = eval(inp, {'__builtins__':None})
            return str(val)
        else:
            return "Error"


class Agent(object):
    def __init__(self):
        self.model = Llama2Model(stop='Observation:')
        self.tools = {'calculator': CalculatorTool(), 'search': SearchTool()}

    def get_agent_prompt(self, question):
        agent_prompt = '''
            Answer the following questions as best you can. You have access to the following tools:
            '''
        for tool_name, tool in self.tools.items():
            agent_prompt += tool_name + ": " + tool.description

        agent_prompt += '''
            Use the following format:

            Question: the input question you must answer
            Thought: you should always think about what to do
            Action: the action to take, should be one of [search, calculator]
            Action Input: the input to the action
            Observation: the result of the action
            ... (this Thought/Action/Action Input/Observation can repeat N times)
            Thought: I now know the final answer
            Final Answer: the final answer to the original input question

            Begin!
            '''
        agent_prompt += "Question: " + question + "\n"
        agent_prompt += "Thought: "

        return agent_prompt

    def get_action_from_answer(self, res):
        action = None
        action_input = None
        for line in res.content.split("\n"):
            line = line.strip()
            if line.startswith("Action: "):
                action = " ".join(line.split(" ")[1:])
            if line.startswith("Action Input: "):
                action_input = " ".join(line.split(" ")[2:])
        print(f"Action detected: {action}({action_input})")
        return (action, action_input)

    def single_generation(self, question):
        print(f"Question: {question}")
        res = self.model.generate(self.get_agent_prompt(question))
        action, action_input = self.get_action_from_answer(res)
        while action:
            if action in self.tools:
                observation = "Observation: " + \
                    self.tools[action].operate(action_input)
            else:
                observation = "Observation: error in reasoning"
            print(observation)
            res = self.model.generate(observation)
            action, action_input = self.get_action_from_answer(res)
        return res

    def generate(self, question):
        # prompt = '''
        #    Given the previous conversation and a follow up question, rephrase the
        #    follow up question to be a standalone question.
        #    Follow up question: ''' + question + "\nStandalone question: "
        # res = self.model.generate(self.get_agent_prompt(question))
        # self.model.clear_history()
        # question = res.content
        self.single_generation(question)


if __name__ == "__main__":
    a = Agent()
    msg = a.generate(
        "What was the high temperature in SF yesterday in Celsius?")
