from django.contrib import admin
from core.models import (
    Home, HomeMember, Location, Device, Entity, EntityAttribute,
    EntityStateHistory, Automation, AutomationTrigger, AutomationAction,
    Scene, SceneAction, Schedule, Firmware, OTAUpdate
)


@admin.register(Home)
class HomeAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'created_at')
    search_fields = ('name', 'owner__username')
    list_filter = ('created_at',)


@admin.register(HomeMember)
class HomeMemberAdmin(admin.ModelAdmin):
    list_display = ('home', 'user', 'role')
    list_filter = ('role',)
    search_fields = ('home__name', 'user__username')


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'home', 'location_type')
    list_filter = ('location_type',)
    search_fields = ('name', 'home__name')


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('name', 'node_name', 'home', 'location', 'is_online', 'last_seen')
    list_filter = ('is_online', 'home')
    search_fields = ('name', 'node_name')
    readonly_fields = ('created_at', 'last_seen')


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    list_display = ('name', 'entity_type', 'device', 'location', 'is_controllable')
    list_filter = ('entity_type', 'is_controllable', 'device__home')
    search_fields = ('name', 'device__name', 'device__node_name')
    readonly_fields = ('created_at',)


@admin.register(EntityAttribute)
class EntityAttributeAdmin(admin.ModelAdmin):
    list_display = ('entity', 'key', 'value', 'unit', 'updated_at')
    list_filter = ('key',)
    search_fields = ('entity__name', 'key')
    readonly_fields = ('updated_at',)


@admin.register(EntityStateHistory)
class EntityStateHistoryAdmin(admin.ModelAdmin):
    list_display = ('entity', 'value', 'timestamp')
    list_filter = ('timestamp', 'entity__entity_type')
    search_fields = ('entity__name',)
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'


@admin.register(Automation)
class AutomationAdmin(admin.ModelAdmin):
    list_display = ('name', 'home', 'enabled', 'created_at')
    list_filter = ('enabled', 'home')
    search_fields = ('name',)
    readonly_fields = ('created_at',)


@admin.register(AutomationTrigger)
class AutomationTriggerAdmin(admin.ModelAdmin):
    list_display = ('automation', 'entity', 'attribute', 'operator', 'value')
    list_filter = ('operator', 'automation__home')
    search_fields = ('automation__name', 'entity__name')


@admin.register(AutomationAction)
class AutomationActionAdmin(admin.ModelAdmin):
    list_display = ('automation', 'entity', 'scene', 'command')
    search_fields = ('automation__name', 'entity__name', 'scene__name')


@admin.register(Scene)
class SceneAdmin(admin.ModelAdmin):
    list_display = ('name', 'home')
    list_filter = ('home',)
    search_fields = ('name',)


@admin.register(SceneAction)
class SceneActionAdmin(admin.ModelAdmin):
    list_display = ('scene', 'entity', 'order', 'value')
    list_filter = ('scene__home',)
    search_fields = ('scene__name', 'entity__name')


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('name', 'home', 'schedule_type', 'enabled', 'created_at')
    list_filter = ('schedule_type', 'enabled', 'home')
    search_fields = ('name',)
    readonly_fields = ('created_at',)


@admin.register(Firmware)
class FirmwareAdmin(admin.ModelAdmin):
    list_display = ('version', 'file_url', 'created_at')
    search_fields = ('version',)
    readonly_fields = ('created_at',)


@admin.register(OTAUpdate)
class OTAUpdateAdmin(admin.ModelAdmin):
    list_display = ('device', 'firmware', 'status', 'updated_at')
    list_filter = ('status',)
    search_fields = ('device__name', 'firmware__version')
    readonly_fields = ('updated_at',)
