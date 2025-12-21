from rest_framework import serializers
from core.models import (
    Home, Location, Device, Entity, Scene, SceneAction,
    Automation, AutomationTrigger, AutomationAction
)


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ["id", "name", "location_type"]


class EntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Entity
        fields = [
            "id",
            "name",
            "entity_type",
            "subtype",
            "state",
            "capabilities",
            "unit",
            "is_controllable",
        ]


class DeviceSerializer(serializers.ModelSerializer):
    entities = EntitySerializer(many=True, read_only=True)

    class Meta:
        model = Device
        fields = [
            "id",
            "name",
            "node_name",
            "is_online",
            "last_seen",
            "entities",
        ]


class HomeSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    
    class Meta:
        model = Home
        fields = ["id", "name", "role"]
    
    def get_role(self, obj):
        request = self.context.get('request')
        if request and request.user:
            # Get the user's role in this home from HomeMember
            member = obj.homemember_set.filter(user=request.user).first()
            if member:
                return member.role
        return "guest"




class SceneActionSerializer(serializers.ModelSerializer):
    entity_name = serializers.CharField(source='entity.name', read_only=True)
    entity_type = serializers.CharField(source='entity.entity_type', read_only=True)
    
    class Meta:
        model = SceneAction
        fields = ['id', 'entity', 'entity_name', 'entity_type', 'value', 'order']


class SceneSerializer(serializers.ModelSerializer):
    actions = SceneActionSerializer(many=True, read_only=True)
    actions_data = serializers.ListField(write_only=True, required=False)
    
    class Meta:
        model = Scene
        fields = ['id', 'home', 'name', 'actions', 'actions_data']
        read_only_fields = ['id']
    
    def create(self, validated_data):
        actions_data = validated_data.pop('actions_data', [])
        scene = Scene.objects.create(**validated_data)
        
        # Create scene actions
        for action_data in actions_data:
            # Fetch the Entity object from the entity ID
            entity_id = action_data.pop('entity')
            entity = Entity.objects.get(id=entity_id)
            
            SceneAction.objects.create(
                scene=scene,
                entity=entity,
                **action_data
            )
        
        return scene
    
    def update(self, instance, validated_data):
        actions_data = validated_data.pop('actions_data', None)
        
        # Update scene fields
        instance.name = validated_data.get('name', instance.name)
        instance.save()
        
        # Update actions if provided
        if actions_data is not None:
            # Delete existing actions
            instance.actions.all().delete()
            # Create new actions
            for action_data in actions_data:
                # Fetch the Entity object from the entity ID
                entity_id = action_data.pop('entity')
                entity = Entity.objects.get(id=entity_id)
                
                SceneAction.objects.create(
                    scene=instance,
                    entity=entity,
                    **action_data
                )
        
        return instance


class AutomationTriggerSerializer(serializers.ModelSerializer):
    entity_name = serializers.CharField(source='entity.name', read_only=True)
    
    class Meta:
        model = AutomationTrigger
        fields = ['id', 'entity', 'entity_name', 'attribute', 'operator', 'value']


class AutomationActionSerializer(serializers.ModelSerializer):
    entity_name = serializers.CharField(source='entity.name', read_only=True, allow_null=True)
    scene_name = serializers.CharField(source='scene.name', read_only=True, allow_null=True)
    
    class Meta:
        model = AutomationAction
        fields = ['id', 'entity', 'entity_name', 'scene', 'scene_name', 'command', 'delay_seconds']


class AutomationSerializer(serializers.ModelSerializer):
    triggers = AutomationTriggerSerializer(many=True, read_only=True)
    actions = AutomationActionSerializer(many=True, read_only=True)
    triggers_data = serializers.ListField(write_only=True, required=False)
    actions_data = serializers.ListField(write_only=True, required=False)
    
    class Meta:
        model = Automation
        fields = [
            'id', 'home', 'name', 'enabled',
            'trigger_logic', 'cooldown_seconds',  # New fields
            'triggers', 'actions', 'triggers_data', 'actions_data'
        ]
        read_only_fields = ['id']
    
    def create(self, validated_data):
        triggers_data = validated_data.pop('triggers_data', [])
        actions_data = validated_data.pop('actions_data', [])
        
        automation = Automation.objects.create(**validated_data)
        
        # Create triggers
        for trigger_data in triggers_data:
            # Extract entity ID and fetch Entity object
            entity_id = trigger_data.pop('entity')
            entity = Entity.objects.get(id=entity_id)
            
            AutomationTrigger.objects.create(
                automation=automation,
                entity=entity,
                **trigger_data
            )
        
        # Create actions
        for action_data in actions_data:
            # Extract entity or scene ID and fetch the object
            entity_id = action_data.pop('entity', None)
            scene_id = action_data.pop('scene', None)
            
            if entity_id:
                entity = Entity.objects.get(id=entity_id)
                AutomationAction.objects.create(
                    automation=automation,
                    entity=entity,
                    **action_data
                )
            elif scene_id:
                scene = Scene.objects.get(id=scene_id)
                AutomationAction.objects.create(
                    automation=automation,
                    scene=scene,
                    **action_data
                )
        
        return automation
    
    def update(self, instance, validated_data):
        triggers_data = validated_data.pop('triggers_data', None)
        actions_data = validated_data.pop('actions_data', None)
        
        # Update automation fields
        instance.name = validated_data.get('name', instance.name)
        instance.enabled = validated_data.get('enabled', instance.enabled)
        instance.save()
        
        # Update triggers if provided
        if triggers_data is not None:
            instance.triggers.all().delete()
            for trigger_data in triggers_data:
                # Extract entity ID and fetch Entity object
                entity_id = trigger_data.pop('entity')
                entity = Entity.objects.get(id=entity_id)
                
                AutomationTrigger.objects.create(
                    automation=instance,
                    entity=entity,
                    **trigger_data
                )
        
        # Update actions if provided
        if actions_data is not None:
            instance.actions.all().delete()
            for action_data in actions_data:
                # Extract entity or scene ID and fetch the object
                entity_id = action_data.pop('entity', None)
                scene_id = action_data.pop('scene', None)
                
                if entity_id:
                    entity = Entity.objects.get(id=entity_id)
                    AutomationAction.objects.create(
                        automation=instance,
                        entity=entity,
                        **action_data
                    )
                elif scene_id:
                    scene = Scene.objects.get(id=scene_id)
                    AutomationAction.objects.create(
                        automation=instance,
                        scene=scene,
                        **action_data
                    )
        
        return instance
