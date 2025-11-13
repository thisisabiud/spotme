from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q, Count, Prefetch, Exists, OuterRef
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.views import View
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta, date
import json
import logging

from .models import Event, Attendee, Seat, Section

logger = logging.getLogger(__name__)

def index(request):
    """Main page with search functionality"""
    # Get filter parameters
    search_query = request.GET.get('search', '').strip()
    date_filter = request.GET.get('date_filter', 'all')
    
    # Base query for active events only
    events_query = Event.objects.filter(is_active=True).select_related().annotate(
        total_seats=Count('sections__seats', distinct=True),
        occupied_seats=Count('sections__seats__attendee', distinct=True)
    )
    
    # Apply search filter
    if search_query:
        events_query = events_query.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(venue__icontains=search_query)
        )
    
    # Apply date filter
    today = date.today()
    if date_filter == 'upcoming':
        events_query = events_query.filter(date__gte=today)
    elif date_filter == 'past':
        events_query = events_query.filter(date__lt=today)
    elif date_filter == 'this_week':
        week_end = today + timedelta(days=7)
        events_query = events_query.filter(date__range=[today, week_end])
    elif date_filter == 'this_month':
        from calendar import monthrange
        month_end = date(today.year, today.month, monthrange(today.year, today.month)[1])
        events_query = events_query.filter(date__range=[today, month_end])
    
    events = events_query.order_by('-date', '-time')
    
    # Pagination
    paginator = Paginator(events, 12)  # Show 12 events per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'date_filter': date_filter,
        'total_events': events.count()
    }
    
    return render(request, 'seating/index.html', context)


@require_http_methods(["GET"])
def search_events(request):
    """AJAX endpoint for searching events"""
    try:
        query = request.GET.get('q', '').strip()
        date_filter = request.GET.get('date_filter', 'upcoming')  # Default to upcoming
        limit = min(int(request.GET.get('limit', 12)), 50)  # Max 50 results

        # Base query with annotations for active events only
        events_query = Event.objects.filter(is_active=True).select_related().annotate(
            total_seats=Count('sections__seats', distinct=True),
            occupied_seats=Count('sections__seats__attendee', distinct=True)
        )

        # Apply search filter only if query is present and >= 2 chars
        if query and len(query) >= 2:
            events_query = events_query.filter(
                Q(name__icontains=query) | 
                Q(description__icontains=query) |
                Q(venue__icontains=query)
            )

        # Apply date filter
        today = date.today()
        if date_filter == 'upcoming':
            events_query = events_query.filter(date__gte=today)
        elif date_filter == 'past':
            events_query = events_query.filter(date__lt=today)
        elif date_filter == 'this_week':
            week_end = today + timedelta(days=7)
            events_query = events_query.filter(date__range=[today, week_end])
        elif date_filter == 'this_month':
            from calendar import monthrange
            month_end = date(today.year, today.month, monthrange(today.year, today.month)[1])
            events_query = events_query.filter(date__range=[today, month_end])

        events = events_query.order_by('-date', '-time')[:limit]

        results = []
        for event in events:
            occupancy_rate = 0
            if event.total_seats > 0:
                occupancy_rate = round((event.occupied_seats / event.total_seats) * 100, 1)
            
            results.append({
                'id': event.id,
                'name': event.name,
                'description': (event.description[:150] + '...') if event.description and len(event.description) > 150 else (event.description or ''),
                'venue': event.venue,
                'date': event.date.strftime('%Y-%m-%d'),
                'time': event.time.strftime('%H:%M') if event.time else None,
                'total_seats': event.total_seats,
                'occupied_seats': event.occupied_seats,
                'available_seats': max(0, event.total_seats - event.occupied_seats),
                'occupancy_rate': occupancy_rate,
                'status': 'past' if event.date < today else 'upcoming',
                'url': f'/event/{event.id}/map/'
            })

        return JsonResponse({
            'results': results,
            'count': len(results),
            'query': query,
            'date_filter': date_filter,
            'success': True
        })
        
    except ValueError as e:
        logger.warning(f"Invalid parameter in search_events: {str(e)}")
        return JsonResponse({
            'results': [],
            'count': 0,
            'query': query if 'query' in locals() else '',
            'date_filter': date_filter if 'date_filter' in locals() else 'upcoming',
            'success': False,
            'error': 'Invalid search parameters'
        }, status=400)
        
    except Exception as e:
        logger.error(f"Error in search_events: {str(e)}")
        return JsonResponse({
            'results': [],
            'count': 0,
            'query': query if 'query' in locals() else '',
            'date_filter': date_filter if 'date_filter' in locals() else 'upcoming',
            'success': False,
            'error': 'An error occurred while searching events'
        }, status=500)


@require_http_methods(["GET"])
def search_attendee(request):
    """AJAX endpoint for searching attendees"""
    try:
        query = request.GET.get('q', '').strip()
        event_id = request.GET.get('event_id')
        limit = min(int(request.GET.get('limit', 10)), 50)  # Max 50 results
        
        if not query or len(query) < 2:
            return JsonResponse({
                'results': [], 
                'message': 'Please enter at least 2 characters',
                'count': 0,
                'success': True
            })
        
        # Optimized query with select_related
        attendees_query = Attendee.objects.select_related(
            'seat__section__event'
        ).filter(
            Q(name__icontains=query) | Q(ticket_number__icontains=query),
            seat__section__event__is_active=True
        )
        
        if event_id:
            try:
                event_id = int(event_id)
                attendees_query = attendees_query.filter(seat__section__event_id=event_id)
            except (ValueError, TypeError):
                return JsonResponse({
                    'results': [], 
                    'message': 'Invalid event ID',
                    'count': 0,
                    'success': False
                }, status=400)
        
        attendees = attendees_query.order_by('name')[:limit]
        
        results = []
        for attendee in attendees:
            results.append({
                'id': attendee.id,
                'name': attendee.name,
                'ticket_number': attendee.ticket_number,
                'seat_info': f"Row {attendee.seat.row}, Seat {attendee.seat.seat_number}",
                'section': attendee.seat.section.name,
                'event': attendee.seat.section.event.name,
                'event_id': attendee.seat.section.event.id,
                'event_date': attendee.seat.section.event.date.strftime('%Y-%m-%d'),
                'seat_coordinates': {
                    'x': attendee.seat.x_coordinate,
                    'y': attendee.seat.y_coordinate
                }
            })
        
        return JsonResponse({
            'results': results,
            'count': len(results),
            'query': query,
            'success': True
        })
        
    except Exception as e:
        logger.error(f"Error in search_attendee: {str(e)}")
        return JsonResponse({
            'results': [],
            'count': 0,
            'query': query if 'query' in locals() else '',
            'success': False,
            'error': 'An error occurred while searching attendees'
        }, status=500)


@cache_page(60 * 5)  # Cache for 5 minutes
def seat_map(request, event_id):
    """Display seat map for an event with optimized queries"""
    try:
        event = get_object_or_404(Event.objects.filter(is_active=True), id=event_id)
        
        # Optimized prefetch for sections with their seats and attendees
        sections = Section.objects.filter(event=event).prefetch_related(
            Prefetch(
                'seats',
                queryset=Seat.objects.select_related('attendee')
            )
        )
        
        # Get statistics
        total_seats = Seat.objects.filter(section__event=event, is_available=True).count()
        occupied_seats = Attendee.objects.filter(seat__section__event=event).count()
        available_seats = max(0, total_seats - occupied_seats)
        
        context = {
            'event': event,
            'sections': sections,
            'total_seats': total_seats,
            'occupied_seats': occupied_seats,
            'available_seats': available_seats,
            'occupancy_rate': round((occupied_seats / total_seats) * 100, 1) if total_seats > 0 else 0,
        }
        
        return render(request, 'seating/seat_map.html', context)
        
    except Exception as e:
        logger.error(f"Error in seat_map: {str(e)}")
        return render(request, 'seating/error.html', {
            'error_message': 'Event not found or unavailable'
        })


@require_http_methods(["GET"])
def get_seat_info(request, seat_id):
    """Get detailed information about a specific seat"""
    try:
        seat = get_object_or_404(
            Seat.objects.select_related('section__event', 'attendee'), 
            id=seat_id,
            section__event__is_active=True
        )
        
        seat_info = {
            'id': seat.id,
            'seat_number': seat.seat_number,
            'row': seat.row,
            'section': seat.section.name,
            'event': seat.section.event.name,
            'is_available': seat.is_available,
            'coordinates': {
                'x': seat.x_coordinate,
                'y': seat.y_coordinate
            },
            'success': True
        }
        
        # Check if seat is occupied
        if hasattr(seat, 'attendee'):
            seat_info.update({
                'occupied': True,
                'attendee_name': seat.attendee.name,
                'ticket_number': seat.attendee.ticket_number,
                'attendee_id': seat.attendee.id
            })
        else:
            seat_info['occupied'] = False
        
        return JsonResponse(seat_info)
        
    except Exception as e:
        logger.error(f"Error in get_seat_info: {str(e)}")
        return JsonResponse({
            'error': 'Seat not found or unavailable',
            'success': False
        }, status=404)


@require_http_methods(["GET"])
def event_statistics(request, event_id):
    """Get detailed statistics for an event"""
    try:
        event = get_object_or_404(Event.objects.filter(is_active=True), id=event_id)
        
        # Section-wise statistics
        sections_stats = []
        sections = Section.objects.filter(event=event).annotate(
            total_seats=Count('seats', filter=Q(seats__is_available=True)),
            occupied_seats=Count('seats__attendee')
        )
        
        for section in sections:
            available_seats = max(0, section.total_seats - section.occupied_seats)
            occupancy_rate = (section.occupied_seats / section.total_seats * 100) if section.total_seats > 0 else 0
            
            sections_stats.append({
                'id': section.id,
                'name': section.name,
                'color': section.color,
                'total_seats': section.total_seats,
                'occupied_seats': section.occupied_seats,
                'available_seats': available_seats,
                'occupancy_rate': round(occupancy_rate, 1)
            })
        
        # Overall statistics
        total_seats = sum(s['total_seats'] for s in sections_stats)
        total_occupied = sum(s['occupied_seats'] for s in sections_stats)
        total_available = max(0, total_seats - total_occupied)
        overall_occupancy = (total_occupied / total_seats * 100) if total_seats > 0 else 0
        
        return JsonResponse({
            'event': {
                'id': event.id,
                'name': event.name,
                'date': event.date.strftime('%Y-%m-%d'),
                'time': event.time.strftime('%H:%M') if event.time else None,
                'venue': event.venue,
                'description': event.description
            },
            'overall_statistics': {
                'total_seats': total_seats,
                'occupied_seats': total_occupied,
                'available_seats': total_available,
                'occupancy_rate': round(overall_occupancy, 1)
            },
            'sections_statistics': sections_stats,
            'success': True
        })
        
    except Exception as e:
        logger.error(f"Error in event_statistics: {str(e)}")
        return JsonResponse({
            'error': 'Event not found or unavailable',
            'success': False
        }, status=404)


class EventDetailAPI(View):
    """Class-based view for event details API"""
    
    @method_decorator(cache_page(60 * 2))
    def get(self, request, event_id):
        try:
            event = Event.objects.filter(is_active=True).select_related().annotate(
                total_seats=Count('sections__seats', distinct=True, filter=Q(sections__seats__is_available=True)),
                occupied_seats=Count('sections__seats__attendee', distinct=True)
            ).get(id=event_id)
            
            available_seats = max(0, event.total_seats - event.occupied_seats)
            occupancy_rate = (event.occupied_seats / event.total_seats * 100) if event.total_seats > 0 else 0
            
            event_data = {
                'id': event.id,
                'name': event.name,
                'description': event.description,
                'venue': event.venue,
                'date': event.date.strftime('%Y-%m-%d'),
                'time': event.time.strftime('%H:%M') if event.time else None,
                'total_seats': event.total_seats,
                'occupied_seats': event.occupied_seats,
                'available_seats': available_seats,
                'occupancy_rate': round(occupancy_rate, 1),
                'status': 'past' if event.date < date.today() else 'upcoming',
                'is_active': event.is_active,
                'success': True
            }
            
            return JsonResponse(event_data)
            
        except Event.DoesNotExist:
            return JsonResponse({
                'error': 'Event not found',
                'success': False
            }, status=404)
        except (ValueError, TypeError):
            return JsonResponse({
                'error': 'Invalid event ID',
                'success': False
            }, status=400)
        except Exception as e:
            logger.error(f"Error in EventDetailAPI: {str(e)}")
            return JsonResponse({
                'error': 'An error occurred',
                'success': False
            }, status=500)
        

@require_http_methods(["GET"])
def get_event_map_data(request, event_id):
    """Get event data with seat map image URL"""
    try:
        event = get_object_or_404(Event.objects.filter(is_active=True), id=event_id)
        
        return JsonResponse({
            'success': True,
            'event': {
                'id': event.id,
                'name': event.name,
                'venue': event.venue,
                'date': event.date.strftime('%b %d, %Y'),
                'time': event.time.strftime('%I:%M %p') if event.time else None,
                'seat_map_url': event.seat_map_image.url if event.seat_map_image else None,
            }
        })
    except Exception as e:
        logger.error(f"Error in get_event_map_data: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=404)