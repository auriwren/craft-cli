"""CLI smoke tests using Click's test runner."""

from click.testing import CliRunner
from craft_cli.cli import cli


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Craft.do" in result.output


def test_doc_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["doc", "--help"])
    assert result.exit_code == 0
    assert "list" in result.output
    assert "create" in result.output


def test_block_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["block", "--help"])
    assert result.exit_code == 0


def test_folder_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["folder", "--help"])
    assert result.exit_code == 0


def test_task_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["task", "--help"])
    assert result.exit_code == 0


def test_collection_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["collection", "--help"])
    assert result.exit_code == 0
