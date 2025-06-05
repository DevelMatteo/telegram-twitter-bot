# Bot Telegram - Fabrizio Romano Tweet Reposter

Bot Telegram che monitora automaticamente i tweet di Fabrizio Romano e li riposta sui canali Telegram registrati.

## 💰 GRATIS - Nessun Costo API!
✅ **Web scraping tramite Nitter** - Non usa le API di Twitter a pagamento  
✅ **Completamente gratuito** - Nessun limite di tweet o costi nascosti  
✅ **Affidabile** - Usa multiple istanze Nitter per garantire disponibilità

## 🚀 Deploy su Render

### 1. Preparazione
- Assicurati di avere un bot Telegram creato tramite @BotFather
- Ottieni il token del bot

### 2. Configurazione su Render
1. Vai su [render.com](https://render.com) e crea un account
2. Clicca su "New +" → "Web Service"
3. Connetti il tuo repository GitHub
4. Configura il servizio:
   - **Name**: `fabrizio-romano-bot` (o nome a tua scelta)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn twitter_telegram_bot:app`

### 3. Variabili d'ambiente
Aggiungi queste variabili d'ambiente su Render:

- `TELEGRAM_BOT_TOKEN`: Il token del tuo bot Telegram
- `WEBHOOK_URL`: L'URL del tuo servizio Render (es: `https://fabrizio-romano-bot.onrender.com`)
- `PORT`: `10000` (Render usa questa porta di default)

### 4. Deploy
- Clicca su "Create Web Service"
- Render farà automaticamente il deploy

## 🔧 Problemi Risolti

### Error 409 (Conflict)
- ✅ Sostituito `infinity_polling()` con webhook
- ✅ Aggiunto server Flask per gestire le richieste

### No Open Ports
- ✅ Aggiunto server web che espone la porta richiesta da Render
- ✅ Configurato Gunicorn come server WSGI

## 📱 Come Usare il Bot

1. Aggiungi il bot al tuo canale/gruppo Telegram
2. Dai al bot i permessi per scrivere messaggi
3. Il bot inizierà automaticamente a monitorare i tweet di Fabrizio Romano
4. Riceverai i nuovi tweet ogni 10 minuti

### Comandi Disponibili
- `/start` - Informazioni sul bot
- `/stop` - Disattiva il bot per il canale corrente
- `/status` - Mostra lo stato del bot

## 🔍 Monitoraggio

- Il bot controlla nuovi tweet ogni 10 minuti
- Usa istanze Nitter pubbliche per evitare limitazioni di Twitter
- Mantiene traccia dei tweet già pubblicati per evitare duplicati

## 📊 Endpoints

- `GET /` - Status del bot e informazioni
- `GET /health` - Health check per Render
- `POST /{TELEGRAM_BOT_TOKEN}` - Webhook per Telegram

## 🛠️ Tecnologie Utilizzate

- **Python 3.11+**
- **Flask** - Server web
- **pyTelegramBotAPI** - Libreria Telegram
- **BeautifulSoup4** - Web scraping
- **Gunicorn** - Server WSGI per produzione
- **Render** - Hosting cloud

## 🎯 Vantaggi del Web Scraping

- **Nessun costo** - Le API di Twitter costano $100/mese, questo bot è gratis
- **Nessun limite** - Non ci sono limitazioni sui tweet che puoi monitorare
- **Indipendente** - Non dipende dalle politiche di pricing di Twitter/X
- **Resiliente** - Usa multiple istanze Nitter come backup

## 📝 Note

- Il bot usa web scraping tramite Nitter per ottenere i tweet
- I file JSON per tracciare canali e tweet vengono salvati localmente
- Il bot rimuove automaticamente canali non raggiungibili
- Perfetto per chi vuole un servizio gratuito e affidabile
