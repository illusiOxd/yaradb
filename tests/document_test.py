from models.models_init.document_init import create_document

# 1. Создаем документ
user_data = {
    "username": "alice",
    "email": "alice@example.com",
    "level": 99
}
doc = create_document(
    name="user_account",
    body=user_data
)

# 2. Используем новые "удобные" функции

# (а) Легко получаем ID
print(f"ID Документа: {doc.get_id_str()}")

# (б) Легко получаем данные из 'body'
username = doc.get("username")
print(f"Имя пользователя: {username}")

# (в) Проверяем поле, которого нет (безопасно)
non_existent = doc.get("last_login")
print(f"Последний логин: {non_existent}") # Выведет: None

# (г) Получаем "красивый" вывод для логов
print("\n--- Полный документ (pretty) ---")
print(doc.pretty())