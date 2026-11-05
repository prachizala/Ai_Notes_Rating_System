import pytest
from app.core.normalizer import normalize_name


def test_normalize_name():
    # Case insensitive
    assert normalize_name("Data Structures") == "data structures"
    # Strips punctuation
    assert normalize_name("C Programming!!") == "c programming"
    assert normalize_name("Object-Oriented Programming (OOP)") == "object oriented programming oop"
    # Collapses multiple spaces and trims
    assert normalize_name("   Database   Management   Systems   ") == "database management systems"
    # Empty string handling
    assert normalize_name("") == ""
    assert normalize_name("   ") == ""
