"""
Test suite for Innovation 3: Concept Mind Map & Flowchart Generator.
"""

from app.services.mindmap import mindmap_service, _generate_fallback_mindmap


def test_fallback_mindmap_generation():
    title = "Computer Networks: OSI Model Architecture"
    text = (
        "Physical Layer: Transmits raw bitstream over physical media.\n"
        "Data Link Layer: Handles error-free node-to-node frame transfer.\n"
        "Network Layer: Manages packet routing and IP addressing.\n"
        "Transport Layer: Provides reliable end-to-end data delivery via TCP/UDP.\n"
        "Application Layer: High-level protocols including HTTP, DNS, and SMTP."
    )
    summary = "Comprehensive breakdown of the 7-layer OSI model."

    res = _generate_fallback_mindmap(title, text, summary)

    assert "diagram_type" in res
    assert "mermaid_code" in res
    assert "nodes" in res
    assert "edges" in res
    assert "summary" in res

    # Verify nodes
    assert len(res["nodes"]) >= 5
    root_nodes = [n for n in res["nodes"] if n["category"] == "core"]
    assert len(root_nodes) == 1

    # Verify edges
    assert len(res["edges"]) >= 4

    # Verify mermaid code syntax
    assert "graph TD" in res["mermaid_code"]
    assert "root" in res["mermaid_code"]


def test_mindmap_service():
    res = mindmap_service.generate_mindmap(
        document_title="C Programming Pointers",
        text="Pointer: Variable storing memory address. malloc: Dynamic allocation. free: Deallocation.",
        summary="Pointer basics."
    )
    assert len(res["nodes"]) >= 4
    assert len(res["edges"]) >= 3
    assert "mermaid_code" in res
