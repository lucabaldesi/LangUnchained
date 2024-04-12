# LangUnchained

Simple LLM-based system (a.k.a., agent or ReAct implementation).

## Setup

```
$> python3 -m virtualenv .venv
$> pip3 install -r requirements.txt
```

### OpenAI

You are required to provide the API key:
```
$> export OPENAI_API_KEY="..."
```

### Meta Llama2
We assume the upper directory is the llama git repository,
where you have downloded the tokenizer and the model, something e.g., _llama-2-7b-chat_, _tokenizer.model_.


## Run

```
$> ./distributed_run.sh
```

If you do not have a GPU and/or work with the OpenAI model:
```
$> python3 agent.py
```
