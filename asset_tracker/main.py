#!/usr/bin/env python
from __future__ import print_function
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

def _report():
    print("Total:", asset_tracker.get_num_assets(), "assets tracked on", asset_tracker.get_num_machines(), "machines")
    missing = asset_tracker.get_deleted_files()
    if missing:
        print("**** MISSING FILES:")
        for asset in missing:
            print(asset)
    changed = asset_tracker.get_changed_files()
    if changed:
        print("**** CHANGED FILES:")
        for asset in changed:
            print(asset)

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
