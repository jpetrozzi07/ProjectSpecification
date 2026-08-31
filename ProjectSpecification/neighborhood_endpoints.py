# neighborhood_endpoints.py
from flask import Blueprint, request, jsonify, current_app
import traceback

neighborhood_bp = Blueprint('neighborhood', __name__)

def _parse_payload(required_fields=None):
    payload = request.get_json(force=True, silent=True) or {}
    term = (payload.get('term') or '').strip()
    try:
        level = int(payload.get('level', 1))
    except Exception:
        level = 1
    result = {'term': term, 'level': level, 'raw': payload}
    if required_fields:
        for f in required_fields:
            if not result.get(f):
                raise ValueError(f"Missing or empty field: {f}")
    return result

@neighborhood_bp.route('/neighborhood/get', methods=['POST'], endpoint='get_neighborhood')
def get_neighborhood():
    try:
        parsed = _parse_payload(required_fields=['term'])
    except Exception as ex:
        return jsonify({'error': str(ex)}), 400

    # Import shared state from tools_state at request time
    from tools_state import _tools, _tools_lock, _tools_status

    with _tools_lock:
        if not _tools_status.get('ready') or not _tools:
            current_app.logger.info("get_neighborhood called but tools not ready")
            return jsonify({'error': 'tools not ready', 'tools_status': _tools_status}), 503
        tools = _tools

    current_app.logger.info("get_neighborhood called payload=%s", parsed['raw'])

    # Try to find a sensible function to compute neighborhood
    func = None
    if hasattr(tools, 'get_neighborhood'):
        func = getattr(tools, 'get_neighborhood')
    else:
        obo = getattr(tools, 'obo', None)
        if obo and hasattr(obo, 'get_neighborhood'):
            func = getattr(obo, 'get_neighborhood')

    if not func:
        current_app.logger.warning("No neighborhood function found on tools object")
        return jsonify({'results': [], 'warning': 'neighborhood implementation not found on server'}), 501

    try:
        result = func(parsed['term'], parsed['level'])
        if isinstance(result, set):
            result = sorted(result)  # deterministic order; use list(result) if order not needed
        return jsonify({
            'count': len(result),
            'results': result
        })
    except Exception as ex:
        current_app.logger.exception("Error in get_neighborhood:")
        return jsonify({'error': str(ex), 'trace': traceback.format_exc()}), 500

@neighborhood_bp.route('/neighborhood/info', methods=['POST'], endpoint='get_neighborhood_info')
def get_neighborhood_info():
    try:
        parsed = _parse_payload(required_fields=['term'])
    except Exception as ex:
        return jsonify({'error': str(ex)}), 400

    from tools_state import _tools, _tools_lock, _tools_status

    with _tools_lock:
        if not _tools_status.get('ready') or not _tools:
            current_app.logger.info("get_neighborhood_info called but tools not ready")
            return jsonify({'error': 'tools not ready', 'tools_status': _tools_status}), 503
        tools = _tools

    current_app.logger.info("get_neighborhood_info called payload=%s", parsed['raw'])

    func = None
    if hasattr(tools, 'get_neighborhood_info'):
        func = getattr(tools, 'get_neighborhood_info')
    else:
        obo = getattr(tools, 'obo', None)
        if obo and hasattr(obo, 'get_neighborhood_info'):
            func = getattr(obo, 'get_neighborhood_info')

    if not func:
        current_app.logger.warning("No neighborhood_info function found on tools object")
        return jsonify({'info': {}, 'warning': 'neighborhood info implementation not found on server'}), 501

    try:
        info = func(parsed['term'], parsed['level'])
        return jsonify({'info': info})
    except Exception as ex:
        current_app.logger.exception("Error in get_neighborhood_info:")
        return jsonify({'error': str(ex), 'trace': traceback.format_exc()}), 500