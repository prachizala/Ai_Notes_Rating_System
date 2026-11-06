from typing import List, Dict
from pydantic import BaseModel, Field


class FormulaSyntaxItem(BaseModel):
    title: str
    syntax_or_formula: str
    note: str


class DistinctionItem(BaseModel):
    parameter: str
    concept_a: str
    concept_b: str


class CheatSheetResponse(BaseModel):
    document_id: str
    document_title: str
    subject_name: str
    summary_capsule: str
    formulas_and_syntax: List[FormulaSyntaxItem]
    key_definitions: List[Dict[str, str]]
    distinctions_table: List[DistinctionItem]
    exam_traps: List[str]
    rapid_mnemonics: List[str]
