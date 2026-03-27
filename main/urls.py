from django.urls import path

from . import views


urlpatterns = [
    path('', views.landing, name='landing'),
    path('loader/', views.loader, name='loader'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('search-hub/', views.search_hub, name='search_hub'),
    path('explore/', views.explore_page, name='explore_page'),
    path('planner/', views.planner_page, name='planner_page'),
    path('api/itinerary/', views.itinerary_api, name='itinerary_api'),
    path('assistant/', views.assistant_page, name='assistant_page'),
    path('search/', views.search_results, name='search_results'),
    path('booking/<slug:trip_id>/', views.booking_page, name='booking_page'),
    path('payment/<int:booking_id>/', views.payment_page, name='payment_page'),
    path('invoice/<int:booking_id>/', views.invoice_page, name='invoice_page'),
    path('invoice/<int:booking_id>/download/', views.download_invoice_pdf, name='download_invoice_pdf'),
    path('history/', views.booking_history, name='booking_history'),
    path('cancel-booking/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
]
