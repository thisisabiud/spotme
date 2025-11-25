# seating/urls.py
from django.urls import path
from . import views

app_name = 'seating'

urlpatterns = [
    # Main pages
    path('', views.index, name='index'),
    path('event/<int:event_id>/map/', views.seat_map, name='seat_map'),
    
    # Search APIs
    path('api/search/events/', views.search_events, name='search_events'),
    path('api/search/attendee/', views.search_attendee, name='search_attendee'),
    
    # Event APIs
    path('api/events/<int:event_id>/', views.EventDetailAPI.as_view(), name='event_detail_api'),
    path('api/events/<int:event_id>/statistics/', views.event_statistics, name='event_statistics'),
    path('api/events/<int:event_id>/map-data/', views.get_event_map_data, name='event_map_data'),
    
    # Seat APIs
    path('api/seats/<int:seat_id>/info/', views.get_seat_info, name='seat_info'),
    
    # Legacy endpoints (for backward compatibility)
    path('search_attendee/', views.search_attendee, name='search_attendee_legacy'),
    path('seat/<int:seat_id>/info/', views.get_seat_info, name='seat_info_legacy'),
]