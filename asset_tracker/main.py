#!/usr/bin/env python
from __future__ import print_function
from .alert import DeletionAlert
from .tracker import AssetTracker
import argparse
import logging
import sys

parser = argparse.ArgumentParser(usage="%(prog)s [options] args...")
parser.add_argument("-c", "--config-filename", default="~/.asset_tracker/config")
parser.add_argument("-s", "--state-filename", default="~/.asset_tracker/state")
parser.add_argument("-v", action="append_const", const=1, dest="verbosity", default=[],
                    help="Be more verbose. Can be specified multiple times to increase verbosity further")
subparsers = parser.add_subparsers(help="Action to be taken")

def _action(name):
    def decorator(func):
        subparser = subparsers.add_parser(name)
        subparser.set_defaults(action=func)
        return subparser
    return decorator

@_action("scan")
def cmd_scan(args):
    asset_tracker.scan()
    _report()
    asset_tracker.save_state(args.state_filename)
    return 0

@_action("duplicates")
def cmd_duplicates(args):
    by_hash = {}
    for asset in asset_tracker.iter_assets():
        by_hash.setdefault(asset.get_hash(), []).append(asset)

    index = 1
    for asset_hash, assets in by_hash.iteritems():
        if len(assets) > 1:
            print(index, ")", ", ".join(str(asset) for asset in assets))
            index += 1
    return 0

@_action("clear")
def cmd_clear_alert(args):
    alerts = asset_tracker.get_alerts()
    to_clear = [alerts[int(index)-1] for index in args.indices]
    for alert in to_clear:
        asset_tracker.clear_alert(alert)
    asset_tracker.save_state(args.state_filename)
cmd_clear_alert.add_argument("indices", nargs="+")

def _report():
    print("Total:", asset_tracker.get_num_assets(), "assets tracked on", asset_tracker.get_num_machines(), "machines")
    for index, alert in enumerate(asset_tracker.get_alerts()):
        if index == 0:
            print("*** ALERTS ***")
        index += 1
        print(index, ")", alert)
        if isinstance(alert, DeletionAlert):
            recoverable = asset_tracker.get_identical_assets(alert.asset)
            if recoverable:
                print("\tFound alternative:", recoverable[0])

################################## Boilerplate ################################
def _configure_logging(args):
    verbosity_level = len(args.verbosity)
    if verbosity_level == 0:
        level = "WARNING"
    elif verbosity_level == 1:
        level = "INFO"
    else:
        level = "DEBUG"
    logging.basicConfig(
        stream=sys.stderr,
        level=level,
        format="%(asctime)s -- %(message)s"
        )

asset_tracker = None

#### For use with entry_points/console_scripts
def main_entry_point():
    global asset_tracker
    args = parser.parse_args()
    asset_tracker = AssetTracker()
    asset_tracker.load_configuration(args.config_filename)
    asset_tracker.try_load_state(args.state_filename)
    _configure_logging(args)
    sys.exit(args.action(args))


if __name__ == "__main__":
    main_entry_point()
