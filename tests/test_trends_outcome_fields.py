import inspect
import trends


def test_trends_module_references_outcome_fields():
    src = inspect.getsource(trends)
    assert "attributed_rework_rate" in src
    assert "under_specified_initial_plan" in src
