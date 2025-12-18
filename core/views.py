from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from core.models import Entity
from core.services.device_control import control_entity


def toggle_entity(request, entity_id):
    """
    Toggle an entity ON/OFF.
    
    This is a simple testing endpoint.
    """
    entity = get_object_or_404(Entity, id=entity_id)

    # Simple toggle
    current = entity.state.get("value", "OFF")
    new_value = "OFF" if current == "ON" else "ON"

    control_entity(entity, new_value)

    return JsonResponse({
        "success": True,
        "entity": entity.name,
        "command": new_value
    })


def control_entity_api(request, entity_id):
    """
    Control an entity with custom command.
    
    POST body should contain the command value.
    """
    import json
    
    entity = get_object_or_404(Entity, id=entity_id)
    
    if request.method == "POST":
        try:
            command = json.loads(request.body)
            control_entity(entity, command)
            
            return JsonResponse({
                "success": True,
                "entity": entity.name,
                "command": command
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "error": str(e)
            }, status=400)
    
    return JsonResponse({
        "success": False,
        "error": "Only POST allowed"
    }, status=405)
