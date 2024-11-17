from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import uvicorn
from pydantic import BaseModel
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import json
from func import get_openai_completion
import os
import logging
import re

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve React app
app.mount("/static", StaticFiles(directory="/home/nebius/playground/chat-frontend/build/static"), name="static")

# Global variables
df = None
variable_names = []
problem_description = ""
verified_dependencies = set()  # Changed to a set
hypothesis_responses = []

def load_data():
    global df, variable_names, problem_description
    try:
        df = pd.read_csv("/home/nebius/playground/main/data.csv")
        variable_names = df.columns.tolist()
        
        with open("/home/nebius/playground/main/data_relationships.txt", "r") as file:
            problem_description = file.read()
        logger.info(f"Data loaded successfully. Variables: {variable_names}")
    except Exception as e:
        logger.error(f"Error loading data: {str(e)}")
        raise

load_data()

def dependency_score(verified_deps):
    # This is a placeholder function. Implement the actual scoring logic here.
    return len(verified_deps)

class ChatMessage(BaseModel):
    message: str

@app.post("/api/chat")
async def chat(chat_message: ChatMessage):
    global verified_dependencies, hypothesis_responses
    user_message = chat_message.message
    
    logger.info(f"Received message: {user_message}")
    
    if user_message.lower() == "restart":
        verified_dependencies = set()  # Reset to an empty set
        hypothesis_responses = []
        logger.info("Game restarted")
        return JSONResponse(content={"message": "Game restarted. All progress has been reset."})

    # Check if it's the first message
    if not hypothesis_responses:
        intro_message = f"""You will be practicing your analytical skills, on a data understanding task. 
Your goal is to uncover structure in the data - what data variables depend on what other data variables?.
- At any point, you can ask the system to plot any variables against any other.
- If you guess there is any dependency in the data, you should record it as a hypothesis.
- If you believe you have seen the right data to confirm the hypothesis, you should say the hypothesis is confirmed. You will then get feedback.

The variables available in the data are: {', '.join(variable_names)}

What variables would you like to plot?"""
        logger.info("Sending intro message")
        hypothesis_responses.append(user_message)
        return JSONResponse(content={"message": intro_message})

    # Extract variables to plot
    plot_prompt = f"""Extract a list of variable names the user wants to plot from the following user message.
The available variables are: {', '.join(variable_names)}. 
If the user makes a small spelling error in the variables, correct it. 
Preserve the variable order given by the user.
Return your response as a JSON array of strings.

User message: {user_message}

Example response format:
["variable1", "variable2"]
"""
    plot_variables_response = get_openai_completion("You are a helpful assistant.", plot_prompt)
    logger.info(f"OpenAI response for plot variables: {plot_variables_response}")
    
    try:
        # Remove any extra text around the JSON array
        json_start = plot_variables_response.find('[')
        json_end = plot_variables_response.rfind(']') + 1
        if json_start != -1 and json_end != -1:
            plot_variables_json = plot_variables_response[json_start:json_end]
            plot_variables = json.loads(plot_variables_json)
        else:
            raise ValueError("JSON array not found in the response")

        if not isinstance(plot_variables, list) or not all(isinstance(var, str) for var in plot_variables):
            raise ValueError("Invalid format: expected a list of strings")
        logger.info(f"Extracted plot variables: {plot_variables}")
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing plot variables: {str(e)}")
        return JSONResponse(content={"message": "I'm sorry, I couldn't understand which variables to plot. Could you please specify them clearly?"})
    except ValueError as e:
        logger.error(f"Error validating plot variables: {str(e)}")
        return JSONResponse(content={"message": "I'm sorry, I couldn't understand which variables to plot. Could you please specify them clearly?"})

    # Generate plot
    if len(plot_variables) == 1:
        fig = px.histogram(df, x=plot_variables[0], title=f"Histogram of {plot_variables[0]}")
        plot_json = fig.to_json()
        logger.info("1D histogram generated successfully")
    elif len(plot_variables) == 2:
        fig = px.scatter(df, x=plot_variables[0], y=plot_variables[1], title=f"{plot_variables[1]} vs {plot_variables[0]}")
        plot_json = fig.to_json()
        logger.info("2D scatter plot generated successfully")
    elif len(plot_variables) == 3:
        fig = px.scatter_3d(df, x=plot_variables[0], y=plot_variables[1], z=plot_variables[2], 
                  title=f"3D Plot of {plot_variables[0]}, {plot_variables[1]}, and {plot_variables[2]}")
        plot_json = fig.to_json()
        logger.info("3D scatter plot generated successfully")
    else:
        logger.warning(f"Invalid number of plot variables: {len(plot_variables)}")
        return JSONResponse(content={"message": "Please specify one, two, or three variables to plot."})

    # Ask for hypothesis
    hypothesis_prompt = "Can you form or confirm any hypothesis about the data?"
    
    # Evaluate hypothesis
    evaluation_prompt = f"""We have a data science with data generated from Python with numpy code as follows:
{problem_description}

The user has formulated the following hypotheses, in order:
{hypothesis_responses}

The user's latest response is:
{user_message}

If the user's response says "restart", return the string "RESTART".

If the user's response forms a hypothesis (but does not confirm it), return a paraphrase of the string "How would you check or verify this hypothesis?"

If the user's response confirms a hypothesis, check it against the problem description - is it correct? If so, return a tuple in the format (correctness_message, verified_dependencies) where verified_dependencies = ["dependent_variable", "independent_variable1 identified by the user in last turn", ..., "independent_variableN identified by the user in the last turn"] or return an empty list if no relationship is correct. The correctness message is an assessment if the user's last turn is correct, wrong, or on the right track.
"""
    evaluation_result = get_openai_completion("You are a helpful assistant.", evaluation_prompt)
    logger.info(f"Evaluation result: {evaluation_result}")
    
    try:
        if evaluation_result == "RESTART":
            verified_dependencies = set()  # Reset to an empty set
            hypothesis_responses = []
            logger.info("Game restarted")
            return JSONResponse(content={"message": "Game restarted. All progress has been reset."})
        
        if evaluation_result.startswith("(") and evaluation_result.endswith(")"):
            evaluation_result = eval(evaluation_result)
            if isinstance(evaluation_result, tuple):
                correctness_message, new_dependencies = evaluation_result
                verified_dependencies = verified_dependencies.union(set(new_dependencies))  # Use set union
                score = dependency_score(verified_dependencies)
                response_message = f"{correctness_message}\n\nYour current score is: {score}\n\n{hypothesis_prompt}"
            else:
                response_message = f"{evaluation_result}\n\n{hypothesis_prompt}"
        else:
            response_message = f"{evaluation_result}\n\n{hypothesis_prompt}"
        
        hypothesis_responses.append(user_message)
    except Exception as e:
        logger.error(f"Error evaluating hypothesis: {str(e)}")
        response_message = f"I couldn't properly evaluate your hypothesis. {hypothesis_prompt}"

    logger.info(f"Sending response: {response_message}")
    return JSONResponse(content={"message": response_message, "plot": plot_json})

@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    file_path = f"/home/nebius/playground/chat-frontend/build/{full_path}"
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    return FileResponse("/home/nebius/playground/chat-frontend/build/index.html")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host="0.0.0.0", port=8080)
