import os
from datetime import datetime
from dotenv import load_dotenv
import json
import openai
from ai_task import gen_prompt, gen_systemprompt
from user import User
from goal import Goal, aiGetUserGoals, aiGetAllGoals

load_dotenv(".env")
openai.api_key  = os.getenv('OPENAI_API_KEY')
LOG_LEVEL = os.getenv('LOG_LEVEL')
if not LOG_LEVEL:
    LOG_LEVEL = 'debug'
OPENAI_MODEL = os.getenv('OPENAI_MODEL')
if not OPENAI_MODEL:
    OPENAI_MODEL = 'gpt-3.5-turbo'
OPENAI_TEMPERATURE = os.getenv('OPENAI_TEMPERATURE')
if not OPENAI_TEMPERATURE:
    OPENAI_TEMPERATURE = 0.7
else:
    OPENAI_TEMPERATURE = float(OPENAI_TEMPERATURE)
if LOG_LEVEL=='debug':
    print('Running OpenAI model '+OPENAI_MODEL)

def get_completion(userPrompt, systemPrompt, model=OPENAI_MODEL):
    messages = [
    {"role": "system", "content": systemPrompt},
    {"role": "user", "content": userPrompt}
    ]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=OPENAI_TEMPERATURE, # this is the degree of randomness of the model's output
    )
    return response.choices[0].message["content"]

def generateGoal(user: User, mode='run'):
    if user.id == 0:
        goals = []
    else:
        goals = aiGetUserGoals(user.id)
    if LOG_LEVEL=='debug':
        print('Generating a goal for a user')
        print('Goals: ')
        for goal in goals:
            print(goal['title'])
    if goals:
        prompt = gen_prompt(goals, isnew=False)
    else:
        goals = []
        prompt = gen_prompt(goals, isnew=True)
    if LOG_LEVEL=='debug':
        print('Prompt:')
        print(prompt)
    systemPrompt = gen_systemprompt()
    response = get_completion(prompt,systemPrompt)
    if mode=='test':
            print('Response:')
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
        if 'title' in jsonResponse:
            if LOG_LEVEL=='debug':
                print('Response contains a title:')
                print(jsonResponse["title"])
            genGoal = Goal(
                author=user.id,
                date = datetime.now(),
                title=jsonResponse["title"],
                status=7,
                ispublic=False,
                isfriends=False,
                isprivate=True,
                isgenerated=True,
                isaccepted=False,
            )
            genGoal.save()
            # if 'person' in jsonResponse:
            #     if LOG_LEVEL=='debug':
            #         print('JSON contains a personality')
            #     user.savePersonality(genGoal.id, jsonResponse["person"])
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
    