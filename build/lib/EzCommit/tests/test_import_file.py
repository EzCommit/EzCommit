import pytest
from model.git import Model


def test_success_import_context():
    model = Model(
        context_path="./tests/mocks/convention.txt",
        convention_path=None
    )

    assert len(model.context) > 0, "Failed to import context"

def test_success_import_convention():
    model = Model(
        context_path=None,
        convention_path="./tests/mocks/convention.txt"
    )

    assert len(model.convention) > 0, "Failed to import convention"

def test_success_import_context_and_convention():
    model = Model(
        context_path="./tests/mocks/context.txt",
        convention_path="./tests/mocks/convention.txt"
    )

    assert len(model.context) > 0, "Failed to import context"
    assert len(model.convention) > 0, "Failed to import convention"

def test_fail_import_context():
    with pytest.raises(AssertionError):
        model = Model(
            context_path="./tests/mocks/invalid.txt",
            convention_path=None
        )

def test_fail_import_convention():
    with pytest.raises(AssertionError):
        model = Model(
            context_path=None,
            convention_path="./tests/mocks/invalid.txt"
        )