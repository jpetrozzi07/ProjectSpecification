"""
API endpoints for similarity calculations.

Exposes POST /api/similarity
Body (JSON): { "term1": "<term1>", "term2": "<term2>" }

This module will:
 - obtain a `GO_Tools` instance from `tools_states` if available, or instantiate a new one
 - call `compare_similarity_methods(term1, term2)` and return JSON result
"""
from flask import Blueprint, request, jsonify, current_app
import traceback

similarity_bp = Blueprint("similarity_endpoints", __name__)

def _parse_payload(required_fields=None):
    payload = request.get_json(force=True, silent=True) or {}
    term1 = (payload.get('term1') or '').strip()
    term2 = (payload.get('term2') or '').strip()

    result = {'term1': term1, 'term2': term2, 'raw': payload}
    if required_fields:
        for f in required_fields:
            if not result.get(f):
                raise ValueError(f"Missing or empty field: {f}")
    return result

@similarity_bp.route("/api/similarity", methods=["POST"])
def similarity():
    try:
        parsed = _parse_payload(required_fields=['term1','term2'])
    except Exception as ex:
        return jsonify({'error': str(ex)}), 400

    # Import shared state from tools_state at request time
    from tools_state import _tools, _tools_lock, _tools_status
    
    with _tools_lock:
        if not _tools_status.get('ready') or not _tools:
            current_app.logger.info("compare_similarity_methods called but tools not ready")
            return jsonify({'error': 'tools not ready', 'tools_status': _tools_status}), 503
        tools = _tools

    current_app.logger.info("compare_similarity_methods called payload=%s", parsed['raw'])

    func = None
    if hasattr(tools, 'compare_similarity_methods'):
        func = getattr(tools, 'compare_similarity_methods')
    else:
        obo = getattr(tools, 'obo', None)
        if obo and hasattr(obo, 'compare_similarity_methods'):
            func = getattr(obo, 'compare_similarity_methods')

    if not func:
        current_app.logger.warning("No compare_similarity_methods function found on tools object")
        return jsonify({'results': [], 'warning': 'compare_similarity_methods implementation not found on server'}), 501

    # call the target method
    try:
        # Expect compare_similarity_methods(term1, term2) or compare_similarity_methods(self, term1, term2)
        result = func(parsed['term1'], parsed['term2'])
    except Exception as ex:
        current_app.logger.exception("Error in get_neighborhood:")
        return jsonify({'error': str(ex), 'trace': traceback.format_exc()}), 500

    return jsonify({"result": result})