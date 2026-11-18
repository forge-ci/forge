"""A Linux producer can package Darwin output without recipe relabeling."""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("darwin_producer", ROOT / "scripts/master_pull.py")
producer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(producer)


def test_macos_26_runner_is_explicit_and_does_not_change_linux():
    arm = next(row for _, row in producer.PLATFORMS if row["platform"] == "macos-arm64")
    linux = next(row for _, row in producer.PLATFORMS if row["platform"] == "linux-x64")
    assert producer.worker_row(arm, "2.17", macos_runner="macos-26")["runner"] == "macos-26"
    assert producer.worker_row(arm, "2.17")["runner"] == "macos-15"
    assert producer.worker_row(linux, "2.17", macos_runner="macos-26")["runner"] == "ubuntu-24.04"
    with pytest.raises(SystemExit, match="macos_arm64_runner"):
        producer.worker_row(arm, "2.17", macos_runner="self-hosted")


@pytest.mark.parametrize("name", ["compiler-rt-darwin-arm64", "llvm-tools-linux-x64"])
def test_exact_recipe_selection_preserves_cross_producer(tmp_path, name):
    path = tmp_path / name
    path.mkdir()
    (path / "conanfile.py").touch()
    linux = next(row for _, row in producer.PLATFORMS if row["platform"] == "linux-x64")
    assert producer.select_recipe(name, str(path), linux, selection="exact") == {
        "recipe_name": name, "recipe_path": str(path),
    }
    with pytest.raises(SystemExit, match="missing"):
        producer.select_recipe(name, str(path / "absent"), linux, selection="exact")


def test_workflow_forwards_new_planning_inputs():
    text = (ROOT / ".github/workflows/forge-conan.yml").read_text()
    assert text.count("      macos_arm64_runner:") == 2
    assert text.count("      recipe_selection:") == 2
    assert "MACOS_ARM64_RUNNER: ${{ inputs.macos_arm64_runner }}" in text
    assert "RECIPE_SELECTION: ${{ inputs.recipe_selection }}" in text


def test_floor_worker_installs_pinned_source_build_tools():
    text = (ROOT / '.github/workflows/forge-conan.yml').read_text()
    assert '"cmake==3.31.10" "ninja==1.11.1.4"' in text
