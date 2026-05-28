from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

import uvicorn
from db.init import initialize_database
from routers import chat, learning_objectives, materials, performance, students

app = FastAPI()
app.include_router(learning_objectives.router)
app.include_router(students.router)
app.include_router(materials.router)
app.include_router(performance.router)
app.include_router(chat.router)


@app.on_event("startup")
def startup():
    initialize_database()



if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
