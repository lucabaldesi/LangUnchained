#!/bin/bash

import os


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
        print(len(chat_completion.choices))
        answer = chat_completion.choices[0].message
        self.prompts.append(answer)
        print(answer.content)
        return answer

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
        return str(eval(input_str))


class Agent(object):
    def __init__(self):
        self.model = OpenAIModel(stop='Observation:')
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
