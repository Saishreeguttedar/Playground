import json
import re
from datetime import datetime, timedelta
from decimal import Decimal
from io import BytesIO
from uuid import uuid4

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.utils import timezone

from .models import Booking

GST_RATE = Decimal("0.05")
CONVENIENCE_FEE = Decimal("150.00")


TRIPS = [
    {
        "id": "goa-sunset-escape",
        "source": "Mumbai",
        "destination": "Goa",
        "mode": "Flight",
        "duration": "1h 20m",
        "price": 4999,
        "rating": 4.6,
        "tag": "Beach Escape",
        "image": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80",
        "description": "Golden beaches, boutique stays, and nightlife curated for an effortless weekend.",
        "offer": "15% off on beachfront stays",
    },
    {
        "id": "shimla-mountain-retreat",
        "source": "Delhi",
        "destination": "Shimla",
        "mode": "Train",
        "duration": "6h 10m",
        "price": 3599,
        "rating": 4.4,
        "tag": "Mountain Retreat",
        "image": "https://images.unsplash.com/photo-1518002054494-3a6f94352e9d?auto=format&fit=crop&w=1200&q=80",
        "description": "Pine valleys, toy-train charm, and cozy mountain lodges for a breezy hill getaway.",
        "offer": "Breakfast included for 2 nights",
    },
    {
        "id": "dubai-city-lights",
        "source": "Bengaluru",
        "destination": "Dubai",
        "mode": "Flight",
        "duration": "4h 05m",
        "price": 21999,
        "rating": 4.8,
        "tag": "Luxury International",
        "image": "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?auto=format&fit=crop&w=1200&q=80",
        "description": "Skyline views, desert experiences, and luxury shopping packed into one premium trip.",
        "offer": "Free airport transfer",
    },
    {
        "id": "jaipur-royal-weekend",
        "source": "Ahmedabad",
        "destination": "Jaipur",
        "mode": "Bus",
        "duration": "10h 15m",
        "price": 2899,
        "rating": 4.3,
        "tag": "Heritage Trail",
        "image": "https://images.unsplash.com/photo-1477587458883-47145ed94245?auto=format&fit=crop&w=1200&q=80",
        "description": "Palaces, pink-city food trails, and heritage stays with a comfortable city transfer plan.",
        "offer": "Flat ₹ 750 cashback",
    },
    {
        "id": "kerala-backwater-bliss",
        "source": "Chennai",
        "destination": "Kochi",
        "mode": "Flight",
        "duration": "1h 05m",
        "price": 6499,
        "rating": 4.7,
        "tag": "Nature Escape",
        "image": "https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?auto=format&fit=crop&w=1200&q=80",
        "description": "Backwaters, spice trails, and houseboat-inspired relaxation for a slow scenic vacation.",
        "offer": "Couple package add-on at 20% off",
    },
    {
        "id": "varanasi-spiritual-circuit",
        "source": "Kolkata",
        "destination": "Varanasi",
        "mode": "Train",
        "duration": "8h 40m",
        "price": 3199,
        "rating": 4.2,
        "tag": "Cultural Journey",
        "image": "https://images.unsplash.com/photo-1561361513-2d000a50f0dc?auto=format&fit=crop&w=1200&q=80",
        "description": "Ghats, evening aarti, and guided cultural immersion with convenient station transfers.",
        "offer": "Guided ghat tour included",
    },
]

MODE_IMAGES = {
    "Flight": "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?auto=format&fit=crop&w=1200&q=80",
    "Train": "https://images.unsplash.com/photo-1474487548417-781cb71495f3?auto=format&fit=crop&w=1200&q=80",
    "Bus": "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?auto=format&fit=crop&w=1200&q=80",
}

MODE_TAGS = {
    "Flight": "Fastest Option",
    "Train": "Balanced Journey",
    "Bus": "Budget Friendly",
}

DASHBOARD_AIRLINES = [
    {"name": "Air India", "time": "06:10 AM", "duration": "2h 20m", "price": 6840},
    {"name": "Indigo", "time": "10:45 AM", "duration": "2h 05m", "price": 5920},
    {"name": "Vistara", "time": "07:35 PM", "duration": "2h 15m", "price": 7310},
]

DASHBOARD_HOTELS = [
    {
        "name": "Seabreeze Suites",
        "rating": 4.7,
        "price": 4299,
        "image": "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?auto=format&fit=crop&w=900&q=80",
    },
    {
        "name": "Hillcrest Retreat",
        "rating": 4.5,
        "price": 3890,
        "image": "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=900&q=80",
    },
    {
        "name": "Urban Luxe Stay",
        "rating": 4.8,
        "price": 5290,
        "image": "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=900&q=80",
    },
]

DASHBOARD_HOLIDAYS = [
    {
        "title": "Goa Quick Break",
        "days": "3 Days / 2 Nights",
        "preview": "Beach walk, sunset cruise, and a market evening in one compact holiday.",
    },
    {
        "title": "Jaipur Heritage Escape",
        "days": "5 Days / 4 Nights",
        "preview": "Fort visits, local food trails, and a handpicked stay with guided sightseeing.",
    },
]

DASHBOARD_SMART_PLANS = [
    {"label": "Budget Smart", "copy": "Under ₹6000 with train or bus travel and comfortable stays."},
    {"label": "Long Weekend", "copy": "2 to 3 day ideas that fit a fast escape without exhausting travel."},
    {"label": "Premium Easy", "copy": "Flight-first plans with premium hotel suggestions for shorter routes."},
]

TRAVEL_ASSISTANT_RESPONSES = {
    "beach": "Goa and Kochi are the strongest beach-style options in Tripora right now. Goa is better for nightlife, while Kochi suits a slower scenic break.",
    "budget": "For tighter budgets, Jaipur, Varanasi, and Shimla are the strongest matches. They keep travel and stay costs more manageable.",
    "family": "For family trips, Jaipur and Kochi work very well because they balance sightseeing, food, and easy pacing.",
    "luxury": "For a luxury-style plan, Dubai is the premium pick. If you want something within India, a premium Goa or Kochi stay works well too.",
    "adventure": "For a more active trip, Shimla and Kochi are good picks depending on whether you prefer mountain or nature-driven travel.",
    "weekend": "For a short weekend plan, Goa or Jaipur are the easiest recommendations because they deliver a lot in just a few days.",
}

TRIPURA_ITINERARIES = {
    3: [
        {
            "title": "Arrival in Agartala",
            "icon": "🏛️",
            "places": [
                {
                    "name": "Ujjayanta Palace",
                    "description": "Start with the royal palace and museum to understand Tripura's heritage.",
                },
                {
                    "name": "Heritage Park",
                    "description": "Enjoy an easy walk through miniature landmarks and green open spaces.",
                },
                {
                    "name": "Agartala Local Market",
                    "description": "Try local snacks and shop for bamboo and handloom crafts.",
                },
            ],
        },
        {
            "title": "Water Palace Circuit",
            "icon": "🌊",
            "places": [
                {
                    "name": "Neermahal",
                    "description": "Visit the famous lake palace and take in the architecture from the shore or boat.",
                },
                {
                    "name": "Rudrasagar Lake",
                    "description": "Add a relaxing boat ride and sunset stop around the lakefront.",
                },
            ],
        },
        {
            "title": "Culture and Departure",
            "icon": "🌿",
            "places": [
                {
                    "name": "Tripura Government Museum",
                    "description": "Catch up on tribal art, sculptures, and historic collections before departure.",
                },
                {
                    "name": "Jagannath Temple",
                    "description": "A short spiritual stop with city views and calm surroundings.",
                },
            ],
        },
    ],
    5: [
        {
            "title": "Agartala Heritage Day",
            "icon": "🏛️",
            "places": [
                {"name": "Ujjayanta Palace", "description": "Explore the city's most iconic palace and museum."},
                {"name": "Heritage Park", "description": "Relax with a lightweight city outing and photo spots."},
                {"name": "Local Handicraft Market", "description": "Browse bamboo products and traditional textiles."},
            ],
        },
        {
            "title": "Lakeside Excursion",
            "icon": "🌊",
            "places": [
                {"name": "Neermahal", "description": "Spend time at the lake palace and surrounding viewpoints."},
                {"name": "Rudrasagar Lake Boat Ride", "description": "Add a scenic boat experience for the full circuit."},
            ],
        },
        {
            "title": "Temple and Nature Trail",
            "icon": "⛩️",
            "places": [
                {"name": "Tripura Sundari Temple", "description": "One of the most important spiritual landmarks in the region."},
                {"name": "Sepahijala Wildlife Sanctuary", "description": "A softer wildlife and birding day near Agartala."},
            ],
        },
        {
            "title": "Hill Views and Village Life",
            "icon": "🏞️",
            "places": [
                {"name": "Jampui Hills", "description": "Take in hill views, orange orchards, and a cooler climate."},
                {"name": "Local Village Stop", "description": "See a slower side of Tripura with local hospitality."},
            ],
        },
        {
            "title": "Wrap-up in Agartala",
            "icon": "🛍️",
            "places": [
                {"name": "State Museum or Café Stop", "description": "Keep the last day light and city-focused."},
                {"name": "Airport / Station Transfer", "description": "End the trip with a comfortable departure plan."},
            ],
        },
    ],
    7: [
        {
            "title": "Royal Agartala",
            "icon": "🏛️",
            "places": [
                {"name": "Ujjayanta Palace", "description": "Open the trip with Tripura's royal and cultural heart."},
                {"name": "Heritage Park", "description": "A relaxed evening after city sightseeing."},
            ],
        },
        {
            "title": "Neermahal and Rudrasagar",
            "icon": "🌊",
            "places": [
                {"name": "Neermahal", "description": "Spend longer around the palace and enjoy the lakeside setting."},
                {"name": "Rudrasagar Lake", "description": "Boating, sunset, and local photography stops."},
            ],
        },
        {
            "title": "Temple Day",
            "icon": "⛩️",
            "places": [
                {"name": "Tripura Sundari Temple", "description": "A meaningful heritage and spiritual day trip."},
                {"name": "Nearby Town Walk", "description": "Explore the local streets and food nearby."},
            ],
        },
        {
            "title": "Wildlife and Green Spaces",
            "icon": "🦜",
            "places": [
                {"name": "Sepahijala Wildlife Sanctuary", "description": "Enjoy birding, forest zones, and nature breaks."},
                {"name": "Botanical Zones", "description": "Add an easy afternoon around the sanctuary."},
            ],
        },
        {
            "title": "Northern Escape",
            "icon": "🏞️",
            "places": [
                {"name": "Jampui Hills", "description": "Move toward hill landscapes and scenic viewpoints."},
                {"name": "Sunset Ridge", "description": "A slower day for photos and peaceful stays."},
            ],
        },
        {
            "title": "Local Community Experience",
            "icon": "🏡",
            "places": [
                {"name": "Traditional Village Visit", "description": "Learn about local culture, weaving, and daily life."},
                {"name": "Regional Food Stop", "description": "Try Tripuri dishes and homestyle flavors."},
            ],
        },
        {
            "title": "Departure Day",
            "icon": "✈️",
            "places": [
                {"name": "Agartala City Stop", "description": "Keep the final day flexible for shopping or coffee."},
                {"name": "Departure Transfer", "description": "Head to the airport or station comfortably."},
            ],
        },
    ],
    10: [
        {
            "title": "Agartala Arrival",
            "icon": "🏛️",
            "places": [
                {"name": "Ujjayanta Palace", "description": "Begin with Tripura's signature landmark."},
                {"name": "Local Market", "description": "Ease into the trip with crafts and food."},
            ],
        },
        {
            "title": "City Heritage Day",
            "icon": "🏙️",
            "places": [
                {"name": "Heritage Park", "description": "Spend a slower city morning outdoors."},
                {"name": "Museum Trail", "description": "Cover history and regional culture."},
            ],
        },
        {
            "title": "Water Palace Day",
            "icon": "🌊",
            "places": [
                {"name": "Neermahal", "description": "Long-form palace visit with lakeside exploration."},
                {"name": "Rudrasagar Lake", "description": "Add sunset and extended boat time."},
            ],
        },
        {
            "title": "Temple and Heritage Town",
            "icon": "⛩️",
            "places": [
                {"name": "Tripura Sundari Temple", "description": "One of the core spiritual highlights of the state."},
                {"name": "Town Exploration", "description": "Walk the nearby market and local food spots."},
            ],
        },
        {
            "title": "Wildlife Day",
            "icon": "🦜",
            "places": [
                {"name": "Sepahijala Wildlife Sanctuary", "description": "Enjoy forests, birds, and quiet nature trails."},
                {"name": "Lake Zone", "description": "Add a restful second half to the sanctuary day."},
            ],
        },
        {
            "title": "Road to the Hills",
            "icon": "🏞️",
            "places": [
                {"name": "Jampui Hills Transfer", "description": "Move north and enjoy the changing landscapes."},
                {"name": "Village Viewpoint", "description": "Pause for scenic hill outlooks."},
            ],
        },
        {
            "title": "Hill Leisure Day",
            "icon": "🌄",
            "places": [
                {"name": "Sunrise / Sunset Point", "description": "A slow scenic day in the hills."},
                {"name": "Orange Orchard Stop", "description": "Add a classic Jampui experience when seasonal."},
            ],
        },
        {
            "title": "Community and Culture",
            "icon": "🏡",
            "places": [
                {"name": "Traditional Village Visit", "description": "Interact with local communities and craft traditions."},
                {"name": "Regional Cuisine Session", "description": "Try a fuller range of Tripuri food."},
            ],
        },
        {
            "title": "Flexible Exploration Day",
            "icon": "📍",
            "places": [
                {"name": "Repeat Favorite Spot", "description": "Use the extra day for a relaxed revisit or slower pace."},
                {"name": "Optional Shopping", "description": "Great time for souvenirs and handloom pieces."},
            ],
        },
        {
            "title": "Departure Day",
            "icon": "✈️",
            "places": [
                {"name": "Agartala Wrap-up", "description": "A final easy city stop before leaving."},
                {"name": "Departure Transfer", "description": "Head out comfortably with buffer time."},
            ],
        },
    ],
}


def get_trip_by_id(trip_id):
    return next((trip for trip in TRIPS if trip["id"] == trip_id), None)


def get_trip_from_session(request, trip_id):
    return request.session.get("search_trip_map", {}).get(trip_id)


def get_default_date():
    return (timezone.localdate() + timedelta(days=7)).isoformat()


def get_greeting():
    current_hour = timezone.localtime().hour
    if current_hour < 12:
        return "Good Morning"
    if current_hour < 17:
        return "Good Afternoon"
    return "Good Evening"


def is_letters_only_username(username):
    return bool(re.fullmatch(r"[A-Za-z]{5,}", username or ""))


def is_strong_password(password):
    return (
        len(password or "") >= 8
        and bool(re.search(r"[A-Z]", password))
        and bool(re.search(r"[a-z]", password))
        and bool(re.search(r"[^A-Za-z0-9]", password))
    )


def is_valid_full_name(full_name):
    return bool(re.fullmatch(r"[A-Za-z ]{3,}", full_name or ""))


def estimate_route_distance(source, destination):
    route_key = f"{source.strip().lower()}-{destination.strip().lower()}"
    base_seed = sum(ord(char) for char in route_key)
    city_weight = (len(source.strip()) + len(destination.strip())) * 42
    return max(220, 180 + city_weight + (base_seed % 780))


def calculate_trip_price(source, destination, mode):
    distance = estimate_route_distance(source, destination)
    price_multiplier = {"Flight": 8, "Train": 2, "Bus": 1.5}[mode]
    return int(round(distance * price_multiplier))


def with_search_result_pricing(trip):
    priced_trip = trip.copy()
    priced_trip["distance"] = estimate_route_distance(priced_trip["source"], priced_trip["destination"])
    priced_trip["price"] = calculate_trip_price(priced_trip["source"], priced_trip["destination"], priced_trip["mode"])
    return priced_trip


def build_generated_trip(source, destination, mode):
    route_key = f"{source.lower()}-{destination.lower()}-{mode.lower()}"
    seed = sum(ord(char) for char in route_key)
    distance = estimate_route_distance(source, destination)
    duration_divisor = {"Flight": 520, "Train": 90, "Bus": 55}[mode]
    rating = round(4.1 + ((seed % 7) * 0.1), 1)
    duration_hours = max(1.0, round(distance / duration_divisor, 1))
    duration = f"{int(duration_hours)}h {int((duration_hours % 1) * 60):02d}m"
    description = (
        f"A {mode.lower()} journey from {source} to {destination} with comfortable scheduling, "
        f"reliable transfers, and a smooth booking flow."
    )

    return {
        "id": f"dynamic-{slugify(source)}-{slugify(destination)}-{mode.lower()}",
        "source": source.title(),
        "destination": destination.title(),
        "mode": mode,
        "duration": duration,
        "price": calculate_trip_price(source, destination, mode),
        "rating": min(rating, 4.8),
        "tag": MODE_TAGS[mode],
        "image": MODE_IMAGES[mode],
        "description": description,
        "offer": f"Flexible {mode.lower()} fare for your selected route",
    }


def get_dashboard_context(user):
    user_bookings = Booking.objects.filter(user=user)
    upcoming_booking = user_bookings.filter(status="confirmed", date__gte=timezone.localdate()).order_by("date").first()
    latest_booking = user_bookings.first()
    return {
        "greeting": get_greeting(),
        "user_display_name": user.first_name or user.username,
        "default_date": get_default_date(),
        "popular_destinations": TRIPS[:4],
        "recommended_trips": sorted(TRIPS, key=lambda item: (-item["rating"], item["price"]))[:3],
        "booking_count": user_bookings.count(),
        "confirmed_count": user_bookings.filter(status="confirmed").count(),
        "upcoming_booking": upcoming_booking,
        "latest_booking": latest_booking,
        "cheapest_trip": min(TRIPS, key=lambda item: item["price"]),
        "offers": [
            {"title": "New User Unlock", "description": "Flat 15% off on your first confirmed booking.", "code": "NEW15", "discount": "15%"},
            {"title": "Season Special", "description": "Up to 20% off on selected premium stays and flights.", "code": "SEASON20", "discount": "20%"},
            {"title": "Weekend Dash", "description": "Quick getaway deals for Friday departures and short stays.", "code": "WEEKEND10", "discount": "10%"},
        ],
        "hero_image": "https://images.unsplash.com/photo-1502920514313-52581002a659?auto=format&fit=crop&w=1600&q=80",
        "airline_options": DASHBOARD_AIRLINES,
        "hotel_options": DASHBOARD_HOTELS,
        "holiday_packages": DASHBOARD_HOLIDAYS,
        "smart_plans": DASHBOARD_SMART_PLANS,
        "trip_catalog_json": json.dumps(TRIPS),
    }


def build_planner_outline(days, budget, travel_style):
    total_days = max(1, days)
    style = travel_style.title()
    transport = "Bus" if budget <= 4500 else "Train" if budget <= 9000 else "Flight"
    hotel = {
        "Luxury": "Azure Grand Residences",
        "Budget": "CityLite Smart Stay",
        "Adventure": "TrailNest Explorer Camp",
    }.get(style, "CityLite Smart Stay")
    estimated_cost = int(max(budget * 0.88, total_days * 1800))
    itinerary = []

    for day in range(1, total_days + 1):
        if day == 1:
            headline = "Travel + Check-in"
            details = f"Arrive by {transport.lower()}, transfer to {hotel}, and settle in with a relaxed evening nearby."
        elif day == total_days:
            headline = "Return Journey"
            details = f"Keep the final day light, add one local stop, and return comfortably by {transport.lower()}."
        else:
            headline = "Explore & Local Experiences"
            if style == "Luxury":
                details = "Focus on premium sightseeing, curated dining, and a polished city experience."
            elif style == "Adventure":
                details = "Prioritize nature stops, active sightseeing, and a faster-paced travel day."
            else:
                details = "Balance key attractions with budget-friendly food, local transit, and a manageable pace."

        itinerary.append({"day": day, "headline": headline, "details": details})

    return {
        "estimated_cost": estimated_cost,
        "transport": transport,
        "hotel": hotel,
        "style": style,
        "days": itinerary,
    }


def build_search_results(source="", destination="", max_price=None, min_rating=None, mode=None):
    source_query = source.strip().lower()
    destination_query = destination.strip().lower()
    mode_query = (mode or "").strip().lower()
    results = []

    if source_query and destination_query:
        requested_modes = [mode.title()] if mode_query else ["Flight", "Train", "Bus"]
        curated_for_route = {
            trip["mode"]: trip for trip in TRIPS
            if trip["source"].lower() == source_query and trip["destination"].lower() == destination_query
        }

        for selected_mode in requested_modes:
            trip = curated_for_route.get(selected_mode) or build_generated_trip(source.strip(), destination.strip(), selected_mode)
            trip = with_search_result_pricing(trip)
            matches_price = max_price is None or trip["price"] <= max_price
            matches_rating = min_rating is None or trip["rating"] >= min_rating
            if matches_price and matches_rating:
                results.append(trip)
        return results

    for trip in TRIPS:
        trip = with_search_result_pricing(trip)
        matches_source = not source_query or source_query in trip["source"].lower()
        matches_destination = not destination_query or destination_query in trip["destination"].lower()
        matches_price = max_price is None or trip["price"] <= max_price
        matches_rating = min_rating is None or trip["rating"] >= min_rating
        matches_mode = not mode_query or trip["mode"].lower() == mode_query
        if matches_source and matches_destination and matches_price and matches_rating and matches_mode:
            results.append(trip)
    return results


def build_fallback_trip(source, destination, mode=""):
    if mode:
        return build_generated_trip(source.strip(), destination.strip(), mode.title())

    generated_options = [
        build_generated_trip(source.strip(), destination.strip(), selected_mode)
        for selected_mode in ["Bus", "Train", "Flight"]
    ]
    return sorted(generated_options, key=lambda item: item["price"])[0]


def suggest_trip_for_plan(budget, days):
    safe_budget = max(int(budget or 0), 1)
    safe_days = max(int(days or 1), 1)
    ceiling = safe_budget / safe_days

    within_budget = sorted(
        [trip for trip in TRIPS if trip["price"] <= safe_budget],
        key=lambda item: abs(item["price"] - ceiling),
    )

    fallback = sorted(
        TRIPS,
        key=lambda item: abs(item["price"] - safe_budget) + abs(item["rating"] - 4.4) * 1000,
    )

    match = within_budget[0] if within_budget else fallback[0]
    return {
        "trip": match,
        "is_fallback": not bool(within_budget),
    }


def build_tripura_itinerary(days, budget="medium", travel_type="solo"):
    normalized_days = days if days in TRIPURA_ITINERARIES else 5
    itinerary = []

    for index, day in enumerate(TRIPURA_ITINERARIES[normalized_days], start=1):
        places = []
        for place in day["places"]:
            description = place["description"]
            if budget == "low":
                description += " Keep transport simple and focus on budget-friendly local options."
            elif budget == "high":
                description += " Add premium stays or a more comfortable private transfer for this day."

            if travel_type == "family":
                description += " This stop is family-friendly with a comfortable pace."
            elif travel_type == "friends":
                description += " Great for group photos, shared outings, and a lively pace."
            elif travel_type == "solo":
                description += " Easy to cover solo with flexible timing and quiet exploration."

            places.append(
                {
                    "name": place["name"],
                    "description": description,
                }
            )

        itinerary.append(
            {
                "day": index,
                "title": day["title"],
                "icon": day["icon"],
                "places": places,
            }
        )

    return itinerary


def build_invoice_pdf(booking):
    subtotal = ((booking.price - CONVENIENCE_FEE) / (Decimal("1.00") + GST_RATE)).quantize(Decimal("0.01"))
    gst_amount = (subtotal * GST_RATE).quantize(Decimal("0.01"))

    def esc(value):
        return str(value).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    content_lines = [
        "0.96 0.97 0.99 rg",
        "36 710 540 60 re f",
        "0.10 0.17 0.30 rg",
        "BT /F2 24 Tf 48 748 Td (Tripora Travel Invoice) Tj ET",
        "0.38 0.43 0.50 rg",
        "BT /F1 11 Tf 48 728 Td (Professional booking invoice and payment receipt) Tj ET",

        "0.16 0.54 0.96 rg",
        "396 718 160 40 re f",
        "1 1 1 rg",
        f"BT /F2 12 Tf 414 734 Td (Booking ID: {esc(booking.booking_id)}) Tj ET",

        "0.93 0.95 0.98 rg",
        "36 580 540 110 re f",
        "0.10 0.17 0.30 rg",
        "BT /F2 14 Tf 48 670 Td (Traveler Details) Tj ET",
        f"BT /F1 11 Tf 48 646 Td (Traveler: {esc(booking.traveler_name)}) Tj ET",
        f"BT /F1 11 Tf 48 626 Td (Booked By: {esc(booking.user.username)}) Tj ET",
        f"BT /F1 11 Tf 48 606 Td (Passengers: {esc(booking.passengers)}) Tj ET",
        f"BT /F1 11 Tf 300 646 Td (Payment Method: {esc(booking.payment_method or 'Pending')}) Tj ET",
        f"BT /F1 11 Tf 300 626 Td (Status: {esc(booking.status.title())}) Tj ET",
        f"BT /F1 11 Tf 300 606 Td (Issued On: {esc(timezone.localtime(booking.created_at).strftime('%d %b %Y %I:%M %p'))}) Tj ET",

        "0.98 0.98 0.99 rg",
        "36 420 540 140 re f",
        "0.10 0.17 0.30 rg",
        "BT /F2 14 Tf 48 540 Td (Trip Details) Tj ET",
        f"BT /F1 11 Tf 48 516 Td (Route: {esc(booking.source)} to {esc(booking.destination)}) Tj ET",
        f"BT /F1 11 Tf 48 496 Td (Travel Date: {esc(booking.date.strftime('%d %b %Y'))}) Tj ET",
        f"BT /F1 11 Tf 48 476 Td (Booking Status: {esc(booking.status.title())}) Tj ET",

        "0.88 0.90 0.95 rg",
        "36 220 540 170 re f",
        "0.10 0.17 0.30 rg",
        "BT /F2 14 Tf 48 370 Td (Billing Summary) Tj ET",
        f"BT /F1 11 Tf 48 340 Td (Base Fare) Tj ET",
        f"BT /F2 11 Tf 470 340 Td (Rs. {esc(subtotal)}) Tj ET",
        f"BT /F1 11 Tf 48 312 Td (GST 5%) Tj ET",
        f"BT /F2 11 Tf 470 312 Td (Rs. {esc(gst_amount)}) Tj ET",
        f"BT /F1 11 Tf 48 284 Td (Convenience Fee) Tj ET",
        f"BT /F2 11 Tf 470 284 Td (Rs. {esc(CONVENIENCE_FEE)}) Tj ET",
        "0.16 0.54 0.96 rg",
        "48 246 516 2 re f",
        "0.10 0.17 0.30 rg",
        f"BT /F2 14 Tf 48 258 Td (Total Paid) Tj ET",
        f"BT /F2 14 Tf 446 258 Td (Rs. {esc(booking.price)}) Tj ET",

        "0.38 0.43 0.50 rg",
        "BT /F1 10 Tf 48 190 Td (This is a system-generated invoice from Tripora.) Tj ET",
        "BT /F1 10 Tf 48 174 Td (Please retain this copy for travel verification and billing support.) Tj ET",
    ]
    stream = "\n".join(content_lines).encode("latin-1", errors="replace")

    objects = []
    objects.append(b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n")
    objects.append(b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n")
    objects.append(
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R /F2 5 0 R >> >> /Contents 6 0 R >> endobj\n"
    )
    objects.append(b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n")
    objects.append(b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >> endobj\n")
    objects.append(f"6 0 obj << /Length {len(stream)} >> stream\n".encode("latin-1") + stream + b"\nendstream endobj\n")

    pdf = BytesIO()
    pdf.write(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(pdf.tell())
        pdf.write(obj)
    xref_start = pdf.tell()
    pdf.write(f"xref\n0 {len(offsets)}\n".encode("latin-1"))
    pdf.write(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.write(f"{offset:010d} 00000 n \n".encode("latin-1"))
    pdf.write(
        f"trailer << /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF".encode("latin-1")
    )
    return pdf.getvalue()


def calculate_booking_breakdown(base_price, passengers):
    passenger_count = max(1, passengers)
    base_total = (Decimal(str(base_price)) * passenger_count).quantize(Decimal("0.01"))
    gst_amount = (base_total * GST_RATE).quantize(Decimal("0.01"))
    total_amount = (base_total + gst_amount + CONVENIENCE_FEE).quantize(Decimal("0.01"))
    return {
        "base_total": base_total,
        "gst_amount": gst_amount,
        "convenience_fee": CONVENIENCE_FEE,
        "total_amount": total_amount,
    }


def landing(request):
    return render(request, "main/landing.html")


def loader(request):
    return render(request, "main/loader.html")


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        if not all([full_name, username, email, password, confirm_password]):
            messages.error(request, "Please complete all signup fields.")
        elif not is_valid_full_name(full_name):
            messages.error(request, "Enter a valid full name using letters only.")
        elif not is_letters_only_username(username):
            messages.error(request, "Username must be at least 5 letters long and contain only letters.")
        elif password != confirm_password:
            messages.error(request, "Passwords do not match.")
        elif not is_strong_password(password):
            messages.error(request, "Password must be 8+ characters with uppercase, lowercase, and a special character.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "That username is already taken.")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "That email is already registered.")
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            user.first_name = full_name
            user.save(update_fields=["first_name"])
            login(request, user)
            messages.success(request, "Your Tripora account is ready. Welcome aboard.")
            return redirect("dashboard")

    return render(request, "main/signup.html")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        if not is_letters_only_username(username):
            messages.error(request, "Username must be at least 5 letters long and contain only letters.")
        elif not is_strong_password(password):
            messages.error(request, "Enter a stronger password with uppercase, lowercase, and a special character.")
        else:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, "Login successful. Let's plan your next trip.")
                return redirect("dashboard")
            messages.error(request, "Invalid username or password.")

    return render(request, "main/login.html")


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("login")


@login_required
def dashboard(request):
    return render(request, "main/dashboard.html", get_dashboard_context(request.user))


@login_required
def search_hub(request):
    return render(request, "main/search_hub.html", get_dashboard_context(request.user))


@login_required
def explore_page(request):
    context = get_dashboard_context(request.user)
    context["explore_categories"] = [
        {"title": "Best Deals", "subtitle": "Lowest current fares", "trips": sorted(TRIPS, key=lambda item: item["price"])[:3]},
        {"title": "Combos", "subtitle": "Travel + stay inspired routes", "trips": TRIPS[1:4]},
        {"title": "Staycation", "subtitle": "Closer, slower escapes", "trips": TRIPS[:3]},
        {"title": "Weekend Trips", "subtitle": "2 to 3 day quick breaks", "trips": [TRIPS[0], TRIPS[3], TRIPS[4]]},
    ]
    return render(request, "main/explore.html", context)


@login_required
def planner_page(request):
    context = get_dashboard_context(request.user)
    context["planner_budget"] = "8000"
    context["planner_days"] = "4"
    context["planner_travel_style"] = "budget"

    if request.method == "POST":
        budget_raw = request.POST.get("budget", "8000").strip()
        days_raw = request.POST.get("days", "4").strip()
        travel_style = request.POST.get("travel_style", "budget").strip().lower()

        try:
            budget = int(budget_raw)
        except ValueError:
            budget = 8000

        try:
            days = int(days_raw)
        except ValueError:
            days = 4

        context["planner_budget"] = str(budget)
        context["planner_days"] = str(days)
        context["planner_travel_style"] = travel_style
        context["planner_suggestion"] = suggest_trip_for_plan(budget, days)
        context["planner_outline"] = build_planner_outline(days, budget, travel_style)

    return render(request, "main/planner.html", context)


@login_required
def itinerary_api(request):
    try:
        days = int(request.GET.get("days", "5"))
    except ValueError:
        days = 5

    budget = request.GET.get("budget", "medium").lower()
    travel_type = request.GET.get("travel_type", "solo").lower()

    itinerary = build_tripura_itinerary(days, budget, travel_type)
    return JsonResponse(
        {
            "days": days,
            "budget": budget,
            "travel_type": travel_type,
            "itinerary": itinerary,
        }
    )


@login_required
def assistant_page(request):
    return render(request, "main/assistant.html", get_dashboard_context(request.user))


@login_required
def search_results(request):
    source = request.GET.get("source", "")
    destination = request.GET.get("destination", "")
    travel_date = request.GET.get("date") or get_default_date()
    max_price_raw = request.GET.get("max_price", "")
    min_rating_raw = request.GET.get("min_rating", "")
    mode = request.GET.get("mode", "")

    try:
        max_price = int(max_price_raw) if max_price_raw else None
    except ValueError:
        max_price = None

    try:
        min_rating = float(min_rating_raw) if min_rating_raw else None
    except ValueError:
        min_rating = None

    results = build_search_results(source, destination, max_price, min_rating, mode)
    fallback_notice = ""

    if source.strip() and destination.strip() and not results:
        fallback_trip = build_fallback_trip(source, destination, mode)
        results = [fallback_trip]
        fallback_notice = (
            "No trip matched the current filters exactly, so we are showing the closest available route option."
        )

    context = {
        "results": results,
        "source": source,
        "destination": destination,
        "travel_date": travel_date,
        "max_price": max_price_raw,
        "min_rating": min_rating_raw,
        "mode": mode,
        "fallback_notice": fallback_notice,
    }
    request.session["search_trip_map"] = {trip["id"]: trip for trip in results}
    return render(request, "main/search_results.html", context)


@login_required
def booking_page(request, trip_id):
    trip = get_trip_by_id(trip_id) or get_trip_from_session(request, trip_id)
    if not trip:
        messages.error(request, "We couldn't find that trip anymore.")
        return redirect("search_hub")

    travel_date = request.GET.get("date") or request.POST.get("date") or get_default_date()
    traveler_name = ""
    passengers = 1

    if request.method == "POST":
        traveler_name = request.POST.get("traveler_name", "").strip()
        passengers_raw = request.POST.get("passengers", "1").strip()
        try:
            passengers = int(passengers_raw)
        except ValueError:
            passengers = 0

        try:
            parsed_date = datetime.strptime(travel_date, "%Y-%m-%d").date()
        except ValueError:
            parsed_date = timezone.localdate() + timedelta(days=7)

        if not traveler_name:
            messages.error(request, "Please enter the primary traveler name.")
        elif not re.fullmatch(r"[A-Za-z ]+", traveler_name) or len(traveler_name.replace(" ", "")) < 3:
            messages.error(request, "Traveler name must be at least 3 characters and contain only letters and spaces.")
        elif passengers < 1 or passengers > 20:
            messages.error(request, "Passengers must be between 1 and 20.")
        else:
            pricing = calculate_booking_breakdown(trip["price"], passengers)
            booking = Booking.objects.create(
                user=request.user,
                booking_id=f"TRP{uuid4().hex[:8].upper()}",
                trip_id=trip["id"],
                traveler_name=traveler_name,
                passengers=passengers,
                source=trip["source"],
                destination=trip["destination"],
                date=parsed_date,
                price=pricing["total_amount"],
                status="confirmed",
            )
            return redirect("payment_page", booking_id=booking.id)

    pricing = calculate_booking_breakdown(trip["price"], passengers if 1 <= passengers <= 20 else 1)
    context = {
        "trip": trip,
        "travel_date": travel_date,
        "initial_traveler_name": traveler_name,
        "initial_passengers": passengers if 1 <= passengers <= 20 else 1,
        "pricing": pricing,
    }
    return render(request, "main/booking.html", context)


@login_required
def payment_page(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    if booking.status == "cancelled":
        messages.error(request, "Cancelled bookings cannot be paid.")
        return redirect("booking_history")

    if request.method == "POST":
        payment_method = request.POST.get("payment_method", "Card")
        booking.payment_method = payment_method
        booking.status = "confirmed"
        booking.save(update_fields=["payment_method", "status"])
        messages.success(request, "Payment simulated successfully. Your booking is confirmed.")
        return redirect("invoice_page", booking_id=booking.id)

    return render(request, "main/payment.html", {"booking": booking})


@login_required
def invoice_page(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    trip = get_trip_by_id(booking.trip_id)
    return render(request, "main/invoice.html", {"booking": booking, "trip": trip})


@login_required
def download_invoice_pdf(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    pdf_bytes = build_invoice_pdf(booking)
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="tripora-invoice-{booking.booking_id}.pdf"'
    return response


@login_required
def booking_history(request):
    bookings = Booking.objects.filter(user=request.user)
    return render(request, "main/history.html", {"bookings": bookings})


@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    if request.method == "POST" and booking.status != "cancelled":
        booking.status = "cancelled"
        booking.save(update_fields=["status"])
        messages.info(request, f"Booking {booking.booking_id} has been cancelled.")
    return redirect("booking_history")
