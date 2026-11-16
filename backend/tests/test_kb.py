from app import kb

def test_retrieves_relevant_traditional_practice():
    r = kb.search("How can I control aphids naturally?")
    assert r["matched"] is True
    assert r["title"] == "Neem leaf spray for insects"
    assert r["sources"] and r["sources"][0]["verified_by"].startswith("PENDING")

def test_unknown_question_does_not_invent_advice():
    r = kb.search("How do I grow dragon fruit in a hydroponic greenhouse?")
    assert r["matched"] is False
    assert "could not find" in r["answer"].lower()
