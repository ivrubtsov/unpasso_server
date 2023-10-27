import os
from dotenv import load_dotenv
import openai
from ai_task import gen_prompt
from user import User
from goal import Goal, aiGetUserGoals, aiGetAllGoals

load_dotenv(".env")
openai.api_key  = os.getenv('OPENAI_API_KEY')

def get_completion(prompt, model="gpt-3.5-turbo"):
    messages = [{"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=float(os.getenv('OPENAI_TEMPERATURE')), # this is the degree of randomness of the model's output
    )
    return response.choices[0].message["content"]

def generateGoal(user: User, mode='run'):
    if user.id == 0:
        goals = []
    else:
        goals = aiGetUserGoals(user.id)
    if goals:
        prompt = gen_prompt(goals, isnew=False)
    elif mode=='run':
        goals = aiGetAllGoals()
        prompt = gen_prompt(goals, isnew=True)
    else:
        prompt = gen_prompt(goals, isnew=True)
    response = get_completion(prompt)
    print(response)
    if mode=='run':
        genGoal = Goal(
            author=user.id,
            title=response["title"],
            status=7,
            ispublic=False,
            isfriends=False,
            isprivate=True,
            isgenerated=True,
            isaccepted=False,
        )
        genGoal.save()
        return response["title"]
    elif mode=='test':
        return response
    