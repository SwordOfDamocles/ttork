import sys
from optparse import OptionParser, Values
from .__version__ import __version__
from .app import TTorkApp
from ttork.utilities import read_yaml_config, is_valid_config


def main_help() -> None:
    """Top-level help output."""
    description = "ttork: Textual Tilt ORKestrator for Kubernetes."
    help = [
        ("start", "Start the ttork application."),
    ]
    action_help(description, help)


def action_help(description: str, action_help: list[tuple[str, str]]) -> None:
    """Dynamically generate help output with action listing.

    description: Top level app description
    action_help: List of tuples with action and description for that action.
    """
    if len(action_help) == 0:
        print(description)
        sys.exit(1)

    top_level_help = (
        f"usage: ttork <action> [options]\n"
        f"{description}\n\n"
        f"Available Actions:"
    )

    for action in action_help:
        top_level_help += f"\n  {action[0]: <14}: {action[1]}"
    top_level_help += (
        "\n\nFor help on a specific action, use the action name as the first "
        "argument to the script."
        f"\nExample: ttork {action_help[0][0]} --help\n"
    )

    sys.stdout.write(top_level_help)


def main(argv: list[str] = sys.argv[1:]):
    """Commandline entry point for ttork."""
    if not argv:
        argv = ["start"]

    action = ""

    if argv[0] in ["version", "-v", "--version"]:
        print("ttork, version {0}".format(__version__))
        sys.exit(0)

    elif argv[0] in ["start"]:
        usage = "usage: %prog start [options]"
        parser = OptionParser(usage=usage)
        parser.add_option(
            "-a",
            "--autostart",
            action="store_true",
            default=False,
            dest="autostart",
            help="Automatically start Tilt processes.",
        )
        (options, args) = parser.parse_args(argv)
        action = args[0]

    else:
        main_help()
        sys.exit(1)

    # Dictionary of function ptrs indexed by 'action' name
    actionIndex = {
        "start": start,
    }

    # Exectue action
    actionIndex[action](options, args)


def start(options: Values, args: list[str]) -> None:
    """Start the ttork application."""
    # Pull in the configuration data
    ttork_conf = read_yaml_config("./ttork.yaml")
    if not is_valid_config(ttork_conf):
        return

    if options.autostart:
        ttork_conf["autostart"] = True

    # Start the application
    app = TTorkApp()
    app.ttork_config = ttork_conf
    app.run()
