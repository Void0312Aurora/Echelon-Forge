import eventlet

eventlet.monkey_patch()

import os
import signal
import sys

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from examples.viz.app.server import build_arg_parser, create_app
from examples.viz.runtime.action_utils import normalize_fixed_action


def main():
    parser = build_arg_parser()
    args = parser.parse_args()

    if args.fixed_action is not None:
        args.fixed_action = normalize_fixed_action(args.fixed_action, name="--fixed_action")

    app, socketio, manager = create_app(args)
    app.config["SECRET_KEY"] = "unified_viz_secret"

    def request_shutdown(signum=None, frame=None):
        if signum is not None:
            print(f"Shutdown signal received ({signum}); stopping viz session...")
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, request_shutdown)
    signal.signal(signal.SIGTERM, request_shutdown)

    if getattr(args, "profile", None):
        manager.load_profile(str(args.profile))
    elif getattr(args, "scenario", None):
        manager.load_session(str(args.scenario))

    print(f"Running Unified Viz App on http://localhost:{args.port}")
    try:
        socketio.run(app, host="0.0.0.0", port=args.port, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        pass
    finally:
        manager.shutdown(timeout_s=5.0)


if __name__ == "__main__":
    main()
