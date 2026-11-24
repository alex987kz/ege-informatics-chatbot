"""Тесты распознавания тем — стандартный unittest.

Запуск всех тестов проекта (и этих, и тестов веб-сервиса):

    python -m unittest -v

Подсчёт фраз: 49 основных + 17 переформулировок + 4 с опечатками
+ 3 нераспознаваемых + 1 известный промах = 74 фразы.
"""

import unittest

from app.knowledge import FALLBACK
from app.nlp import analyze, get_answer


def find_topic(phrase):
    return analyze(phrase)[0]


# Пары «фраза пользователя — ожидаемая тема».
MAIN_CASES = [
    ("Привет!", "greeting"),
    ("Здравствуйте, есть вопрос", "greeting"),
    ("Добрый день", "greeting"),
    ("Что ты умеешь?", "help"),
    ("На какие вопросы отвечаешь?", "help"),
    ("По какому предмету учите?", "subject"),
    ("Какой предмет?", "subject"),
    ("Какая программа курса?", "program"),
    ("Что входит в программу?", "program"),
    ("Кто преподает?", "teacher"),
    ("Кто ведет курс?", "teacher"),
    ("Кто будет преподавать?", "teacher"),
    ("Какой средний балл учеников?", "results"),
    ("Какие результаты у учеников?", "results"),
    ("Сколько стоит обучение?", "price"),
    ("Какая цена курса?", "price"),
    ("Какие темы входят в обучение?", "topics"),
    ("Какие темы я буду изучать?", "topics"),
    ("Что изучается на курсе?", "topics"),
    ("В каком формате проходит обучение?", "platform"),
    ("Как построено обучение?", "platform"),
    ("Что предоставляет площадка?", "platform"),
    ("Есть ли личный кабинет?", "platform"),
    ("Вебинары в записи или живые?", "platform"),
    ("Есть ли записи занятий?", "platform"),
    ("Когда начинается курс?", "schedule"),
    ("Какое расписание занятий?", "schedule"),
    ("Есть ли пробный урок?", "trial"),
    ("Можно ли попробовать бесплатно?", "trial"),
    ("Подойдет ли курс если я с нуля?", "level"),
    ("Сложно ли будет новичку?", "level"),
    ("Есть ли домашние задания?", "homework"),
    ("Кто проверяет домашку?", "homework"),
    ("Сколько хранится доступ к материалам?", "access"),
    ("Какой срок доступа?", "access"),
    ("Как записаться на курс?", "enroll"),
    ("Хочу купить курс", "enroll"),
    ("+7 000 000-00-00", "phone"),
    ("мой телефон 8 000 000 00 00", "phone"),
    ("Есть ли скидки?", "discount"),
    ("Можно ли в рассрочку?", "discount"),
    ("Можно ли вернуть деньги?", "guarantee"),
    ("Есть ли гарантия возврата?", "guarantee"),
    ("Как с вами связаться?", "contacts"),
    ("Дайте телефон", "contacts"),
    ("Спасибо большое", "thanks"),
    ("Пока", "bye"),
    ("До свидания", "bye"),
]

# Переформулировки: этих слов нет в ключевых словах тем,
# тему находит косинусное сходство с примерами вопросов (TF-IDF).
PARAPHRASE_CASES = [
    ("Чему вы учите?", "subject"),
    ("Какой предмет преподаёте?", "subject"),
    ("Вы учите информатике или математике?", "subject"),
    ("Расскажите про учителя", "teacher"),
    ("Сколько денег нужно?", "price"),
    ("Это онлайн или офлайн?", "platform"),
    ("Что есть на платформе кроме уроков?", "platform"),
    ("Когда ближайший поток?", "schedule"),
    ("Хочу посмотреть демо урока", "trial"),
    ("Я в десятом классе мне подойдет", "level"),
    ("Как проходит практика после уроков?", "homework"),
    ("Можно ли пересматривать уроки?", "access"),
    ("Как оставить заявку?", "enroll"),
    ("Предусмотрена ли рассрочка?", "discount"),
    ("Как вернуть деньги за курс?", "guarantee"),
    ("Хочу поговорить с менеджером", "contacts"),
    # Две темы в одной фразе: бот отвечает только на одну.
    ("Здравствуйте! Какая цена?", "greeting"),
]

# Опечатки: тему находит расстояние Левенштейна.
TYPO_CASES = [
    ("Превет", "greeting"),
    ("Сколько стоет обучение", "price"),
    ("Какие темы входят в обучение", "topics"),
    ("Есть ли пробны урок", "trial"),
]

# Фразы, на которые бот обязан ответить заглушкой.
UNKNOWN_CASES = [
    "Сколько лететь до Марса?",
    "Как дела с квантовой физикой?",
    "asdfgh",
]


class TestMainQuestions(unittest.TestCase):
    """Основные вопросы по всем темам базы знаний."""

    def test_main_questions(self):
        for phrase, expected in MAIN_CASES:
            with self.subTest(phrase=phrase):
                self.assertEqual(find_topic(phrase), expected)


class TestParaphrases(unittest.TestCase):
    """Переформулировки — распознаёт TF-IDF и косинусное сходство."""

    def test_paraphrases(self):
        for phrase, expected in PARAPHRASE_CASES:
            with self.subTest(phrase=phrase):
                self.assertEqual(find_topic(phrase), expected)


class TestTypos(unittest.TestCase):
    """Опечатки в одну букву — распознаёт расстояние Левенштейна."""

    def test_typos(self):
        for phrase, expected in TYPO_CASES:
            with self.subTest(phrase=phrase):
                self.assertEqual(find_topic(phrase), expected)


class TestPhoneEnroll(unittest.TestCase):
    """Сценарий записи: телефон в разных форматах даёт тему phone."""

    def test_phone_formats(self):
        for phrase in ["+7 000 000-00-00", "мой телефон 8 000 000 00 00"]:
            with self.subTest(phrase=phrase):
                topic = find_topic(phrase)
                self.assertEqual(topic, "phone")
                self.assertIn("зафиксировал", get_answer(find_topic(phrase)))


class TestUnknownQuestions(unittest.TestCase):
    """Нераспознанные фразы дают тему None и ответ-заглушку."""

    def test_fallback(self):
        for phrase in UNKNOWN_CASES:
            with self.subTest(phrase=phrase):
                self.assertIsNone(find_topic(phrase))
                self.assertEqual(get_answer(find_topic(phrase)), FALLBACK)


class TestKnownLimitation(unittest.TestCase):
    """Известное ограничение, оставленное в проекте намеренно.

    Две опечатки в одном слове («препадает») не распознаются: порог
    нечёткого поиска — одна буква, а допуск в две буквы давал бы
    ложные срабатывания («пока» и «почта»). Поэтому тест помечен
    expectedFailure: он честно показывает границу метода.
    """

    @unittest.expectedFailure
    def test_double_typo_is_not_recognized(self):
        self.assertEqual(find_topic("Кто препадает"), "teacher")


if __name__ == "__main__":
    unittest.main()
