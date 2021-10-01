import traceback

from flask import Blueprint, current_app, render_template, request

from pepys_timeline.db import get_config_options, get_dashboard_metadata, get_dashboard_stats
from pepys_timeline.utils import make_error_response

api = Blueprint("api", __name__, url_prefix="")

MISSING_PARAMS_MSG = "missing parameter(s)"


@api.app_errorhandler(Exception)
def handle_db_conn_error(err):
    current_app.logger.exception(err)
    return make_error_response(message=str(err), description=traceback.format_exc())


@api.route("/")
def index():
    return render_template("index.html")


@api.route("/config")
def config():
    return {"config_options": get_config_options()}


@api.route("/dashboard_metadata")
def dashboard_metadata():
    data = request.args
    if any((p not in data for p in ("from_date", "to_date"))):
        return MISSING_PARAMS_MSG, 400
    from_date = data.get("from_date")
    to_date = data.get("to_date")
    return {"dashboard_metadata": get_dashboard_metadata(from_date, to_date)}


@api.route("/dashboard_stats", methods=["POST"])
def dashboard_stats():
    data = request.json
    if any((p not in data for p in ("serial_participants", "range_types"))):
        return MISSING_PARAMS_MSG, 400
    serial_participants = data.get("serial_participants")
    range_types = data.get("range_types")
    stats = get_dashboard_stats(serial_participants, range_types)
    return {"dashboard_stats": stats}
