import pytest
from packflow.loaders.utils import inference_backend_parts


@pytest.mark.parametrize(
    "path",
    [
        "foo.bar",
        "foo",
        "foo:bar:baz",  # multiple colons
    ],
)
def test_inference_backend_parts_invalid(path):
    with pytest.raises(ValueError):
        inference_backend_parts(path)


@pytest.mark.parametrize(
    "path, module, object",
    [
        ("foo.bar:baz", "foo.bar", "baz"),
        ("inference:Backend", "inference", "Backend"),
    ],
)
def test_inference_backend_parts(path, module, object):
    assert inference_backend_parts(path) == [module, object]
