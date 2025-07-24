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
            page_text = soup.get_text()
            
            mood_data = {'mmi': None, 'mood': None, 'source': 'TickerTape'}
            
            import re
            
            # Extract MMI value - look for the pattern "MMI changed from X Y"
            mmi_pattern = r'MMI changed from\s+[\d\.]+\s+([\d\.]+)'
            match = re.search(mmi_pattern, page_text)
            if match:
                mood_data['mmi'] = match.group(1)
            
            # If above pattern doesn't work, try alternative patterns
            if not mood_data['mmi']:
                # Look for number before "NIFTY returned"
                nifty_pattern = r'([\d\.]+)\s+NIFTY returned'
                match = re.search(nifty_pattern, page_text)
                if match:
                    mood_data['mmi'] = match.group(1)
            
            # Extract mood from "MMI is in the X zone"
            mood_pattern = r'MMI is in the (\w+) zone'
            match = re.search(mood_pattern, page_text, re.IGNORECASE)
            if match:
                mood_data['mood'] = match.group(1).title()
            
            # Fallback mood detection
            if not mood_data['mood'] and mood_data['mmi']:
                try:
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
                except:
                    pass
            
            return mood_data
            
        except Exception as e:
            return {'error': f'TickerTape fetch failed: {str(e)}', 'source': 'TickerTape'}
    
    def fetch_goodreturns_data(self):
        """Fetch market mood data from GoodReturns"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get('https://www.goodreturns.in/market-mood-index.html', headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            page_text = soup.get_text()
            
            mood_data = {'mmi': None, 'mood': None, 'source': 'GoodReturns'}
            
            import re
            
            # Look for MMI value patterns in GoodReturns
            mmi_patterns = [
                r'MMI[:\s]+(\d+\.?\d*)',  # MMI: 47.01 or MMI 47.01
                r'Market Mood Index[:\s]+(\d+\.?\d*)',  # Market Mood Index: 47.01
                r'Index[:\s]+(\d+\.?\d*)',  # Index: 47.01
                r'(\d+\.?\d+)\s*(?:MMI|Index)',  # 47.01 MMI or 47.01 Index
            ]
            
            for pattern in mmi_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    mood_data['mmi'] = match.group(1)
                    break
            
            # Look for mood indicators
            mood_keywords = ['fear', 'greed', 'neutral', 'extreme fear', 'extreme greed']
            for keyword in mood_keywords:
                if keyword.lower() in page_text.lower():
                    mood_data['mood'] = keyword.title()
                    break
            
            # Try to find specific mood patterns
            mood_patterns = [
                r'(Extreme Fear|Fear|Neutral|Greed|Extreme Greed)',
                r'Market is in\s+(\w+)',
                r'Sentiment[:\s]+(\w+)',
            ]
            
            for pattern in mood_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    mood_data['mood'] = match.group(1).title()
                    break
            
            # Fallback mood calculation from MMI value
            if mood_data['mmi'] and not mood_data['mood']:
                try:
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
                except:
                    pass
            
            return mood_data
            
        except Exception as e:
            return {'error': f'GoodReturns fetch failed: {str(e)}', 'source': 'GoodReturns'}
    
    def format_message(self, tickertape_data, goodreturns_data):
        """Format the market mood data into a nice Telegram message"""
        current_time = datetime.now().strftime("%d %B %Y, %I:%M %p")
        
        message = f"📊 *Market Mood Index Update*\n"
        message += f"🕐 {current_time}\n\n"
        
        # TickerTape Data
        message += "🎯 *TickerTape Data:*\n"
        if 'error' in tickertape_data:
            message += f"❌ {tickertape_data['error']}\n"
        else:
            if tickertape_data.get('mmi') and tickertape_data.get('mood'):
                message += f"📈 MMI: *{tickertape_data['mmi']}*\n"
                message += f"😊 Mood: *{tickertape_data['mood']}*\n"
            else:
                message += "❌ Could not extract complete data\n"
        
        message += "\n"
        
        # GoodReturns Data
        message += "🎯 *GoodReturns Data:*\n"
        if 'error' in goodreturns_data:
            message += f"❌ {goodreturns_data['error']}\n"
        else:
            if goodreturns_data.get('mmi') and goodreturns_data.get('mood'):
                message += f"📈 MMI: *{goodreturns_data['mmi']}*\n"
                message += f"😊 Mood: *{goodreturns_data['mood']}*\n"
            else:
                message += "❌ Could not extract complete data\n"
        
        message += "\n📍 *Sources:* TickerTape & GoodReturns"
        message += "\n💡 *Note:* Different sources may show slight variations"
        
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
            print(f"TickerTape - MMI: {tickertape_data.get('mmi', 'N/A')}, Mood: {tickertape_data.get('mood', 'N/A')}")
            print(f"GoodReturns - MMI: {goodreturns_data.get('mmi', 'N/A')}, Mood: {goodreturns_data.get('mood', 'N/A')}")
        else:
            print("❌ Failed to send message")
        
        return result

def main():
    """Main function to run the bot"""
    bot = MarketMoodBot()
    bot.run()

if __name__ == "__main__":
    main()
