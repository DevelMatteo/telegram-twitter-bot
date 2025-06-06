import os
import time
import requests
from bs4 import BeautifulSoup
import telebot
from datetime import datetime
import json
import hashlib
import threading
from flask import Flask, request
import logging
import urllib3

# Disabilita gli avvisi SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configurazione - SICUREZZA: Token viene da variabile d'ambiente
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TWITTER_USERNAME = "fabrizioromano"  # Username Twitter (senza @)
WEBHOOK_URL = os.getenv('WEBHOOK_URL')  # URL del webhook per Render
PORT = int(os.getenv('PORT', 5000))  # Porta per Render

# Verifica che il token sia configurato
if not TELEGRAM_BOT_TOKEN:
    print("❌ ERRORE: TELEGRAM_BOT_TOKEN non configurato!")
    print("💡 Configura la variabile d'ambiente su Render")
    exit(1)

# Inizializza Flask app
app = Flask(__name__)

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inizializza il bot
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# File per tracciare i canali registrati e i tweet pubblicati
CHANNELS_FILE = "registered_channels.json"
POSTED_TWEETS_FILE = "posted_tweets.json"

def load_registered_channels():
    """Carica la lista dei canali registrati"""
    if os.path.exists(CHANNELS_FILE):
        with open(CHANNELS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_registered_channels(channels):
    """Salva la lista dei canali registrati"""
    with open(CHANNELS_FILE, 'w') as f:
        json.dump(channels, f, indent=2)

def load_posted_tweets():
    """Carica la lista dei tweet già pubblicati"""
    if os.path.exists(POSTED_TWEETS_FILE):
        with open(POSTED_TWEETS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_posted_tweets(posted_tweets):
    """Salva la lista dei tweet pubblicati"""
    with open(POSTED_TWEETS_FILE, 'w') as f:
        json.dump(posted_tweets, f)

def get_tweet_id(tweet_text, tweet_time):
    """Genera un ID unico per il tweet basato su contenuto e timestamp"""
    content = f"{tweet_text}_{tweet_time}"
    return hashlib.md5(content.encode()).hexdigest()

# Handler per quando il bot viene aggiunto a un gruppo/canale
@bot.message_handler(content_types=['new_chat_members'])
def handle_new_member(message):
    """Gestisce quando il bot viene aggiunto a un nuovo canale/gruppo"""
    for new_member in message.new_chat_members:
        if new_member.username == bot.get_me().username:
            chat_id = message.chat.id
            chat_title = message.chat.title or "Chat Privata"
            
            # Registra il canale
            channels = load_registered_channels()
            
            # Controlla se il canale è già registrato
            if not any(ch['chat_id'] == chat_id for ch in channels):
                channels.append({
                    'chat_id': chat_id,
                    'chat_title': chat_title,
                    'added_date': datetime.now().isoformat()
                })
                save_registered_channels(channels)
                
                bot.send_message(
                    chat_id,
                    f"🎉 **Bot attivato!**\n\n"
                    f"Ciao! Sono il bot che ripubblica i tweet di @{TWITTER_USERNAME}.\n"
                    f"📢 Da ora in poi riceverete automaticamente tutti i suoi nuovi tweet!\n\n"
                    f"**Comandi disponibili:**\n"
                    f"/start - Informazioni sul bot\n"
                    f"/stop - Disattiva il bot per questo canale\n"
                    f"/status - Stato del bot",
                    parse_mode='Markdown'
                )
                logger.info(f"✅ Nuovo canale registrato: {chat_title} (ID: {chat_id})")

# Handler per il comando /start
@bot.message_handler(commands=['start'])
def handle_start(message):
    """Gestisce il comando /start"""
    # Se è un canale/gruppo, registralo automaticamente
    if message.chat.type in ['group', 'supergroup', 'channel']:
        chat_id = message.chat.id
        chat_title = message.chat.title or "Chat Senza Nome"
        
        channels = load_registered_channels()
        
        # Controlla se il canale è già registrato
        if not any(ch['chat_id'] == chat_id for ch in channels):
            channels.append({
                'chat_id': chat_id,
                'chat_title': chat_title,
                'added_date': datetime.now().isoformat()
            })
            save_registered_channels(channels)
            logger.info(f"✅ Canale registrato via /start: {chat_title} (ID: {chat_id})")
    
    bot.reply_to(
        message,
        f"🤖 **Bot Tweet @{TWITTER_USERNAME}**\n\n"
        f"Questo bot ripubblica automaticamente tutti i tweet di @{TWITTER_USERNAME}.\n\n"
        f"**Per usarlo:**\n"
        f"1️⃣ Aggiungimi al tuo canale/gruppo\n"
        f"2️⃣ Dammi i permessi per scrivere messaggi\n"
        f"3️⃣ Usa /register per registrare questo canale\n\n"
        f"**Comandi:**\n"
        f"/start - Mostra queste informazioni\n"
        f"/register - Registra questo canale\n"
        f"/stop - Disattiva per questo canale\n"
        f"/status - Stato del servizio",
        parse_mode='Markdown'
    )

# Handler per il comando /register
@bot.message_handler(commands=['register'])
def handle_register(message):
    """Registra manualmente il canale corrente"""
    chat_id = message.chat.id
    chat_title = message.chat.title or f"Chat {chat_id}"
    
    channels = load_registered_channels()
    
    # Controlla se il canale è già registrato
    if any(ch['chat_id'] == chat_id for ch in channels):
        bot.reply_to(
            message,
            "✅ **Canale già registrato!**\n\n"
            "Questo canale riceve già i tweet automaticamente.",
            parse_mode='Markdown'
        )
        return
    
    # Registra il canale
    channels.append({
        'chat_id': chat_id,
        'chat_title': chat_title,
        'added_date': datetime.now().isoformat()
    })
    save_registered_channels(channels)
    
    bot.reply_to(
        message,
        f"🎉 **Canale registrato con successo!**\n\n"
        f"📢 **Canale:** {chat_title}\n"
        f"🐦 **Monitoraggio:** @{TWITTER_USERNAME}\n"
        f"⏰ **Controllo:** Ogni 10 minuti\n\n"
        f"Da ora riceverai automaticamente tutti i nuovi tweet!",
        parse_mode='Markdown'
    )
    logger.info(f"✅ Canale registrato manualmente: {chat_title} (ID: {chat_id})")

# Handler per il comando /stop
@bot.message_handler(commands=['stop'])
def handle_stop(message):
    """Disattiva il bot per il canale corrente"""
    chat_id = message.chat.id
    channels = load_registered_channels()
    
    # Rimuovi il canale dalla lista
    channels = [ch for ch in channels if ch['chat_id'] != chat_id]
    save_registered_channels(channels)
    
    bot.reply_to(
        message,
        "👋 **Bot disattivato**\n\n"
        "Non riceverai più i tweet automaticamente.\n"
        "Usa /register per riattivare il servizio.",
        parse_mode='Markdown'
    )
    logger.info(f"❌ Canale rimosso: {message.chat.title} (ID: {chat_id})")

# Handler per il comando /status
@bot.message_handler(commands=['status'])
def handle_status(message):
    """Mostra lo stato del bot"""
    channels = load_registered_channels()
    total_channels = len(channels)
    
    is_registered = any(ch['chat_id'] == message.chat.id for ch in channels)
    status_emoji = "✅" if is_registered else "❌"
    status_text = "Attivo" if is_registered else "Non attivo"
    
    bot.reply_to(
        message,
        f"📊 **Status Bot**\n\n"
        f"{status_emoji} **Stato in questo canale:** {status_text}\n"
        f"📢 **Canali totali attivi:** {total_channels}\n"
        f"🐦 **Account monitorato:** @{TWITTER_USERNAME}\n"
        f"⏰ **Ultimo controllo:** In corso...\n\n"
        f"Il bot controlla nuovi tweet ogni 10 minuti.",
        parse_mode='Markdown'
    )

def scrape_twitter_rss(username):
    """
    Metodo alternativo: usa RSS feed di Nitter
    """
    tweets = []
    
    # Lista di istanze Nitter con RSS
    rss_instances = [
        "https://nitter.cz",
        "https://nitter.poast.org",
        "https://nitter.privacydev.net",
        "https://nitter.net"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; RSS Reader)'
    }
    
    for instance in rss_instances:
        try:
            rss_url = f"{instance}/{username}/rss"
            logger.info(f"Tentativo RSS con {instance}...")
            
            response = requests.get(rss_url, headers=headers, timeout=15, verify=False)
            
            if response.status_code == 200:
                from xml.etree import ElementTree as ET
                
                try:
                    root = ET.fromstring(response.content)
                    items = root.findall('.//item')
                    
                    for item in items[:5]:
                        title = item.find('title')
                        pub_date = item.find('pubDate')
                        description = item.find('description')
                        
                        if title is not None and title.text:
                            tweet_text = title.text.strip()
                            tweet_time = pub_date.text if pub_date is not None else "Data sconosciuta"
                            
                            tweets.append({
                                'text': tweet_text,
                                'time': tweet_time,
                                'images': [],
                                'id': get_tweet_id(tweet_text, tweet_time)
                            })
                    
                    if tweets:
                        logger.info(f"✅ Trovati {len(tweets)} tweet via RSS da {instance}")
                        return tweets
                        
                except ET.ParseError as e:
                    logger.error(f"Errore parsing RSS da {instance}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Errore RSS con {instance}: {e}")
            continue
    
    return []

def scrape_twitter_nitter(username):
    """
    Scraping dei tweet usando Nitter (frontend alternativo a Twitter)
    """
    tweets = []
    
    # Prima prova con RSS (più affidabile)
    tweets = scrape_twitter_rss(username)
    if tweets:
        return tweets
    
    # Se RSS fallisce, usa scraping HTML
    logger.info("RSS fallito, provo con scraping HTML...")
    
    # Lista aggiornata di istanze Nitter funzionanti
    nitter_instances = [
        "https://nitter.cz",
        "https://nitter.poast.org",
        "https://nitter.privacydev.net", 
        "https://nitter.net",
        "https://nitter.it",
        "https://nitter.fdn.fr",
        "https://nitter.1d4.us",
        "https://nitter.kavin.rocks",
        "https://nitter.unixfox.eu",
        "https://nitter.domain.glass",
        "https://nitter.eu",
        "https://nitter.namazso.eu",
        "https://bird.trom.tf",
        "https://nitter.moomoo.me",
        "https://nitter.fly.dev"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    for instance in nitter_instances:
        try:
            url = f"{instance}/{username}"
            logger.info(f"Tentativo con {instance}...")
            
            # Prova prima con SSL, poi senza se fallisce
            try:
                response = requests.get(url, headers=headers, timeout=20)
            except:
                response = requests.get(url, headers=headers, timeout=20, verify=False)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Prova diversi selettori per i tweet (le strutture cambiano)
                tweet_containers = (
                    soup.find_all('div', class_='timeline-item') or
                    soup.find_all('div', class_='tweet') or
                    soup.find_all('article') or
                    soup.find_all('div', attrs={'data-tweet-id': True})
                )
                
                if not tweet_containers:
                    logger.warning(f"Nessun contenuto tweet trovato su {instance}")
                    continue
                
                for container in tweet_containers[:5]:  # Prendi solo gli ultimi 5 tweet
                    try:
                        # Prova diversi selettori per il contenuto del tweet
                        tweet_content = (
                            container.find('div', class_='tweet-content') or
                            container.find('div', class_='tweet-text') or
                            container.find('p') or
                            container.find('div', class_='content')
                        )
                        
                        if tweet_content:
                            tweet_text = tweet_content.get_text().strip()
                            
                            if not tweet_text or len(tweet_text) < 10:
                                continue
                            
                            # Prova diversi selettori per il timestamp
                            time_element = (
                                container.find('span', class_='tweet-date') or
                                container.find('time') or
                                container.find('span', class_='date') or
                                container.find('a', class_='tweet-link')
                            )
                            
                            if time_element:
                                tweet_time = time_element.get_text().strip() or time_element.get('datetime', 'Data sconosciuta')
                            else:
                                tweet_time = "Data sconosciuta"
                            
                            # Estrai eventuali link alle immagini
                            images = []
                            img_elements = container.find_all('img')
                            for img in img_elements:
                                if img.get('src') and ('pic.twitter.com' in img.get('src', '') or 'attachment' in img.get('class', [])):
                                    img_url = img['src']
                                    if img_url.startswith('/'):
                                        img_url = f"{instance}{img_url}"
                                    images.append(img_url)
                            
                            tweets.append({
                                'text': tweet_text,
                                'time': tweet_time,
                                'images': images,
                                'id': get_tweet_id(tweet_text, tweet_time)
                            })
                    
                    except Exception as e:
                        logger.error(f"Errore nell'estrazione del tweet: {e}")
                        continue
                
                if tweets:
                    logger.info(f"✅ Trovati {len(tweets)} tweet con {instance}")
                    return tweets
                else:
                    logger.warning(f"Nessun tweet valido estratto da {instance}")
                    
        except Exception as e:
            logger.error(f"Errore con {instance}: {e}")
            continue
    
    # Se nessuna istanza Nitter funziona, crea un tweet di test per verificare che il sistema funzioni
    logger.warning("⚠️ Nessuna istanza Nitter disponibile - creazione tweet di test")
    test_tweet = {
        'text': f"🔧 Test del bot - Monitoraggio di @{username} attivo ma istanze Nitter temporaneamente non disponibili. Il servizio riprenderà automaticamente quando le istanze torneranno online.",
        'time': datetime.now().strftime("%Y-%m-%d %H:%M"),
        'images': [],
        'id': get_tweet_id("test_tweet", str(datetime.now()))
    }
    return [test_tweet]

def format_tweet_for_telegram(tweet):
    """Formatta il tweet per Telegram"""
    message = f"🐦 **Nuovo Tweet di @{TWITTER_USERNAME}**\n\n"
    message += f"{tweet['text']}\n\n"
    message += f"📅 {tweet['time']}"
    
    return message

def send_tweet_to_all_channels(tweet):
    """Invia il tweet a tutti i canali registrati"""
    channels = load_registered_channels()
    successful_sends = 0
    failed_channels = []
    
    message = format_tweet_for_telegram(tweet)
    
    for channel in channels:
        try:
            chat_id = channel['chat_id']
            
            # Se ci sono immagini, invia la prima come foto con il testo
            if tweet['images']:
                bot.send_photo(
                    chat_id=chat_id,
                    photo=tweet['images'][0],
                    caption=message,
                    parse_mode='Markdown'
                )
            else:
                bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode='Markdown'
                )
            
            successful_sends += 1
            time.sleep(1)  # Pausa per evitare rate limiting
            
        except Exception as e:
            logger.error(f"Errore nell'invio al canale {channel['chat_title']}: {e}")
            failed_channels.append(channel['chat_id'])
    
    # Rimuovi i canali che hanno dato errore (probabilmente bot rimosso)
    if failed_channels:
        channels = [ch for ch in channels if ch['chat_id'] not in failed_channels]
        save_registered_channels(channels)
        logger.info(f"Rimossi {len(failed_channels)} canali non raggiungibili")
    
    return successful_sends

def tweet_monitor():
    """Funzione che monitora i tweet (da eseguire in thread separato)"""
    logger.info(f"🚀 Avvio monitoraggio tweet per @{TWITTER_USERNAME}")
    
    # Carica i tweet già pubblicati
    posted_tweets = load_posted_tweets()
    
    while True:
        try:
            logger.info("🔍 Controllo nuovi tweet...")
            
            # Ottieni i tweet più recenti
            tweets = scrape_twitter_nitter(TWITTER_USERNAME)
            
            if not tweets:
                logger.warning("❌ Nessun tweet trovato")
                time.sleep(600)  # Aspetta 10 minuti
                continue
            
            new_tweets_count = 0
            channels = load_registered_channels()
            
            if not channels:
                logger.info("📭 Nessun canale registrato, salto l'invio")
                time.sleep(600)
                continue
            
            # Controlla ogni tweet
            for tweet in reversed(tweets):  # Dal più vecchio al più nuovo
                if tweet['id'] not in posted_tweets:
                    logger.info(f"📤 Nuovo tweet trovato: {tweet['text'][:50]}...")
                    
                    # Invia il tweet a tutti i canali
                    successful_sends = send_tweet_to_all_channels(tweet)
                    
                    if successful_sends > 0:
                        posted_tweets.append(tweet['id'])
                        new_tweets_count += 1
                        logger.info(f"✅ Tweet inviato a {successful_sends} canali")
                        
                        # Pausa tra i tweet
                        time.sleep(10)
                    else:
                        logger.error("❌ Errore nell'invio del tweet")
            
            # Salva la lista aggiornata
            if new_tweets_count > 0:
                save_posted_tweets(posted_tweets)
                logger.info(f"💾 Processati {new_tweets_count} nuovi tweet")
            else:
                logger.info("📝 Nessun nuovo tweet da pubblicare")
            
            # Mantieni solo gli ultimi 200 ID per evitare file troppo grandi
            if len(posted_tweets) > 200:
                posted_tweets = posted_tweets[-200:]
                save_posted_tweets(posted_tweets)
            
        except Exception as e:
            logger.error(f"❌ Errore nel monitoraggio: {e}")
        
        # Aspetta 10 minuti prima del prossimo controllo
        logger.info(f"⏰ Prossimo controllo tra 10 minuti... ({len(load_registered_channels())} canali attivi)")
        time.sleep(600)

# Flask routes per Render
@app.route('/')
def index():
    """Route principale per verificare che il servizio sia attivo"""
    return {
        "status": "Bot attivo",
        "bot_username": f"@{TWITTER_USERNAME}",
        "canali_attivi": len(load_registered_channels()),
        "timestamp": datetime.now().isoformat()
    }

@app.route('/health')
def health():
    """Health check per Render"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.route('/webhook-info')
def webhook_info():
    """Verifica lo stato del webhook"""
    try:
        webhook_info = bot.get_webhook_info()
        return {
            "webhook_url": webhook_info.url,
            "has_custom_certificate": webhook_info.has_custom_certificate,
            "pending_update_count": webhook_info.pending_update_count,
            "last_error_date": webhook_info.last_error_date,
            "last_error_message": webhook_info.last_error_message,
            "max_connections": webhook_info.max_connections,
            "allowed_updates": webhook_info.allowed_updates,
            "configured_webhook_url": WEBHOOK_URL,
            "bot_token_configured": bool(TELEGRAM_BOT_TOKEN),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e), "timestamp": datetime.now().isoformat()}

@app.route('/test-bot')
def test_bot():
    """Testa se il bot funziona"""
    try:
        bot_info = bot.get_me()
        return {
            "bot_username": bot_info.username,
            "bot_id": bot_info.id,
            "bot_first_name": bot_info.first_name,
            "can_join_groups": bot_info.can_join_groups,
            "can_read_all_group_messages": bot_info.can_read_all_group_messages,
            "supports_inline_queries": bot_info.supports_inline_queries,
            "status": "Bot funzionante",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e), "status": "Bot non funzionante", "timestamp": datetime.now().isoformat()}

@app.route(f'/{TELEGRAM_BOT_TOKEN}', methods=['POST'])
def webhook():
    """Webhook per ricevere messaggi da Telegram"""
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        return 'Bad Request', 400

def setup_webhook():
    """Configura il webhook per Telegram"""
    if WEBHOOK_URL:
        webhook_url = f"{WEBHOOK_URL}/{TELEGRAM_BOT_TOKEN}"
        try:
            # Rimuovi webhook esistenti e ferma polling
            bot.remove_webhook()
            bot.stop_polling()
            time.sleep(3)
            
            # Configura nuovo webhook
            result = bot.set_webhook(url=webhook_url)
            if result:
                logger.info(f"✅ Webhook configurato: {webhook_url}")
                
                # Verifica che il webhook sia attivo
                webhook_info = bot.get_webhook_info()
                logger.info(f"📡 Webhook info: {webhook_info.url}")
                return True
            else:
                logger.error("❌ Errore nella configurazione del webhook")
                return False
        except Exception as e:
            logger.error(f"❌ Errore nel setup webhook: {e}")
            return False
    else:
        logger.warning("⚠️ WEBHOOK_URL non configurato")
        return False

def start_polling_fallback():
    """Avvia polling come fallback se webhook non funziona"""
    def polling_thread():
        try:
            logger.info("🔄 Avvio polling fallback...")
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            logger.error(f"Errore nel polling: {e}")
    
    polling = threading.Thread(target=polling_thread, daemon=True)
    polling.start()

def main():
    """Funzione principale"""
    logger.info("🤖 Avvio Bot Telegram Multi-Canale per Render")
    logger.info(f"📢 Account Twitter monitorato: @{TWITTER_USERNAME}")
    logger.info(f"🌐 Porta: {PORT}")
    
    # Avvia il monitoraggio tweet in un thread separato
    tweet_thread = threading.Thread(target=tweet_monitor, daemon=True)
    tweet_thread.start()
    
    # Configura webhook se siamo su Render, altrimenti usa polling
    if WEBHOOK_URL:
        webhook_success = setup_webhook()
        if webhook_success:
            logger.info("🌐 Modalità webhook attiva")
        else:
            logger.warning("⚠️ Webhook fallito, uso polling")
            start_polling_fallback()
    else:
        logger.info("🔄 Modalità polling attiva (sviluppo)")
        start_polling_fallback()

# Avvia automaticamente quando importato da Gunicorn
logger.info("🚀 Inizializzazione automatica")
main()

if __name__ == "__main__":
    # Verifica che il token sia configurato
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN non configurato!")
        exit(1)
    
    # Avvia Flask solo se eseguito direttamente
    logger.info("🚀 Server Flask attivo (modalità sviluppo)")
    app.run(host='0.0.0.0', port=PORT, debug=False)
