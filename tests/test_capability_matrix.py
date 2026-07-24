from capability_matrix import (
    CAPABILITY_MATRIX,
    capabilities_for,
    supports_session_analysis,
)


def test_every_known_adapter_has_capability():
    for tool in ("claude", "cursor", "codex", "copilot", "import_paste"):
        assert tool in CAPABILITY_MATRIX


def test_unknown_tool_is_all_false():
    cap = capabilities_for("does-not-exist")
    assert cap.role is False
    assert cap.session_boundary is False
    assert supports_session_analysis("does-not-exist") is False


def test_import_paste_cannot_do_session_analysis():
    # pasted single blobs have no reliable session/role structure
    assert supports_session_analysis("import_paste") is False
