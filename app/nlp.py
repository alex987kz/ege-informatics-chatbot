"""Распознавание темы вопроса на русском языке.

Порядок проверки: номер телефона, TF-IDF с косинусным сходством,
ключевые слова, ключевые слова с одной опечаткой.
"""

import re

import nltk
from nltk.metrics.distance import edit_distance
from nltk.stem.snowball import SnowballStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.knowledge import COMPANY, FALLBACK, KNOWLEDGE_BASE

# Ниже этого сходства считаем, что похожего примера нет.
SIMILARITY_THRESHOLD = 0.65

# Запасной список, если корпус NLTK не удалось скачать.
BASIC_STOP_WORDS = {
    "и", "в", "во", "не", "что", "он", "на", "я", "с", "со", "как", "а", "то",
    "все", "она", "так", "его", "но", "да", "ты", "к", "у", "же", "вы", "за",
    "бы", "по", "ее", "мне", "было", "вот", "от", "меня", "еще", "нет", "о",
    "из", "ему", "теперь", "даже", "ну", "ли", "если", "уже", "или", "быть",
    "был", "него", "до", "вас", "нибудь", "опять", "уж", "вам", "ведь", "там",
}


def load_stop_words():
    for attempt in range(2):
        try:
            return set(nltk.corpus.stopwords.words("russian"))
        except LookupError:
            if attempt == 0:
                nltk.download("stopwords", quiet=True)
    print("Внимание: корпус стоп-слов NLTK недоступен, взят сокращённый список.")
    return BASIC_STOP_WORDS


# Стеммер отбрасывает окончания: «уроки» и «уроков» дают основу «урок».
stemmer = SnowballStemmer("russian")
STOP_WORDS = load_stop_words()


def tokenize(text):
    """Слова в нижнем регистре, без знаков препинания."""
    return re.findall(r"[а-яa-z0-9]+", text.lower().replace("ё", "е"))


def normalize(text):
    """Основы слов без стоп-слов."""
    stems = []
    for word in tokenize(text):
        if word not in STOP_WORDS:
            stems.append(stemmer.stem(word))
    return stems


# Подготовка при запуске: ответы, основы ключевых слов и TF-IDF-матрица примеров.
answers = {}
keyword_stems = {}
examples = []
example_topics = []
for item in KNOWLEDGE_BASE:
    answers[item["topic"]] = item["answer"]
    keyword_stems[item["topic"]] = [stemmer.stem(word) for word in item["keywords"]]
    for example in item["examples"]:
        examples.append(example)
        example_topics.append(item["topic"])

vectorizer = TfidfVectorizer(analyzer=normalize)
example_vectors = vectorizer.fit_transform(examples)


def find_phone(text):
    """Номер из 10 цифр или из 11, начиная с 7 или 8."""
    digits = re.sub(r"\D", "", text)
    if len(digits) == 10 or (len(digits) == 11 and digits[0] in "78"):
        return digits
    return None


def is_typo(word, key):
    """Одна лишняя, пропущенная или неверная буква. Короткие слова не сравниваем."""
    return len(word) >= 5 and len(key) >= 5 and edit_distance(word, key) <= 1


def find_by_keywords(stems, allow_typo):
    """Тема с наибольшим числом совпавших ключевых слов и сами совпадения."""
    best_topic, best_keys = None, []
    for topic, keys in keyword_stems.items():
        found = []
        for key in keys:
            if key in stems:
                found.append(key)
            elif allow_typo and any(is_typo(stem, key) for stem in stems):
                found.append(key)
        if len(found) > len(best_keys):
            best_topic, best_keys = topic, found
    return best_topic, best_keys


def analyze(text):
    """Возвращает тему (или None) и список шагов распознавания."""
    steps = [f"Слова после токенизации: {', '.join(tokenize(text)) or '—'}"]

    phone = find_phone(text)
    if phone:
        steps.append(f"Правило: распознан номер телефона ({phone})")
        return "phone", steps

    stems = normalize(text)
    steps.append(f"Основы без стоп-слов: {', '.join(stems) or '—'}")

    # Сравниваем вектор фразы со всеми примерами и берём самый похожий.
    similarity = cosine_similarity(vectorizer.transform([text]), example_vectors)[0]
    best = similarity.argmax()
    if similarity[best] >= SIMILARITY_THRESHOLD:
        steps.append(f"Правило: TF-IDF и косинусное сходство — {similarity[best]:.2f}")
        return example_topics[best], steps
    steps.append(f"TF-IDF: сходство {similarity[best]:.2f} ниже порога {SIMILARITY_THRESHOLD}")

    topic, keys = find_by_keywords(stems, allow_typo=False)
    if topic:
        steps.append(f"Правило: совпали ключевые слова — {', '.join(keys)}")
        return topic, steps
    steps.append("Ключевые слова: совпадений нет")

    topic, keys = find_by_keywords(stems, allow_typo=True)
    if topic:
        steps.append(f"Правило: расстояние Левенштейна — {', '.join(keys)}")
        return topic, steps
    steps.append("Опечатки: совпадений нет, тема не распознана")
    return None, steps


def get_answer(topic):
    return answers.get(topic, FALLBACK)


if __name__ == "__main__":
    print(f"Чат-бот: {COMPANY}. Для выхода напишите «пока».")
    while True:
        topic, steps = analyze(input("Вы: "))
        print("Бот:", get_answer(topic))
        if topic == "bye":
            break
