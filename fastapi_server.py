from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/courses/{course_name}")
def read_course(course_name):
    return {"course_name": course_name}


course_items = [{"course_name": "Python"}, {"course_name": "SQLAlchemy"}, {"course_name": "NodeJS"}]


@app.get("/courses/")
def read_courses(start: int, end: int):
    return course_items[start: start + end]