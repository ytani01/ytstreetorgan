import click
from click.testing import CliRunner

from ytstreetorgan.click_utils import click_common_opts


def test_click_common_opts():
    @click.command()
    @click_common_opts("1.2.3")
    def cli(ctx, debug):
        click.echo(f"debug={debug}")

    runner = CliRunner()

    # Test debug flag
    result = runner.invoke(cli, ['-d'])
    assert result.exit_code == 0
    assert "debug=True" in result.output

    # Test version flag
    result = runner.invoke(cli, ['-V'])
    assert result.exit_code == 0
    assert "1.2.3" in result.output

    # Test help flag
    result = runner.invoke(cli, ['-h'])
    assert result.exit_code == 0
    assert "Usage:" in result.output

def test_click_common_opts_no_v():
    @click.command()
    @click_common_opts("1.2.3", use_v=False)
    def cli(ctx, debug):
        pass

    runner = CliRunner()
    result = runner.invoke(cli, ['-v'])
    assert result.exit_code != 0
