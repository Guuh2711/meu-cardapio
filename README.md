services:
  - type: web
    name: meu-cardapio
    env: python
    buildCommand: ""
    startCommand: "python app.py"
    envVars:
      - key: OPENAI_API_KEY
        value: SUA_CHAVE_OPENAI
      - key: STRIPE_SECRET_KEY
        value: SUA_CHAVE_STRIPE
      - key: YOUR_DOMAIN
        value: https://meu-cardapio-aluo.onrender.com
      - key: PORT
        value: 10000
