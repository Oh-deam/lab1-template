from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.main import (
    create_person,
    delete_person,
    get_person,
    list_persons,
    update_person,
)
from app.models import Person
from app.schemas import PersonRequest


def test_create_person_returns_201_and_location():
    session = Mock(spec=Session)

    def assign_id(person):
        person.id = 42

    session.refresh.side_effect = assign_id

    response = create_person(
        PersonRequest(name="Ada", age=31, address="Moscow", work="Lab"),
        session,
    )

    assert response.status_code == 201
    assert response.body == b""
    assert response.headers["location"] == "/api/v1/persons/42"

    session.add.assert_called_once()
    saved_person = session.add.call_args.args[0]
    assert saved_person.name == "Ada"
    assert saved_person.age == 31
    session.commit.assert_called_once()


def test_get_person_and_missing_id():
    session = Mock(spec=Session)
    session.get.return_value = Person(id=42, name="Ada", age=31)

    result = get_person(42, session)

    assert result.id == 42
    assert result.name == "Ada"
    assert result.age == 31
    session.get.assert_called_with(Person, 42)

    session.get.return_value = None
    with pytest.raises(HTTPException) as error:
        get_person(999, session)

    assert error.value.status_code == 404


def test_list_persons():
    session = Mock(spec=Session)
    session.scalars.return_value.all.return_value = [
        Person(id=1, name="Ada"),
        Person(id=2, name="Grace"),
    ]

    result = list_persons(session)

    assert [(person.id, person.name) for person in result] == [
        (1, "Ada"),
        (2, "Grace"),
    ]
    session.scalars.assert_called_once()


def test_patch_updates_only_supplied_fields():
    session = Mock(spec=Session)
    person = Person(id=42, name="Ada", age=31, address="Moscow", work="Lab")
    session.get.return_value = person

    result = update_person(
        42,
        PersonRequest(name="Ada Updated", address="New address"),
        session,
    )

    assert result.name == "Ada Updated"
    assert result.address == "New address"
    assert result.age == 31
    assert result.work == "Lab"
    session.commit.assert_called_once()


def test_delete_person_and_missing_id():
    session = Mock(spec=Session)
    person = Person(id=42, name="Ada")
    session.get.return_value = person

    response = delete_person(42, session)

    assert response.status_code == 204
    assert response.body == b""
    session.delete.assert_called_once_with(person)
    session.commit.assert_called_once()

    session.get.return_value = None
    with pytest.raises(HTTPException) as error:
        delete_person(42, session)

    assert error.value.status_code == 404