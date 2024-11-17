import os
from openai import OpenAI

def get_openai_completion(sys_prompt, user_prompt):
    """
    Get a completion from OpenAI's chat model.
    
    Args:
        sys_prompt (str): The system prompt to set the context
        user_prompt (str): The user's input prompt
        
    Returns:
        str: The completion response text
    
    Requires:
        OPENAI_API_KEY environment variable to be set with a valid OpenAI API key
    """
    # Initialize the client with the API key from environment variable
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Create a chat completion request
    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.7,
        max_tokens=1024,
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    
    # Return the completion text
    return response.choices[0].message.content
