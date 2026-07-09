from rest_framework.renderers import JSONRenderer


class EnvelopeJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = (renderer_context or {}).get("response")
        status_code = getattr(response, "status_code", 200)
        meta = None
        if response:
            headers = response.headers
            if "X-Total" in headers:
                meta = {"page": int(headers["X-Page"]), "limit": int(headers["X-Limit"]), "total": int(headers["X-Total"]), "cursor": None}
        if isinstance(data, dict) and {"success", "message", "data", "errors"}.issubset(data):
            payload = data
        else:
            success = status_code < 400
            payload = {"success": success, "message": "تمت العملية بنجاح" if success else "تعذر إتمام العملية", "data": data if success else None, "errors": None if success else data, "meta": meta}
        return super().render(payload, accepted_media_type, renderer_context)
