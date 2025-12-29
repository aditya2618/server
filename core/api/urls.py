from django.urls import path
from core.api import auth, views, scenes, automations, control, energy, location, subscription_views

urlpatterns = [
    # Authentication
    path("auth/login/", auth.login_view, name="api_login"),
    path("auth/register/", auth.register_view, name="api_register"),
    path("auth/profile/", auth.profile_view, name="api_profile"),
    path("auth/change-password/", auth.change_password_view, name="api_change_password"),
    path("auth/logout/", auth.logout_view, name="api_logout"),
    
    # Homes
    path("homes/", views.HomeListView.as_view(), name="home_list"),
    path("homes/<int:home_id>/", views.HomeDetailView.as_view(), name="home_detail"),
    path("homes/<int:home_id>/location/", location.HomeLocationView.as_view(), name="home_location"),
    path("homes/<int:home_id>/sun-times/", location.SunTimesView.as_view(), name="sun_times"),
    path("homes/<int:home_id>/subscription/", subscription_views.check_subscription, name="check_subscription"),
    path("homes/<int:home_id>/cloud/toggle/", subscription_views.toggle_cloud_mode, name="toggle_cloud_mode"),
    
    # Devices
    path("homes/<int:home_id>/devices/", views.DeviceListView.as_view(), name="device_list"),
    path("homes/<int:home_id>/devices/available/", views.AvailableDevicesView.as_view(), name="available_devices"),
    path("homes/<int:home_id>/devices/link/", views.LinkDevicesView.as_view(), name="link_devices"),
    path("homes/<int:home_id>/devices/unlink/", views.UnlinkDevicesView.as_view(), name="unlink_devices"),
    
    # Entities
    path("devices/<int:device_id>/entities/", views.EntityListView.as_view(), name="entity_list"),
    path("entities/<int:entity_id>/control/", control.ControlEntityView.as_view(), name="control_entity"),
    
    # Scenes
    path("homes/<int:home_id>/scenes/", scenes.SceneListView.as_view(), name="scene_list"),
    path("scenes/<int:scene_id>/", scenes.SceneDetailView.as_view(), name="scene_detail"),
    path("scenes/<int:scene_id>/run/", scenes.RunSceneView.as_view(), name="run_scene"),
    
    # Automations
    path("homes/<int:home_id>/automations/", automations.AutomationListView.as_view(), name="automation_list"),
    path("automations/<int:automation_id>/", automations.AutomationDetailView.as_view(), name="automation_detail"),
    path("automations/<int:automation_id>/toggle/", automations.AutomationToggleView.as_view(), name="automation_toggle"),
    
    # Energy Monitoring
    path("energy/", energy.EnergyViewSet.as_view({'get': 'list'}), name="energy_today"),
    path("energy/history/", energy.EnergyViewSet.as_view({'get': 'history'}), name="energy_history"),
    path("energy/settings/", energy.EnergyViewSet.as_view({'get': 'user_settings', 'put': 'user_settings'}), name="energy_settings"),
]
