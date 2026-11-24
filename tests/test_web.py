"""Проверка страницы чата и отправки сообщений без запуска сервера."""

import unittest

from fastapi.testclient import TestClient

from app.knowledge import COMPANY, FALLBACK
from app.main import app
from app.nlp import answers as ANSWERS


class WebChatTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def test_chat_page(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])
        self.assertIn(COMPANY, response.text)
        self.assertIn('id="chat-form"', response.text)
        self.assertIn(ANSWERS["greeting"], response.text)

    def test_known_messages(self):
        for message, topic in [
            ("  Привет!  ", "greeting"),
            ("Сколько стоит?", "price"),
            ("Пока", "bye"),
            ("Какая программа курса?", "program"),
        ]:
            with self.subTest(message=message):
                response = self.client.post("/chat", json={"message": message})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["answer"], ANSWERS[topic])
                self.assertEqual(response.json()["topic"], topic)

    def test_unknown_message(self):
        response = self.client.post("/chat", json={"message": "Сколько лететь до Марса?"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["answer"], FALLBACK)
        self.assertIsNone(response.json()["topic"])

    def test_recognition_steps(self):
        response = self.client.post("/chat", json={"message": "Дайте телефон"})
        steps = response.json()["steps"]
        self.assertTrue(any("токенизации" in step for step in steps))
        self.assertTrue(any("Правило:" in step for step in steps))
        self.assertTrue(all(isinstance(step, str) for step in steps))

    def test_static_files(self):
        for path, content_type in [("/static/style.css", "text/css"),
                                   ("/static/chat.js", "javascript")]:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertIn(content_type, response.headers["content-type"])

    def test_empty_message(self):
        for message in ["", "   ", "\n\t"]:
            with self.subTest(message=message):
                response = self.client.post("/chat", json={"message": message})
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json()["detail"], "Введите сообщение.")

    def test_invalid_message(self):
        for data in [{}, {"message": 123}, {"message": "а" * 1001}]:
            with self.subTest(data=data):
                response = self.client.post("/chat", json=data)
                self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
