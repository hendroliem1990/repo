import pandas as pd
import numpy as np
from database import get_engine
import sqlalchemy
from datetime import datetime, timedelta
import ta
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

class StockRecommender:
    """AI-powered stock recommendation system based on trader profile"""

    def __init__(self, db_engine=None):
        self.engine = db_engine or get_engine()
        self.trader_profiles = {
            'conservative': {
                'volatility_weight': 0.3,
                'momentum_weight': 0.2,
                'volume_weight': 0.2,
                'fundamental_weight': 0.3,
                'max_volatility': 0.15,  # 15% max daily volatility
                'min_volume': 100000,   # Minimum daily volume
                'max_volume': 500000,   # Avoid heavy retail accumulation
                'min_market_cap': 1000000000000  # 1T IDR minimum
            },
            'moderate': {
                'volatility_weight': 0.25,
                'momentum_weight': 0.25,
                'volume_weight': 0.25,
                'fundamental_weight': 0.25,
                'max_volatility': 0.25,  # 25% max daily volatility
                'min_volume': 50000,    # Minimum daily volume
                'max_volume': 200000,   # Avoid heavy retail accumulation
                'min_market_cap': 500000000000   # 500B IDR minimum
            },
            'beginner_growth': {
                'volatility_weight': 0.15,
                'momentum_weight': 0.4,   # High weight on momentum (oversold rebounds)
                'volume_weight': 0.15,   # Lower volume preferred (avoid retail heavy)
                'fundamental_weight': 0.3, # Moderate fundamental weight
                'max_volatility': 0.5,   # High volatility for growth potential
                'min_volume': 5000,      # Low volume (avoid popular retail stocks)
                'max_volume': 50000,     # Maximum volume to avoid heavily accumulated
                'min_price': 50,         # Minimum price 50 IDR
                'max_price': 2000,       # Maximum price 2000 IDR
                'prefer_oversold': True  # Prefer stocks with RSI < 30
            },
            'aggressive': {
                'volatility_weight': 0.2,
                'momentum_weight': 0.3,
                'volume_weight': 0.3,
                'fundamental_weight': 0.2,
                'max_volatility': 0.4,   # 40% max daily volatility
                'min_volume': 10000,     # Minimum daily volume
                'max_volume': 300000,    # Avoid heavy retail accumulation while keeping momentum names
                'min_market_cap': 100000000000  # 100B IDR minimum
            }
        }

    def calculate_technical_score(self, df, profile='moderate'):
        """Calculate technical analysis score for a stock"""
        try:
            if len(df) < 50:  # Need minimum data
                return 0

            # Get recent data (last 3 months)
            recent_df = df.tail(60).copy()

            # Calculate technical indicators
            recent_df['SMA20'] = ta.trend.sma_indicator(recent_df['Close'], window=20)
            recent_df['SMA50'] = ta.trend.sma_indicator(recent_df['Close'], window=50)
            recent_df['RSI'] = ta.momentum.rsi(recent_df['Close'], window=14)
            recent_df['MACD'] = ta.trend.macd(recent_df['Close'])
            recent_df['MACD_signal'] = ta.trend.macd_signal(recent_df['Close'])

            # Calculate returns
            recent_df['Returns'] = recent_df['Close'].pct_change()
            recent_df['Volatility'] = recent_df['Returns'].rolling(20).std()

            # Get latest values
            latest = recent_df.iloc[-1]
            prev = recent_df.iloc[-2] if len(recent_df) > 1 else latest

            # Momentum score (0-100)
            momentum_score = 0

            # Trend following (SMA crossover)
            if latest['SMA20'] > latest['SMA50']:
                momentum_score += 30

            # RSI momentum - Special handling for beginner_growth
            if profile == 'beginner_growth':
                if latest['RSI'] < 30:
                    momentum_score += 40  # High score for oversold stocks
                elif latest['RSI'] < 40:
                    momentum_score += 25  # Good score for slightly oversold
                elif latest['RSI'] > 70:
                    momentum_score += 5   # Low score for overbought
                else:
                    momentum_score += 15  # Neutral score
            else:
                # Original RSI logic for other profiles
                if 40 <= latest['RSI'] <= 60:
                    momentum_score += 20  # Neutral, good for entry
                elif latest['RSI'] > 70:
                    momentum_score += 10  # Overbought but could continue
                elif latest['RSI'] < 30:
                    momentum_score += 15  # Oversold, potential bounce

            # MACD signal
            if latest['MACD'] > latest['MACD_signal']:
                momentum_score += 25  # Bullish
            else:
                momentum_score += 10  # Bearish

            # Recent performance (3-month return)
            three_month_return = (latest['Close'] / recent_df.iloc[0]['Close'] - 1) * 100
            if three_month_return > 10:
                momentum_score += 25
            elif three_month_return > 0:
                momentum_score += 15
            else:
                momentum_score += 5

            # Average volume to support retail filtering and volume score
            avg_volume = recent_df['Volume'].tail(20).mean()

            # Volume score (0-100)
            if profile == 'beginner_growth':
                # For beginner_growth: prefer medium-low volume (avoid retail heavy but not too illiquid)
                if 5000 <= avg_volume <= 50000:
                    volume_score = 100  # Perfect range
                elif 2000 <= avg_volume <= 100000:
                    volume_score = 70   # Acceptable range
                else:
                    volume_score = 30   # Too low or too high volume
            else:
                # Original volume scoring for other profiles
                volume_score = min(100, avg_volume / 100000 * 10)  # Scale volume score

            # Volatility score (0-100)
            current_volatility = latest['Volatility']
            profile_settings = self.trader_profiles[profile]

            if profile == 'beginner_growth':
                # For beginner_growth: higher volatility is better for growth potential
                if current_volatility >= 0.3:  # High volatility preferred
                    volatility_score = min(100, current_volatility * 200)
                elif current_volatility >= 0.2:
                    volatility_score = 70
                else:
                    volatility_score = max(0, current_volatility * 100)  # Low volatility gets lower score
            else:
                # Original volatility scoring for other profiles (lower volatility preferred)
                if current_volatility <= profile_settings['max_volatility']:
                    volatility_score = 100 * (1 - current_volatility / profile_settings['max_volatility'])
                else:
                    volatility_score = max(0, 50 - (current_volatility - profile_settings['max_volatility']) * 200)

            # Weighted score
            weights = profile_settings
            technical_score = (
                momentum_score * weights['momentum_weight'] +
                volume_score * weights['volume_weight'] +
                volatility_score * weights['volatility_weight']
            )

            return min(100, max(0, technical_score))

        except Exception as e:
            print(f"Error calculating technical score: {e}")
            return 0

    def calculate_fundamental_score(self, ticker, profile='moderate'):
        """Calculate fundamental score based on available data"""
        try:
            # Check if fundamental data exists
            fundamentals_table = f"{ticker}_fundamentals"
            inspector = sqlalchemy.inspect(self.engine)

            if fundamentals_table not in inspector.get_table_names():
                return 50  # Neutral score if no fundamentals

            # Get latest fundamental data
            query = f"""
            SELECT * FROM "{fundamentals_table}"
            ORDER BY date DESC
            LIMIT 1
            """
            fundamentals_df = pd.read_sql(query, self.engine)

            if fundamentals_df.empty:
                return 50

            latest_fund = fundamentals_df.iloc[0]

            fundamental_score = 50  # Base score

            # Market cap score - Different logic for beginner_growth
            if profile == 'beginner_growth':
                # For beginner_growth: prefer smaller companies with growth potential
                if 'market_cap' in latest_fund:
                    market_cap = latest_fund['market_cap']
                    if market_cap <= 1000000000000:  # Below 1T IDR (smaller companies)
                        fundamental_score += 30
                    elif market_cap <= 5000000000000:  # Below 5T IDR
                        fundamental_score += 20
                    else:
                        fundamental_score += 5  # Large caps get lower score
            else:
                # Original market cap logic for other profiles
                if 'market_cap' in latest_fund:
                    market_cap = latest_fund['market_cap']
                    profile_settings = self.trader_profiles[profile]

                    if market_cap >= profile_settings['min_market_cap']:
                        fundamental_score += 20
                    elif market_cap >= profile_settings['min_market_cap'] * 0.1:
                        fundamental_score += 10

            # PE ratio (reasonable valuation)
            if 'pe_ratio' in latest_fund and pd.notna(latest_fund['pe_ratio']):
                pe = latest_fund['pe_ratio']
                if 10 <= pe <= 25:
                    fundamental_score += 15
                elif 5 <= pe <= 40:
                    fundamental_score += 5

            # ROE (return on equity - profitability)
            if 'roe' in latest_fund and pd.notna(latest_fund['roe']):
                roe = latest_fund['roe']
                if roe > 15:
                    fundamental_score += 10
                elif roe > 10:
                    fundamental_score += 5

            return min(100, max(0, fundamental_score))

        except Exception as e:
            print(f"Error calculating fundamental score for {ticker}: {e}")
            return 50

    def get_stock_recommendations(self, profile='moderate', top_n=10, avoid_retail=False):
        """
        Get top N stock recommendations based on trader profile

        Args:
            profile (str): 'conservative', 'moderate', or 'aggressive'
            top_n (int): Number of recommendations to return
            avoid_retail (bool): Apply retail-heavy filtering

        Returns:
            pd.DataFrame: Top recommended stocks with scores
        """
        print(f"🔍 Analyzing stocks for {profile} trader profile...")

        # Get all available tickers from database
        inspector = sqlalchemy.inspect(self.engine)
        all_tables = inspector.get_table_names()

        # Filter to price data tables (exclude fundamentals, metadata, etc.)
        exclude_tables = ['corporate_actions', 'data_collection_metadata', 'test_table']
        price_tables = [t for t in all_tables if not t.endswith('_fundamentals') and t not in exclude_tables]

        print(f"📊 Found {len(price_tables)} stocks to analyze")

        recommendations = []

        for ticker in price_tables[:50]:  # Limit for performance, can be increased
            try:
                # Get price data
                query = f'SELECT * FROM "{ticker}" ORDER BY Date DESC LIMIT 200'
                df = pd.read_sql(query, self.engine)

                if len(df) < 50:  # Skip if insufficient data
                    continue

                # Convert date and sort
                df['Date'] = pd.to_datetime(df['Date'])
                df = df.sort_values('Date')

                # Calculate scores
                technical_score = self.calculate_technical_score(df, profile)
                fundamental_score = self.calculate_fundamental_score(ticker, profile)

                # Combined score (weighted average)
                profile_weights = self.trader_profiles[profile]
                combined_score = (
                    technical_score * (profile_weights['volatility_weight'] + profile_weights['momentum_weight'] + profile_weights['volume_weight']) +
                    fundamental_score * profile_weights['fundamental_weight']
                )

                # Get latest price info
                latest_price = df.iloc[-1]['Close']
                prev_price = df.iloc[-2]['Close'] if len(df) > 1 else latest_price
                price_change = (latest_price - prev_price) / prev_price * 100

                # Volume and price checks based on profile
                avg_volume = df['Volume'].tail(20).mean()
                profile_settings = self.trader_profiles[profile]

                # Price range check for beginner_growth profile
                if profile == 'beginner_growth':
                    if not (profile_settings['min_price'] <= latest_price <= profile_settings['max_price']):
                        continue

                if avg_volume < profile_settings['min_volume']:
                    continue  # Skip low volume stocks

                if avoid_retail and 'max_volume' in profile_settings:
                    if avg_volume > profile_settings['max_volume']:
                        continue  # Skip high volume stocks (retail heavy)

                recommendations.append({
                    'ticker': ticker,
                    'technical_score': round(technical_score, 1),
                    'fundamental_score': round(fundamental_score, 1),
                    'combined_score': round(combined_score, 1),
                    'latest_price': latest_price,
                    'price_change_pct': round(price_change, 2),
                    'avg_volume': int(avg_volume),
                    'data_points': len(df)
                })

                if len(recommendations) % 10 == 0:
                    print(f"✅ Analyzed {len(recommendations)} stocks...")

            except Exception as e:
                print(f"❌ Error analyzing {ticker}: {e}")
                continue

        # Sort by combined score and return top N
        recommendations_df = pd.DataFrame(recommendations)
        if not recommendations_df.empty:
            recommendations_df = recommendations_df.sort_values('combined_score', ascending=False).head(top_n)

        print(f"🎯 Found {len(recommendations_df)} recommendations for {profile} profile")
        return recommendations_df

    def get_profile_description(self, profile):
        """Get description of trader profile"""
        descriptions = {
            'conservative': {
                'name': 'Conservative Trader',
                'description': 'Low risk, stable stocks with strong fundamentals',
                'focus': 'Stability, dividends, blue-chip companies'
            },
            'moderate': {
                'name': 'Moderate Trader',
                'description': 'Balanced approach with moderate risk/reward',
                'focus': 'Growth potential with reasonable volatility'
            },
            'beginner_growth': {
                'name': 'Beginner Growth Trader',
                'description': 'High growth potential for beginners with small capital',
                'focus': 'Cheap stocks (50-2000 IDR) with oversold rebounds, avoid retail-heavy stocks'
            },
            'aggressive': {
                'name': 'Aggressive Trader',
                'description': 'High risk, high reward opportunities',
                'focus': 'High momentum, emerging opportunities'
            }
        }
        return descriptions.get(profile, descriptions['moderate'])

    def calculate_signal_strength(self, df, profile='moderate'):
        """
        Calculate signal strength for a stock (0-100 scale)
        
        Parameters:
        -----------
        df : DataFrame
            Price data with technical indicators
        profile : str
            Trader profile
            
        Returns:
        --------
        float: Signal strength score 0-100
        """
        try:
            if len(df) < 20:
                return 0
            
            latest = df.iloc[-1]
            
            signal_score = 50  # Base score
            
            # RSI signals
            if 'RSI' in df.columns:
                rsi = latest['RSI']
                if rsi < 20:
                    signal_score += 30  # Very oversold
                elif rsi < 30:
                    signal_score += 25  # Oversold
                elif rsi > 80:
                    signal_score -= 25  # Very overbought
                elif rsi > 70:
                    signal_score -= 15  # Overbought
                else:
                    signal_score += 0   # Neutral
            
            # MACD signals
            if 'MACD' in df.columns and 'MACD_Signal' in df.columns:
                macd = latest['MACD']
                signal_line = latest['MACD_Signal']
                if macd > signal_line:
                    signal_score += 15  # Bullish
                else:
                    signal_score -= 10  # Bearish
            
            # Volume signals
            if 'Volume_Ratio' in df.columns:
                vol_ratio = latest['Volume_Ratio']
                if vol_ratio > 1.5:
                    signal_score += 10  # High volume confirmation
                elif vol_ratio < 0.7:
                    signal_score -= 5   # Low volume concern
            
            # Moving Average alignment
            if 'MA5' in df.columns and 'MA20' in df.columns:
                ma5 = latest['MA5']
                ma20 = latest['MA20']
                if ma5 > ma20:
                    signal_score += 10  # Short MA above long MA (bullish)
                elif ma5 < ma20:
                    signal_score -= 10  # Short MA below long MA (bearish)
            
            # Price position relative to MAs
            if 'MA50' in df.columns:
                price = latest['Close']
                ma50 = latest['MA50']
                if price > ma50:
                    signal_score += 5   # Above 50-day MA
                else:
                    signal_score -= 5   # Below 50-day MA
            
            return max(0, min(100, signal_score))
            
        except Exception as e:
            print(f"Error calculating signal strength: {e}")
            return 50

    def predict_price_movements(self, df, forward_periods=[7, 14, 21, 30]):
        """
        Predict price movements for multiple timeframes
        
        Parameters:
        -----------
        df : DataFrame
            Price data
        forward_periods : list
            Periods to predict (in days): [1W=7, 2W=14, 3W=21, 1M=30]
            
        Returns:
        --------
        dict: Price predictions for each period with confidence
        """
        try:
            if len(df) < 50:
                return {'error': 'Insufficient data'}
            
            # Prepare data
            df_copy = df.copy()
            df_copy['Returns'] = df_copy['Close'].pct_change()
            df_copy['MA5'] = ta.trend.sma_indicator(df_copy['Close'], window=5)
            df_copy['MA20'] = ta.trend.sma_indicator(df_copy['Close'], window=20)
            df_copy['RSI'] = ta.momentum.rsi(df_copy['Close'], window=14)
            df_copy['Volume_Ratio'] = df_copy['Volume'] / df_copy['Volume'].rolling(20).mean()
            
            # Drop NaN
            df_copy = df_copy.dropna()
            
            if len(df_copy) < 30:
                return {'error': 'Insufficient clean data'}
            
            current_price = df_copy['Close'].iloc[-1]
            predictions = {}
            
            # Simple linear regression model for each timeframe
            for period in forward_periods:
                try:
                    # Prepare features
                    features = df_copy[['Close', 'MA5', 'MA20', 'RSI', 'Volume_Ratio']].tail(min(60, len(df_copy)))
                    
                    if len(features) < 20:
                        continue
                    
                    # Normalize features
                    scaler = StandardScaler()
                    features_scaled = scaler.fit_transform(features)
                    
                    # Create target (future price direction)
                    X = features_scaled[:-period] if len(features_scaled) > period else features_scaled
                    y = df_copy['Close'].tail(len(X) + period).shift(-period).dropna().values if len(df_copy) > period else []
                    
                    if len(X) > 0 and len(y) > 0 and len(X) == len(y):
                        # Train simple model
                        model = LinearRegression()
                        model.fit(X, y)
                        
                        # Predict
                        latest_scaled = features_scaled[-1:] if len(features_scaled) > 0 else features_scaled
                        predicted_price = model.predict(latest_scaled)[0] if len(latest_scaled) > 0 else current_price
                        
                        # Calculate expected return
                        expected_return = ((predicted_price - current_price) / current_price) * 100
                        
                        # Confidence score (R² equivalent, simplified)
                        confidence = min(100, max(0, 50 + expected_return * 0.5))
                        
                        period_name = {7: '1W', 14: '2W', 21: '3W', 30: '1M'}.get(period, f'{period}D')
                        
                        predictions[period_name] = {
                            'predicted_price': float(round(predicted_price, 0)),
                            'expected_return': float(round(expected_return, 2)),
                            'confidence': float(round(confidence, 1)),
                            'upside': expected_return > 0
                        }
                except Exception as e:
                    print(f"Error predicting {period}-day movement: {e}")
                    continue
            
            return predictions if predictions else {'error': 'Prediction failed'}
            
        except Exception as e:
            print(f"Error in predict_price_movements: {e}")
            return {'error': str(e)}

    def get_recommendations_with_signals(self, profile='moderate', top_n=10, avoid_retail=False):
        """
        Get stock recommendations with signal strength and price predictions
        
        Returns:
        --------
        pd.DataFrame: Recommendations with signal strength and predictions
        """
        # Get base recommendations
        recommendations_df = self.get_stock_recommendations(profile, top_n=top_n*2, avoid_retail=avoid_retail)
        
        if recommendations_df.empty:
            return recommendations_df
        
        # Add signal strength and predictions
        enhanced_recs = []
        for idx, row in recommendations_df.iterrows():
            try:
                ticker = row['ticker']
                
                # Get price data
                query = f'SELECT * FROM "{ticker}" ORDER BY Date DESC LIMIT 200'
                df = pd.read_sql(query, self.engine)
                
                if len(df) < 20:
                    continue
                
                df['Date'] = pd.to_datetime(df['Date'])
                df = df.sort_values('Date')
                
                # Calculate signal strength
                signal_strength = self.calculate_signal_strength(df, profile)
                
                # Predict prices
                predictions = self.predict_price_movements(df)
                
                # Add to recommendations
                rec_dict = row.to_dict()
                rec_dict['signal_strength'] = round(signal_strength, 1)
                
                # Add price predictions
                for period in ['1W', '2W', '3W', '1M']:
                    if period in predictions:
                        rec_dict[f'pred_{period}_price'] = predictions[period]['predicted_price']
                        rec_dict[f'pred_{period}_return'] = predictions[period]['expected_return']
                        rec_dict[f'pred_{period}_conf'] = predictions[period]['confidence']
                    else:
                        rec_dict[f'pred_{period}_price'] = 0
                        rec_dict[f'pred_{period}_return'] = 0
                        rec_dict[f'pred_{period}_conf'] = 0
                
                # Classify by profile
                rec_dict['profile_match'] = self._profile_match(signal_strength, profile)
                
                enhanced_recs.append(rec_dict)
            except Exception as e:
                print(f"Error enhancing recommendation for {row.get('ticker', 'Unknown')}: {e}")
                continue
        
        # Create dataframe and sort by signal strength
        enhanced_df = pd.DataFrame(enhanced_recs)
        if not enhanced_df.empty:
            enhanced_df = enhanced_df.sort_values('signal_strength', ascending=False).head(top_n)
        
        return enhanced_df

    def _profile_match(self, signal_strength, profile):
        """Classify recommendation match with profile"""
        if signal_strength >= 75:
            return 'Perfect'
        elif signal_strength >= 60:
            return 'Good'
        elif signal_strength >= 45:
            return 'Fair'
        else:
            return 'Check'
