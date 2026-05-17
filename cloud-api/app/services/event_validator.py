from models.ies_event import IESEvent


def validate_event(event_dict: dict) -> dict:
    """Valida un evento IES v2.0. Devuelve {'valid': bool, 'errors': [str]}."""
    errors: list[str] = []

    if reject_payload_field(event_dict):
        errors.append("Campo 'payload' está prohibido — usar 'data'")

    try:
        IESEvent(**event_dict)
    except Exception as e:
        errors.extend(_parse_pydantic_errors(str(e)))

    return {"valid": len(errors) == 0, "errors": errors}


def validate_event_simple(event_dict: dict) -> tuple[bool, str]:
    """Versión simplificada para compatibilidad interna."""
    result = validate_event(event_dict)
    msg = result["errors"][0] if result["errors"] else "valid"
    return result["valid"], msg


def reject_payload_field(event_dict: dict) -> bool:
    """Retorna True si el evento tiene campo prohibido 'payload'."""
    return "payload" in event_dict


def _parse_pydantic_errors(error_str: str) -> list[str]:
    lines = [l.strip() for l in error_str.splitlines() if l.strip()]
    return [l for l in lines if l and not l.startswith("For further")][:3]
