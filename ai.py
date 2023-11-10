import os
from dotenv import load_dotenv
import json
import openai
from ai_task import gen_prompt
from user import User
from goal import Goal, aiGetUserGoals, aiGetAllGoals

load_dotenv(".env")
openai.api_key  = os.getenv('OPENAI_API_KEY')
LOG_LEVEL = os.getenv('LOG_LEVEL')
if not LOG_LEVEL:
    LOG_LEVEL = 'debug'

def get_completion(prompt, model="gpt-3.5-turbo"):
    messages = [{"role": "user", "content": prompt}]
    if LOG_LEVEL=='debug':
        print('Asking a generative AI for an answer')
        print('Request: ')
        print(messages)
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=float(os.getenv('OPENAI_TEMPERATURE')), # this is the degree of randomness of the model's output
    )
    if LOG_LEVEL=='debug':
        print('Reply: ')
        print(response)
    return response.choices[0].message["content"]

def generateGoal(user: User, mode='run'):
    if user.id == 0:
        goals = []
    else:
        goals = aiGetUserGoals(user.id)
    if LOG_LEVEL=='debug':
        print('Generating a goal for a user')
        print('Goals: ')
        print(goals)
    if goals:
        prompt = gen_prompt(goals, isnew=False)
    elif mode=='run':
        # goals = aiGetAllGoals()
        goals = []
        prompt = gen_prompt(goals, isnew=True)
    else:
        prompt = gen_prompt(goals, isnew=True)
    if LOG_LEVEL=='debug':
        print('Prompt:')
        print(prompt)
    response = get_completion(prompt)
    if mode=='test':
            print(response)
            return response
    if LOG_LEVEL=='debug':
        print('Response from the model:')
        print(response)
    if response:
        try:
            jsonResponse = json.loads(response)
            if LOG_LEVEL=='debug':
                print('Response is in the JSON format:')            
        except:
            print('AI response doesn\'t contain JSON')
            print('GenAI user '+str(user.id))
            print(response)
            jsonResponse = ''
        if jsonResponse["title"]:
            if LOG_LEVEL=='debug':
                print('Response contains a title')
            genGoal = Goal(
                author=user.id,
                title=jsonResponse["title"],
                status=7,
                ispublic=False,
                isfriends=False,
                isprivate=True,
                isgenerated=True,
                isaccepted=False,
            )
            genGoal.save()
            if jsonResponse["person"]:
                if LOG_LEVEL=='debug':
                    print('JSON contains a personality')
                user.savePersonality(genGoal.id, jsonResponse["person"])
            return jsonResponse["title"]
        else:
            print('AI response doesn\'t contain goal')
            print('GenAI user '+str(user.id))
            print(response)
            return ''
    else:
        print('AI response doesn\'t contain response')
        print('GenAI user '+str(user.id))
        return ''
    