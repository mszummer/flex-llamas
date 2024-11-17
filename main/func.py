import os
from openai import OpenAI

from ratelimit import limits, sleep_and_retry
from langchain_community.llms import Ollama




llm = Ollama(model="llama3.2:latest", base_url="http://127.0.0.1:42069/")

@sleep_and_retry
@limits(calls=1, period=5)
def get_ollama_completion(sys_prompt, user_prompt):

    print("DEFINITELY TRIED TO HIT OLLAMA")

    resp = llm.invoke(
        [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt},
        ],
        options={
            "temperature": 0.7,
            "max_tokens": 1024
        }
    )

    print(f'from prompt: {sys_prompt}\n---------\n{user_prompt}\n-----------')
    print(f'\t\tresp length: {len(resp)}')
    return resp





def get_completion(sys_prompt, user_prompt):
    return get_ollama_completion(sys_prompt, user_prompt)
