import tempfile
from pathlib import Path
import pytest
from rlm_engine import execute_code_search


@pytest.mark.asyncio
async def test_execute_code_search_finds_pattern():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "a.py").write_text("foo = 1\nbar = 2\n")
        (root / "b.txt").write_text("nothing here\n")
        results = await execute_code_search(pattern="foo", repo_root=str(root), file_glob="**/*.py")
        assert len(results) == 1
        assert results[0]["file"].endswith("a.py")
        assert results[0]["line"] == 1
