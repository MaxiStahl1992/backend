from django.test import TestCase
from unittest.mock import patch, MagicMock
from .openai_service import get_openai_response
from .models import OpenAIModel
from .enums import Temperature
import requests

# Service Test Case
class OpenAIServiceTests(TestCase):

    def setUp(self):
        """Set up a default active model for testing."""
        self.default_model = OpenAIModel.objects.create(
            name="gpt-4o",
            endpoint="/openai/deployments/gpt-4o/chat/completions?api-version=2024-06-01",
            active=True
        )
    
    @patch("api.openai_service.requests.post")
    def test_return_value_with_message_only(self, mock_post):
        """Test that get_openai_response returns a value when only a message is provided."""
        mock_post.return_value = MagicMock(status_code=200)
        mock_post.return_value.json.return_value = {"choices": [{"message": {"content": "Mocked response"}}]}

        response = get_openai_response(messages=[{"role": "user", "content": "Hello"}])

        self.assertIn("choices", response)
        self.assertEqual(response["choices"][0]["message"]["content"], "Mocked response")

    @patch("api.openai_service.requests.post")
    def test_return_value_with_message_and_temperature(self, mock_post):
        """Test that get_openai_response returns a value when a message and temperature are provided."""
        mock_post.return_value = MagicMock(status_code=200)
        mock_post.return_value.json.return_value = {"choices": [{"message": {"content": "Mocked response"}}]}

        response = get_openai_response(
            messages=[{"role": "user", "content": "Hello"}],
            temperature=Temperature.HIGH.value
        )

        self.assertIn("choices", response)
        self.assertEqual(response["choices"][0]["message"]["content"], "Mocked response")

    @patch("api.openai_service.requests.post")
    def test_return_value_with_message_and_model(self, mock_post):
        """Test that get_openai_response returns a value when a specific model and message are provided."""
        mock_post.return_value = MagicMock(status_code=200)
        mock_post.return_value.json.return_value = {"choices": [{"message": {"content": "Mocked response"}}]}

        response = get_openai_response(
            messages=[{"role": "user", "content": "Hello"}],
            model_name="gpt-4o"
        )

        self.assertIn("choices", response)
        self.assertEqual(response["choices"][0]["message"]["content"], "Mocked response")

    def test_model_does_not_exist_error(self):
        """Test that get_openai_response raises a ValueError when an invalid model is specified."""
        with self.assertRaises(ValueError) as context:
            get_openai_response(
                messages=[{"role": "user", "content": "Hello"}],
                model_name="non_existent_model"
            )

        self.assertEqual(str(context.exception), "The specified model does not exist or is inactive.")

    @patch("api.openai_service.requests.post")
    def test_openai_api_request_failed_error(self, mock_post):
        """Test that get_openai_response raises an error if the API request fails."""
        mock_post.side_effect = requests.exceptions.RequestException("Mocked API error")

        with self.assertRaises(requests.exceptions.RequestException) as context:
            get_openai_response(messages=[{"role": "user", "content": "Hello"}])

        self.assertIn("Mocked API error", str(context.exception))