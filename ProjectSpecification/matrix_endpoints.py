from flask import Blueprint, request, jsonify, current_app
import traceback
import numpy as np
import pandas as pd

matrix_bp = Blueprint("matrix_endpoints", __name__)

def _to_jsonable(obj):
    if isinstance(obj, (list, tuple)):
        return [_to_jsonable(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (pd.Series, pd.Index)):
        return obj.tolist()

    try:
       
        if hasattr(obj, "tolist") and not isinstance(obj, (str, bytes)):
            return _to_jsonable(obj.tolist())
    except Exception:
        pass

    if isinstance(obj, (np.generic,)):
        return obj.item()

    return obj

@matrix_bp.route("/api/matrix", methods=["POST"])
def analyze_matrix():


    from tools_state import _tools, _tools_lock, _tools_status
    
    with _tools_lock:
        if not _tools_status.get('ready') or not _tools:
            current_app.logger.info("analyze_matrix called but tools not ready")
            return jsonify({'error': 'tools not ready', 'tools_status': _tools_status}), 503
        tools = _tools

    current_app.logger.info("analyze_matrix called")

    func = None
    if hasattr(tools, 'analyze_matrix'):
        func = getattr(tools, 'analyze_matrix')
    else:
        obo = getattr(tools, 'obo', None)
        if obo and hasattr(obo, 'analyze_matrix'):
            func = getattr(obo, 'analyze_matrix')

    if not func:
        current_app.logger.warning("No analyze_matrix function found on tools object")
        return jsonify({'results': [], 'warning': 'analyze_matrix implementation not found on server'}), 501


    try:
        result = func()
    except Exception as ex:
        current_app.logger.exception("Error in analyze_matrix:")
        return jsonify({'error': str(ex), 'trace': traceback.format_exc()}), 500


    try:
        if isinstance(result, (list, tuple)) and len(result) >= 3:
            values, y_labels, x_labels = result[0], result[1], result[2]
            payload = {
                'values': _to_jsonable(values),
                'y_labels': _to_jsonable(y_labels),
                'x_labels': _to_jsonable(x_labels)
            }
        else:

            payload = _to_jsonable(result)
    except Exception as ex:
        current_app.logger.exception("Error converting analyze_matrix result to JSON-friendly types:")
        return jsonify({'error': 'conversion error', 'detail': str(ex)}), 500

    return jsonify({"result": payload})


