import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import time

class MarketMoodBot:
    def __init__(self):
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.base_url = f"https://api.telegram.org/bot{self.telegram_token}"
        
    def fetch_tickertape_data(self):
        """Fetch market mood data from TickerTape"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get('https://www.tickertape.in/market-mood-index', headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for market mood index value and sentiment
            mood_data = {}
            
            # Try to find the main mood index value
            mood_elements = soup.find_all(['div', 'span'], class_=lambda x: x and ('mood' in x.lower() or 'index' in x.lower()))
            
            # Look for numerical values that might be the mood index
            for element in soup.find_all(['div', 'span', 'p']):
                text = element.get_text(strip=True)
                if any(keyword in text.lower() for keyword in ['mood', 'fear', 'greed', 'sentiment']):
                    mood_data['raw_text'] = text
                    break
            
            # Try to extract any percentage or numerical values
            import re
            numbers = re.findall(r'\b\d+(?:\.\d+)?%?\b', str(soup))
            if numbers:
                mood_data['values'] = numbers[:5]  # Get first 5 numbers found
            
            return mood_data
            
        except Exception as e:
            return {'error': f'TickerTape fetch failed: {str(e)}'}
    
    def fetch_goodreturns_data(self):
        """Fetch market mood data from GoodReturns"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get('https://www.goodreturns.in/market-mood-index.html', headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            mood_data = {}
            
            # Look for market mood related content
            for element in soup.find_all(['div', 'span', 'p', 'h1', 'h2', 'h3']):
                text = element.get_text(strip=True)
                if any(keyword in text.lower() for keyword in ['market mood', 'fear', 'greed', 'sentiment', 'index']):
                    mood_data['content'] = text
                    break
            
            # Extract numerical values
            import re
            numbers = re.findall(r'\b\d+(?:\.\d+)?%?\b', str(soup))
            if numbers:
                mood_data['values'] = numbers[:5]
            
            return mood_data
            
        except Exception as e:
            return {'error': f'GoodReturns fetch failed: {str(e)}'}
    
    def format_message(self, tickertape_data, goodreturns_data):
        """Format the market mood data into a nice Telegram message"""
        current_time = datetime.now().strftime("%d %B %Y, %I:%M %p")
        
        message = f"📊 *Market Mood Index Update*\n"
        message += f"🕐 {current_time}\n\n"
        
        # TickerTape Data
        message += "📈 *TickerTape Data:*\n"
        if 'error' in tickertape_data:
            message += f"❌ {tickertape_data['error']}\n"
        else:
            if 'raw_text' in tickertape_data:
                message += f"📊 {tickertape_data['raw_text']}\n"
            if 'values' in tickertape_data:
                message += f"🔢 Key Values: {', '.join(tickertape_data['values'])}\n"
        
        message += "\n"
        
        # GoodReturns Data
        message += "📈 *GoodReturns Data:*\n"
        if 'error' in goodreturns_data:
            message += f"❌ {goodreturns_data['error']}\n"
        else:
            if 'content' in goodreturns_data:
                message += f"📊 {goodreturns_data['content'][:200]}...\n"
            if 'values' in goodreturns_data:
                message += f"🔢 Key Values: {', '.join(goodreturns_data['values'])}\n"
        
        message += "\n💡 *Market Sentiment Analysis will be updated based on the above data*"
        
        return message
    
    def send_telegram_message(self, message):
        """Send message to Telegram"""
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, data=data, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            print(f"Failed to send Telegram message: {e}")
            return None
    
    def run(self):
        """Main execution function"""
        print(f"Starting Market Mood Bot at {datetime.now()}")
        
        # Fetch data from both sources
        print("Fetching TickerTape data...")
        tickertape_data = self.fetch_tickertape_data()
        
        print("Fetching GoodReturns data...")
        goodreturns_data = self.fetch_goodreturns_data()
        
        # Format and send message
        message = self.format_message(tickertape_data, goodreturns_data)
        print("Sending Telegram message...")
        
        result = self.send_telegram_message(message)
        
        if result:
            print("✅ Message sent successfully!")
        else:
            print("❌ Failed to send message")
        
        return result

def main():
    """Main function to run the bot"""
    bot = MarketMoodBot()
    bot.run()

if __name__ == "__main__":
    main()
