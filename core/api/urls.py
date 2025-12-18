from django.urls import path
from core.api.views import HomeListView, DeviceListView, EntityListView
from core.api.control import ControlEntityView
from core.api.scenes import SceneListView, RunSceneView
from core.api.auth import login_view, logout_view

urlpatterns = [
    # Authentication
    path("auth/login/", login_view, name="api_login"),
    path("auth/logout/", logout_view, name="api_logout"),
    
    # Existing endpoints
    path("homes/", HomeListView.as_view(), name="api_homes"),
    path("homes/<int:home_id>/devices/", DeviceListView.as_view(), name="api_devices"),
    path("homes/<int:home_id>/scenes/", SceneListView.as_view(), name="api_scenes"),
    path("devices/<int:device_id>/entities/", EntityListView.as_view(), name="api_entities"),
    path("entities/<int:entity_id>/control/", ControlEntityView.as_view(), name="api_control"),
    path("scenes/<int:scene_id>/run/", RunSceneView.as_view(), name="api_run_scene"),
]
