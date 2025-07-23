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
            
            mood_data = {'mmi': None, 'mood': None}
            
            # Extract MMI value and mood from the page text
            page_text = soup.get_text()
            
            # Extract MMI value using regex - look for patterns like "52.92" or "47.01"
            import re
            
            # Look for MMI value - typically appears as a decimal number
            mmi_patterns = [
                r'MMI changed from\s*\d+\.\d+\s*(\d+\.\d+)',  # From the "MMI changed from X Y" pattern
                r'(\d+\.\d+)(?=\s*NIFTY returned)',  # Number before "NIFTY returned"
                r'MMI.*?(\d+\.\d+)',  # Any decimal after MMI mention
            ]
            
            for pattern in mmi_patterns:
                match = re.search(pattern, page_text)
                if match:
                    mood_data['mmi'] = match.group(1)
                    break
            
            # Extract mood - look for fear/greed indicators
            mood_patterns = [
                r'MMI is in the (\w+) zone',  # "MMI is in the greed zone"
                r'market is in the (\w+) zone',  # "market is in the greed zone"
                r'(fear|greed|neutral)(?:\s+zone)?',  # Direct fear/greed mentions
            ]
            
            for pattern in mood_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    mood_value = match.group(1).lower()
                    if mood_value in ['fear', 'greed', 'neutral']:
                        mood_data['mood'] = mood_value.title()
                        break
            
            # Fallback: if no specific mood found, determine from MMI value
            if mood_data['mmi'] and not mood_data['mood']:
                mmi_val = float(mood_data['mmi'])
                if mmi_val < 25:
                    mood_data['mood'] = 'Extreme Fear'
                elif mmi_val < 45:
                    mood_data['mood'] = 'Fear'
                elif mmi_val < 55:
                    mood_data['mood'] = 'Neutral'
                elif mmi_val < 75:
                    mood_data['mood'] = 'Greed'
                else:
                    mood_data['mood'] = 'Extreme Greed'
            
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
        
        # TickerTape Data - Clean format
        if 'error' in tickertape_data:
            message += f"❌ Error: {tickertape_data['error']}\n"
        else:
            if tickertape_data.get('mmi') and tickertape_data.get('mood'):
                message += f"📈 *MMI: {tickertape_data['mmi']}*\n"
                message += f"🎯 *Mood: {tickertape_data['mood']}*\n"
            else:
                message += "❌ Could not extract MMI data from TickerTape\n"
        
        message += "\n📍 Source: TickerTape Market Mood Index"
        
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
        
        # Fetch data from TickerTape only
        print("Fetching TickerTape data...")
        tickertape_data = self.fetch_tickertape_data()
        
        # Format and send message
        message = self.format_message(tickertape_data, {})
        print("Sending Telegram message...")
        
        result = self.send_telegram_message(message)
        
        if result:
            print("✅ Message sent successfully!")
            print(f"MMI: {tickertape_data.get('mmi', 'N/A')}")
            print(f"Mood: {tickertape_data.get('mood', 'N/A')}")
        else:
            print("❌ Failed to send message")
        
        return result

def main():
    """Main function to run the bot"""
    bot = MarketMoodBot()
    bot.run()

if __name__ == "__main__":
    main()
