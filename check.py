import google.generativeai as genai

# Вставь сюда свой реальный API-ключ вместо звездочек
genai.configure(api_key="AIzaSyDEk-y_3RLifmLBzcRa-UepRRrEovQRcoU")

print("Доступные модели:")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)