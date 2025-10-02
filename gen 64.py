import base64

# Исходное сообщение
message = "Капибара на омене, ты не туда спайк поставил"

# Кодирование в Base64
encoded = base64.b64encode(message.encode('utf-8')).decode('ascii')

print(encoded)