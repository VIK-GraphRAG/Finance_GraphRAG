"""
Real-time Financial Data Synchronization
실시간 재무 지표 동기화 (yfinance)
"""

import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Any
from neo4j import GraphDatabase
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD


class RealTimeDataSync:
    """
    Sync real-time financial data from Yahoo Finance to Neo4j
    """
    
    # Ticker mappings
    TICKERS = {
        'Nvidia': 'NVDA',
        'AMD': 'AMD',
        'TSMC': 'TSM',
        'Samsung Electronics': '005930.KS',
        'Philadelphia Semiconductor Index': '^SOX',
        'Taiwan Dollar': 'TWD=X',
        'KOSPI': '^KS11'
    }
    
    def __init__(self):
        self.driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
        )
    
    def close(self):
        """Close Neo4j connection"""
        self.driver.close()
    
    def fetch_ticker_data(self, ticker: str, period: str = '1d') -> Dict[str, Any]:
        """
        Fetch data from Yahoo Finance
        
        Args:
            ticker: Stock ticker (e.g., 'NVDA')
            period: Data period ('1d', '5d', '1mo', '3mo', '1y')
        
        Returns:
            {
                'price': float,
                'change': float,
                'change_percent': float,
                'volume': int,
                'market_cap': float,
                'timestamp': str
            }
        """
        
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            
            if hist.empty:
                print(f"⚠️  No data for {ticker}")
                return None
            
            latest = hist.iloc[-1]
            previous = hist.iloc[-2] if len(hist) > 1 else latest
            
            info = stock.info
            
            data = {
                'ticker': ticker,
                'price': float(latest['Close']),
                'open': float(latest['Open']),
                'high': float(latest['High']),
                'low': float(latest['Low']),
                'volume': int(latest['Volume']),
                'change': float(latest['Close'] - previous['Close']),
                'change_percent': float((latest['Close'] - previous['Close']) / previous['Close'] * 100),
                'market_cap': info.get('marketCap', 0),
                'timestamp': datetime.now().isoformat(),
                'date': latest.name.strftime('%Y-%m-%d')
            }
            
            return data
            
        except Exception as e:
            print(f"❌ Error fetching {ticker}: {e}")
            return None
    
    def update_company_financials(self, company_name: str, ticker_data: Dict):
        """Update company node with latest financial data"""
        
        query = f"""
        MATCH (c:Company {{name: '{company_name}'}})
        SET c.stock_price = {ticker_data['price']},
            c.price_change = {ticker_data['change']},
            c.price_change_pct = {ticker_data['change_percent']},
            c.volume = {ticker_data['volume']},
            c.market_cap_realtime = {ticker_data['market_cap']},
            c.last_sync = datetime('{ticker_data['timestamp']}')
        RETURN c.name as name, c.stock_price as price
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            record = result.single()
            if record:
                print(f"✅ {record['name']}: ${record['price']:.2f}")
            return record
    
    def create_market_indicator(self, name: str, ticker_data: Dict):
        """Create or update market indicator node"""
        
        query = f"""
        MERGE (m:MarketIndicator {{name: '{name}'}})
        SET m.value = {ticker_data['price']},
            m.change = {ticker_data['change']},
            m.change_percent = {ticker_data['change_percent']},
            m.last_updated = datetime('{ticker_data['timestamp']}'),
            m.ticker = '{ticker_data['ticker']}'
        RETURN m.name as name, m.value as value, m.change_percent as change_pct
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            record = result.single()
            if record:
                print(f"✅ {record['name']}: {record['value']:.2f} ({record['change_pct']:+.2f}%)")
            return record
    
    def sync_all(self) -> Dict[str, Any]:
        """Sync all configured tickers"""
        
        print(f"\n🔄 Syncing market data... ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
        
        results = {
            'companies': {},
            'indicators': {},
            'timestamp': datetime.now().isoformat(),
            'success': True
        }
        
        for name, ticker in self.TICKERS.items():
            data = self.fetch_ticker_data(ticker)
            
            if not data:
                continue
            
            # Company stocks
            if name in ['Nvidia', 'AMD', 'TSMC', 'Samsung Electronics']:
                record = self.update_company_financials(name, data)
                if record:
                    results['companies'][name] = {
                        'price': data['price'],
                        'change_pct': data['change_percent']
                    }
            
            # Market indicators
            else:
                record = self.create_market_indicator(name, data)
                if record:
                    results['indicators'][name] = {
                        'value': data['price'],
                        'change_pct': data['change_percent']
                    }
        
        print(f"\n✅ Sync complete: {len(results['companies'])} companies, {len(results['indicators'])} indicators")
        return results
    
    def get_market_sentiment(self) -> Dict[str, Any]:
        """
        Calculate market sentiment based on SOX index and stock performance
        """
        
        query = """
        MATCH (m:MarketIndicator {name: 'Philadelphia Semiconductor Index'})
        OPTIONAL MATCH (c:Company)
        WHERE c.price_change_pct IS NOT NULL
        RETURN m.change_percent as sox_change,
               avg(c.price_change_pct) as avg_stock_change,
               collect({name: c.name, change: c.price_change_pct}) as stocks
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            record = result.single()
            
            if not record:
                return {'sentiment': 'unknown', 'confidence': 0}
            
            sox_change = record['sox_change'] or 0
            avg_change = record['avg_stock_change'] or 0
            
            # Determine sentiment
            if sox_change > 2 and avg_change > 1:
                sentiment = 'bullish'
                confidence = 0.9
            elif sox_change > 0 and avg_change > 0:
                sentiment = 'positive'
                confidence = 0.7
            elif sox_change < -2 and avg_change < -1:
                sentiment = 'bearish'
                confidence = 0.9
            elif sox_change < 0 and avg_change < 0:
                sentiment = 'negative'
                confidence = 0.7
            else:
                sentiment = 'neutral'
                confidence = 0.5
            
            return {
                'sentiment': sentiment,
                'confidence': confidence,
                'sox_change': sox_change,
                'avg_stock_change': avg_change,
                'stocks': record['stocks']
            }
    
    def create_price_alert(
        self, 
        company: str, 
        threshold_pct: float = 5.0
    ) -> List[Dict]:
        """
        Check if any company has price change exceeding threshold
        """
        
        query = f"""
        MATCH (c:Company {{name: '{company}'}})
        WHERE abs(c.price_change_pct) > {threshold_pct}
        RETURN c.name as company,
               c.stock_price as price,
               c.price_change_pct as change_pct,
               c.last_sync as timestamp
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            alerts = []
            
            for record in result:
                alerts.append({
                    'company': record['company'],
                    'price': record['price'],
                    'change_pct': record['change_pct'],
                    'alert_type': 'surge' if record['change_pct'] > 0 else 'drop',
                    'severity': 'high' if abs(record['change_pct']) > 10 else 'medium'
                })
            
            return alerts


async def scheduled_sync(interval_minutes: int = 30):
    """
    Run data sync on schedule
    
    Args:
        interval_minutes: Sync interval (default: 30 minutes during market hours)
    """
    
    syncer = RealTimeDataSync()
    
    while True:
        try:
            # Sync data
            results = syncer.sync_all()
            
            # Check market sentiment
            sentiment = syncer.get_market_sentiment()
            print(f"\n📊 Market Sentiment: {sentiment['sentiment'].upper()} (confidence: {sentiment['confidence']:.1%})")
            print(f"   SOX Change: {sentiment['sox_change']:+.2f}%")
            print(f"   Avg Stock Change: {sentiment['avg_stock_change']:+.2f}%")
            
            # Check alerts
            for company in ['Nvidia', 'AMD', 'TSMC']:
                alerts = syncer.create_price_alert(company, threshold_pct=5.0)
                for alert in alerts:
                    print(f"\n⚠️  ALERT: {alert['company']} {alert['alert_type'].upper()}")
                    print(f"   Price: ${alert['price']:.2f} ({alert['change_pct']:+.2f}%)")
            
        except Exception as e:
            print(f"❌ Sync error: {e}")
        
        # Wait for next sync
        print(f"\n⏳ Next sync in {interval_minutes} minutes...")
        await asyncio.sleep(interval_minutes * 60)
    
    syncer.close()


def manual_sync():
    """One-time manual sync"""
    
    syncer = RealTimeDataSync()
    
    try:
        results = syncer.sync_all()
        
        sentiment = syncer.get_market_sentiment()
        print(f"\n📊 Market Sentiment: {sentiment['sentiment'].upper()}")
        
        return results
    finally:
        syncer.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--schedule':
        # Scheduled mode
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        print(f"🔄 Starting scheduled sync (every {interval} minutes)...")
        asyncio.run(scheduled_sync(interval))
    else:
        # One-time sync
        manual_sync()
