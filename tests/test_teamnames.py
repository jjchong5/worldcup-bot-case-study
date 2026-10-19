from pmkit.teamnames import match_team, normalize


def test_aliases_and_accents():
    assert normalize("USA") == normalize("United States") == "unitedstates"
    assert normalize("Türkiye") == normalize("Turkey")
    assert normalize("Côte d'Ivoire") == "ivorycoast"


def test_flags_and_sort_hints_stripped():
    assert normalize(":mx: Mexico @@12") == "mexico"


def test_short_code_does_not_substring_match_long_name():
    assert match_team("Netherlands", ["NE", "Niger"]) is None


def test_exact_match_returns_key():
    assert match_team("Korea Republic", ["South Korea", "Japan"]) == "South Korea"
