
import os
import openai

openai.api_key = ""


prompt = "#Generate python mock test code for the rest apis:\n\n\n{}\n{}"

# Open a file: file
file = open('fastapi_server.py', mode='r')

# read all lines at once
all_of_it = file.read()

# close the file
file.close()

prompt = prompt.format(all_of_it,"\n\n\"\"\"\n\n")

prompt_orig="#Generate python mock test code for the rest apis :\n\n\nfrom fastapi import FastAPI\n\napp = FastAPI()\n\n\n@app.get(\"/\")\nasync def root():\n    return {\"message\": \"Hello World\"}\n\n@app.get(\"/courses/{course_name}\")\ndef read_course(course_name):\n    return {\"course_name\": course_name}\n\n\ncourse_items = [{\"course_name\": \"Python\"}, {\"course_name\": \"SQLAlchemy\"}, {\"course_name\": \"NodeJS\"}]\n\n\n@app.get(\"/courses/\")\ndef read_courses(start: int, end: int):\n    return course_items[start: start + end]\n\n\"\"\"\n"

response = openai.Completion.create(
  model="text-davinci-003",
  prompt=prompt,
  temperature=0,
  max_tokens=3146,
  top_p=1,
  frequency_penalty=0,
  presence_penalty=0,
  stop=["\"\"\""]
)



with open('test.py', 'w') as f:
    f.write(response['choices'][0]['text'])
