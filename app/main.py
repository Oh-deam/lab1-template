from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Person
from .schemas import (
    ErrorResponse,
    PersonRequest,
    PersonResponse,
    ValidationErrorResponse,
)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Person Service", lifespan=lifespan)
SessionDep = Annotated[Session, Depends(get_db)]


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    _request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    errors: dict[str, str] = {}

    for error in exc.errors():
        field = ".".join(str(part) for part in error["loc"][1:]) or "body"
        errors[field] = error["msg"]

    return JSONResponse(
        status_code=400,
        content={"message": "Invalid data", "errors": errors},
    )


@app.exception_handler(HTTPException)
async def http_error_handler(
    _request: Request,
    exc: HTTPException,
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": str(exc.detail)},
    )


@app.get(
    "/api/v1/persons",
    response_model=list[PersonResponse],
)
def list_persons(session: SessionDep) -> list[PersonResponse]:
    persons = session.scalars(select(Person).order_by(Person.id)).all()
    return [PersonResponse.model_validate(person) for person in persons]


@app.post(
    "/api/v1/persons",
    status_code=201,
    response_class=Response,
    responses={400: {"model": ValidationErrorResponse}},
)
def create_person(data: PersonRequest, session: SessionDep) -> Response:
    person = Person(**data.model_dump())
    session.add(person)
    session.commit()
    session.refresh(person)

    return Response(
        status_code=201,
        headers={"Location": f"/api/v1/persons/{person.id}"},
    )


@app.get(
    "/api/v1/persons/{id}",
    response_model=PersonResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_person(id: int, session: SessionDep) -> PersonResponse:
    person = session.get(Person, id)

    if person is None:
        raise HTTPException(
            status_code=404,
            detail=f"Person with id {id} not found",
        )

    return PersonResponse.model_validate(person)


@app.patch(
    "/api/v1/persons/{id}",
    response_model=PersonResponse,
    responses={
        400: {"model": ValidationErrorResponse},
        404: {"model": ErrorResponse},
    },
)
def update_person(
    id: int,
    data: PersonRequest,
    session: SessionDep,
) -> PersonResponse:
    person = session.get(Person, id)

    if person is None:
        raise HTTPException(
            status_code=404,
            detail=f"Person with id {id} not found",
        )

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(person, field, value)

    session.commit()
    session.refresh(person)
    return PersonResponse.model_validate(person)


@app.delete(
    "/api/v1/persons/{id}",
    status_code=204,
    response_class=Response,
    responses={404: {"model": ErrorResponse}},
)
def delete_person(id: int, session: SessionDep) -> Response:
    person = session.get(Person, id)

    if person is None:
        raise HTTPException(
            status_code=404,
            detail=f"Person with id {id} not found",
        )

    session.delete(person)
    session.commit()
    return Response(status_code=204)