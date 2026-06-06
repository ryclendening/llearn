from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

import uvicorn
from starlette.middleware.sessions import SessionMiddleware
from auth.config import AUTH_COOKIE_SECURE, AUTH_STATE_SECRET, validate_auth_config
from db.init import initialize_database
from routers import admin, auth, chat, examples, learning_objectives, materials, performance, students

app = FastAPI()
app.add_middleware(
    SessionMiddleware,
    secret_key=AUTH_STATE_SECRET,
    https_only=AUTH_COOKIE_SECURE,
    same_site="lax",
)
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(learning_objectives.router)
app.include_router(students.router)
app.include_router(materials.router)
app.include_router(examples.router)
app.include_router(performance.router)
app.include_router(chat.router)


@app.on_event("startup")
def startup():
    validate_auth_config()
    initialize_database()



if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
