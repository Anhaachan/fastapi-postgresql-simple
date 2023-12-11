from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Annotated, Optional
from database import create_engine_instance, create_session_local
import models
from sqlalchemy.orm import Session


app = FastAPI()

tags_metadata = [
    {"name": "index", "description": "Operations related to the index."},
    {"name": "questions", "description": "Operations related to questions."},
    {"name": "choices", "description": "Operations related to choices."},
]

app = FastAPI(
    openapi_tags=tags_metadata,
)
models.Base.metadata.create_all(bind=create_engine_instance())


class ChoiceBase(BaseModel):
    choice_text: Optional[str]
    is_correct: bool


class QuestionBase(BaseModel):
    question_text: str
    choices: List[ChoiceBase]


def get_db():
    db = create_session_local()()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


@app.get("/", tags=["index"])
async def index():
    return {"message": "Hello Wolrd"}


@app.get("/questions/{question_id}", tags=["questions"])
async def read_question(question_id: int, db: db_dependency):
    result = db.query(models.Questions).filter(models.Questions.id == question_id).first()
    if not result:
        raise HTTPException(status_code=404,
                            detail='Question Not Found'
                            )
    return result


@app.get("/choices/{question_id}",tags=["choices"])
async def read_choices(question_id: int, db: db_dependency):
    result = db.query(models.Choices).filter(models.Choices.question_id == question_id).all()
    if not result:
        raise HTTPException(status_code=404,
                            detail='Choices is NOt Found')
    return result


@app.post("/questions/",tags=["questions"])
async def create_questions(question: QuestionBase, db: db_dependency):
    db_question = models.Questions(question_text=question.question_text)
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    for choice in question.choices:
        db_choice = models.Choices(
            choice_text=choice.choice_text,
            is_correct=choice.is_correct,
            question_id=db_question.id
        )
        db.add(db_choice)
    db.commit()
    return {"message": "Question created successfully"}
