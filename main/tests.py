from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from .models import Booking


class TriporaSmokeTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.password = "tripora-pass-123"
        self.user = User.objects.create_user(
            username="tripora_user",
            email="tripora@example.com",
            password=self.password,
        )
        self.client.login(username=self.user.username, password=self.password)

    def test_main_authenticated_pages_render(self):
        pages = [
            reverse("dashboard"),
            reverse("search_hub"),
            reverse("explore_page"),
            reverse("planner_page"),
            reverse("assistant_page"),
            reverse("booking_history"),
        ]

        for page in pages:
            with self.subTest(page=page):
                response = self.client.get(page)
                self.assertEqual(response.status_code, 200)

    def test_search_returns_generated_trip_for_any_route(self):
        response = self.client.get(
            reverse("search_results"),
            {
                "source": "mumbai",
                "destination": "pune",
                "date": "2026-04-02",
                "mode": "Bus",
                "max_price": "8000",
                "min_rating": "4.0",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mumbai to Pune")
        self.assertContains(response, "Book")

    def test_planner_post_and_itinerary_api_both_work(self):
        planner_response = self.client.post(
            reverse("planner_page"),
            {
                "budget": "8000",
                "days": "4",
            },
        )
        self.assertEqual(planner_response.status_code, 200)
        self.assertContains(planner_response, "Best fit:")

        api_response = self.client.get(
            reverse("itinerary_api"),
            {
                "days": "5",
                "budget": "high",
                "travel_type": "family",
            },
        )
        self.assertEqual(api_response.status_code, 200)
        payload = api_response.json()
        self.assertEqual(payload["days"], 5)
        self.assertEqual(len(payload["itinerary"]), 5)

    def test_booking_payment_invoice_and_cancel_flow(self):
        self.client.get(
            reverse("search_results"),
            {
                "source": "mumbai",
                "destination": "pune",
                "date": "2026-04-02",
                "mode": "Bus",
            },
        )

        booking_get = self.client.get("/booking/dynamic-mumbai-pune-bus/?date=2026-04-02")
        self.assertEqual(booking_get.status_code, 200)

        booking_post = self.client.post(
            "/booking/dynamic-mumbai-pune-bus/?date=2026-04-02",
            {
                "traveler_name": "Tripora Tester",
                "passengers": "2",
                "date": "2026-04-02",
            },
        )
        self.assertEqual(booking_post.status_code, 302)

        booking = Booking.objects.get(user=self.user, traveler_name="Tripora Tester")
        self.assertRedirects(booking_post, reverse("payment_page", args=[booking.id]))

        payment_get = self.client.get(reverse("payment_page", args=[booking.id]))
        self.assertEqual(payment_get.status_code, 200)

        payment_post = self.client.post(
            reverse("payment_page", args=[booking.id]),
            {"payment_method": "UPI"},
        )
        self.assertRedirects(payment_post, reverse("invoice_page", args=[booking.id]))

        booking.refresh_from_db()
        self.assertEqual(booking.payment_method, "UPI")

        invoice_response = self.client.get(reverse("invoice_page", args=[booking.id]))
        self.assertEqual(invoice_response.status_code, 200)
        self.assertContains(invoice_response, "Tripora Travel Invoice")
        self.assertContains(invoice_response, booking.booking_id)

        pdf_response = self.client.get(reverse("download_invoice_pdf", args=[booking.id]))
        self.assertEqual(pdf_response.status_code, 200)
        self.assertEqual(pdf_response["Content-Type"], "application/pdf")

        cancel_response = self.client.post(reverse("cancel_booking", args=[booking.id]))
        self.assertRedirects(cancel_response, reverse("booking_history"))
        booking.refresh_from_db()
        self.assertEqual(booking.status, "cancelled")
