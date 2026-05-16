import eventlet

eventlet.monkey_patch()

import os
import sys

import numpy as np

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from examples.viz.app.server import build_arg_parser, create_app


def main():
    parser = build_arg_parser()
    args = parser.parse_args()

    if args.fixed_action is not None:
        toks = [t.strip() for t in str(args.fixed_action).split(",") if t.strip()]
        if not toks:
            raise ValueError("--fixed_action provided but empty")
        args.fixed_action = np.asarray([float(t) for t in toks], dtype=np.float32)

    app, socketio, manager = create_app(args)
    app.config["SECRET_KEY"] = "unified_viz_secret"

    if getattr(args, "profile", None):
        manager.load_profile(str(args.profile))
    elif getattr(args, "scenario", None):
        manager.load_session(str(args.scenario))

    print(f"Running Unified Viz App on http://localhost:{args.port}")
    socketio.run(app, host="0.0.0.0", port=args.port, allow_unsafe_werkzeug=True)


if __name__ == "__main__":
    main()
