import argparse
import logging
import time

import yaml

from bioblend import toolshed

ts = toolshed.ToolShedInstance(url='https://toolshed.g2.bx.psu.edu')
latest_revision_cache = {}


def retry_with_backoff(func, *args, **kwargs):
    backoff = 2
    max_retries = 5

    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_msg = str(e)
            if any(
                code in error_msg
                for code in (
                    "429",
                    "502",
                    "503",
                    "504",
                    "timed out",
                    "timeout",
                    "Connection",
                )
            ):
                if attempt < max_retries - 1:
                    logging.warning(
                        "ToolShed request failed (%s). Retrying in %ss...",
                        error_msg,
                        backoff,
                    )
                    time.sleep(backoff)
                    backoff = min(backoff * 2, 60)
                    continue
            raise


def get_latest_revision(name, owner):
    key = (owner, name)
    if key in latest_revision_cache:
        return latest_revision_cache[key]

    revs = retry_with_backoff(
        ts.repositories.get_ordered_installable_revisions, name, owner
    )
    latest_rev = revs[-1] if revs else None
    latest_revision_cache[key] = latest_rev
    return latest_rev


def load_locked_tools(fn):
    with open(fn + '.lock', 'r') as handle:
        locked = yaml.safe_load(handle) or {}
    locked.setdefault('tools', [])
    return locked


def save_locked_tools(fn, locked):
    with open(fn + '.lock', 'w') as handle:
        yaml.dump(locked, handle, default_flow_style=False, sort_keys=False)


def update_file(fn, owner=None, name=None, without=False):
    locked = load_locked_tools(fn)
    # Update any locked tools.
    for tool in locked['tools']:
        # If without, then if it is lacking, we should exec.
        logging.debug("Examining {owner}/{name}".format(**tool))

        if without:
            if 'revisions' in tool and not len(tool.get('revisions', [])) == 0:
                continue

        if not without and owner and tool['owner'] != owner:
            continue

        if not without and name and tool['name'] != name:
            continue

        logging.info("Fetching updates for {owner}/{name}".format(**tool))

        try:
            latest_rev = get_latest_revision(tool['name'], tool['owner'])
        except Exception as e:
            logging.warning("Failed to fetch revisions for %s/%s: %s", tool['owner'], tool['name'], e)
            continue

        if latest_rev is None:
            logging.warning("No installable revisions found for %s/%s", tool['owner'], tool['name'])
            continue

        if latest_rev in tool.get('revisions', []):
            # The rev is already known, don't add again.
            continue

        logging.info("Found newer revision of {owner}/{name} ({rev})".format(rev=latest_rev, **tool))

        # Get latest rev, if not already added, add it.
        if 'revisions' not in tool:
            tool['revisions'] = []

        if latest_rev not in tool['revisions']:
            # TS doesn't support utf8 and we don't want to either.
            tool['revisions'].append(str(latest_rev))

        tool['revisions'] = sorted(list(set( tool['revisions'] )))

    save_locked_tools(fn, locked)



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('fn', nargs='+', help="Tool.yaml file(s)")
    parser.add_argument('--owner', help="Repository owner to filter on, anything matching this will be updated")
    parser.add_argument('--name', help="Repository name to filter on, anything matching this will be updated")
    parser.add_argument('--without', action='store_true', help="If supplied will ignore any owner/name and just automatically add the latest hash for anything lacking one.")
    parser.add_argument('--log', choices=('critical', 'error', 'warning', 'info', 'debug'), default='info')
    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.log.upper()))
    for fn in args.fn:
        update_file(fn, owner=args.owner, name=args.name, without=args.without)
