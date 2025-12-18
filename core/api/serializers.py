from rest_framework import serializers
from core.models import Home, Location, Device, Entity, Scene


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


class SceneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scene
        fields = ["id", "name"]
