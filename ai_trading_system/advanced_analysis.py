"""
Advanced Technical Analysis Module
Menyediakan analisis komprehensif dengan semua indikator yang diminta
"""

import pandas as pd
import numpy as np
import ta
from datetime import datetime, timedelta

class AdvancedAnalyzer:
    """
    Analisis teknikal lanjutan dengan semua indikator:
    - Moving Averages (5, 10, 20, 50)
    - RSI + Fibonacci Levels
    - Volume
    - Momentum Indicators
    - SuperTrend
    - Trading Strategy Signals
    """
    
    def __init__(self):
        pass
    
    def calculate_all_indicators(self, df):
        """
        Calculate semua indikator teknikal
        
        Parameters:
        -----------
        df : DataFrame
            Data OHLCV dengan kolom: Open, High, Low, Close, Volume
            
        Returns:
        --------
        df : DataFrame
            DataFrame dengan semua indikator
        """
        df = df.copy()
        
        # 1. MOVING AVERAGES
        if len(df) >= 5:
            df['MA5'] = ta.trend.sma_indicator(df['Close'], window=5)
        if len(df) >= 10:
            df['MA10'] = ta.trend.sma_indicator(df['Close'], window=10)
        if len(df) >= 20:
            df['MA20'] = ta.trend.sma_indicator(df['Close'], window=20)
        if len(df) >= 50:
            df['MA50'] = ta.trend.sma_indicator(df['Close'], window=50)
        
        # 2. RSI (14 period)
        if len(df) >= 14:
            df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
        
        # 3. RSI FIBONACCI LEVELS (21.6%, 38.2%, 50%, 61.8%, 78.4% dari RSI range 0-100)
        if 'RSI' in df.columns:
            df['RSI_Fib_21.6'] = 21.6  # Support 1
            df['RSI_Fib_38.2'] = 38.2  # Support 2
            df['RSI_Fib_50'] = 50.0    # Middle
            df['RSI_Fib_61.8'] = 61.8  # Resistance 1
            df['RSI_Fib_78.4'] = 78.4  # Resistance 2
        
        # 4. VOLUME INDICATORS
        if 'Volume' in df.columns:
            df['Volume_SMA20'] = df['Volume'].rolling(window=20).mean()
            df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA20']
        
        # 5. MOMENTUM INDICATORS
        # MACD
        if len(df) >= 26:
            df['MACD'] = ta.trend.macd(df['Close'])
            df['MACD_Signal'] = ta.trend.macd_signal(df['Close'])
            df['MACD_Diff'] = df['MACD'] - df['MACD_Signal']
        
        # Momentum (ROC - Rate of Change)
        if len(df) >= 12:
            df['Momentum_ROC'] = (df['Close'] - df['Close'].shift(12)) / df['Close'].shift(12) * 100
        
        # 6. SUPERTREND
        df = self._calculate_supertrend(df, period=10, multiplier=3.0)
        
        # 7. BOLLINGER BANDS (20 period)
        if len(df) >= 20:
            df['BB_Middle'] = df['Close'].rolling(window=20).mean()
            bb_std = df['Close'].rolling(window=20).std()
            df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
            df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        
        # 8. FIBONACCI RETRACEMENT LEVELS (Price)
        df = self._calculate_fib_levels(df)
        
        return df
    
    def _calculate_supertrend(self, df, period=10, multiplier=3.0):
        """Calculate SuperTrend indicator"""
        hl_avg = (df['High'] + df['Low']) / 2
        hl_atr = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'], window=period)
        
        df['ST_Basic_Upper'] = hl_avg + multiplier * hl_atr
        df['ST_Basic_Lower'] = hl_avg - multiplier * hl_atr
        
        # Final SuperTrend values
        ST = pd.Series(index=df.index, dtype='float64')
        ST_Trend = pd.Series(index=df.index, dtype='int64')
        
        for i in range(len(df)):
            if i == 0:
                ST.iloc[i] = df['ST_Basic_Upper'].iloc[i]
                ST_Trend.iloc[i] = -1  # Downtrend
            else:
                # Upper line
                if df['ST_Basic_Upper'].iloc[i] < ST.iloc[i-1] or df['Close'].iloc[i-1] > ST.iloc[i-1]:
                    ST_Upper = df['ST_Basic_Upper'].iloc[i]
                else:
                    ST_Upper = ST.iloc[i-1]
                
                # Lower line
                if df['ST_Basic_Lower'].iloc[i] > ST.iloc[i-1] or df['Close'].iloc[i-1] < ST.iloc[i-1]:
                    ST_Lower = df['ST_Basic_Lower'].iloc[i]
                else:
                    ST_Lower = ST.iloc[i-1]
                
                # Determine trend
                if ST_Trend.iloc[i-1] == 1:
                    trend = 1 if df['Close'].iloc[i] >= ST_Lower else -1
                else:
                    trend = -1 if df['Close'].iloc[i] <= ST_Upper else 1
                
                ST.iloc[i] = ST_Upper if trend == -1 else ST_Lower
                ST_Trend.iloc[i] = trend
        
        df['SuperTrend'] = ST
        df['SuperTrend_Trend'] = ST_Trend  # 1 = Uptrend, -1 = Downtrend
        
        return df
    
    def _calculate_fib_levels(self, df, lookback=252):
        """
        Calculate Fibonacci Retracement Levels
        """
        if len(df) < lookback:
            lookback = len(df)
        
        recent = df.tail(lookback)
        high = recent['High'].max()
        low = recent['Low'].min()
        
        diff = high - low
        
        if diff > 0:
            df['Fib_0%'] = high
            df['Fib_23.6%'] = high - (diff * 0.236)
            df['Fib_38.2%'] = high - (diff * 0.382)
            df['Fib_50%'] = high - (diff * 0.5)
            df['Fib_61.8%'] = high - (diff * 0.618)
            df['Fib_78.6%'] = high - (diff * 0.786)
            df['Fib_100%'] = low
        
        return df
    
    def generate_trading_strategy(self, df, ticker, profile='moderate'):
        """
        Generate trading strategy recommendations
        
        Returns:
        --------
        dict : Strategy recommendations
        """
        if len(df) < 50:
            return None
        
        latest = df.iloc[-1]
        
        # Trend identification
        trend = self._identify_trend(df)
        
        # Support & Resistance
        support, resistance = self._calculate_support_resistance(df)
        
        # Entry signals
        entry_signals = self._calculate_entry_signals(df, profile)
        
        # Price targets and stops
        strategy = {
            'ticker': ticker,
            'timestamp': datetime.now(),
            'current_price': float(latest['Close']),
            'trend': trend,
            'support_level': support,
            'resistance_level': resistance,
            'entry_signals': entry_signals,
            'strategy': self._build_strategy(latest, support, resistance, trend, profile),
            'risk_reward_ratio': None,
            'confidence_level': self._calculate_confidence(df, latest, profile)
        }
        
        return strategy
    
    def _identify_trend(self, df):
        """Identify current trend"""
        if len(df) < 50:
            return 'UNKNOWN'
        
        latest = df.iloc[-1]
        
        # Check SuperTrend
        if 'SuperTrend_Trend' in df.columns:
            if latest['SuperTrend_Trend'] == 1:
                return 'UPTREND'
            else:
                return 'DOWNTREND'
        
        # Fallback: Check MAs
        if 'MA20' in latest and 'MA50' in latest:
            if latest['MA20'] > latest['MA50']:
                return 'UPTREND'
            else:
                return 'DOWNTREND'
        
        return 'NEUTRAL'
    
    def _calculate_support_resistance(self, df, lookback=20):
        """Calculate support and resistance from recent data"""
        recent = df.tail(lookback)
        
        support = recent['Low'].min()
        resistance = recent['High'].max()
        
        return support, resistance
    
    def _calculate_entry_signals(self, df, profile):
        """Calculate entry signals"""
        latest = df.iloc[-1]
        signals = {
            'ma_signal': None,
            'rsi_signal': None,
            'macd_signal': None,
            'supertrend_signal': None,
            'volume_signal': None,
            'overall': None
        }
        
        # MA Signal
        if 'MA5' in latest and 'MA20' in latest:
            if latest['MA5'] > latest['MA20']:
                signals['ma_signal'] = 'BUY'
            else:
                signals['ma_signal'] = 'SELL'
        
        # RSI Signal
        if 'RSI' in latest:
            if latest['RSI'] < 30:
                signals['rsi_signal'] = 'OVERSOLD (BUY)'
            elif latest['RSI'] > 70:
                signals['rsi_signal'] = 'OVERBOUGHT (SELL)'
            else:
                signals['rsi_signal'] = 'NEUTRAL'
        
        # MACD Signal
        if 'MACD_Diff' in latest:
            if latest['MACD_Diff'] > 0:
                signals['macd_signal'] = 'BULLISH'
            else:
                signals['macd_signal'] = 'BEARISH'
        
        # SuperTrend Signal
        if 'SuperTrend_Trend' in latest:
            signals['supertrend_signal'] = 'UPTREND' if latest['SuperTrend_Trend'] == 1 else 'DOWNTREND'
        
        # Volume Signal
        if 'Volume_Ratio' in latest:
            if latest['Volume_Ratio'] > 1.2:
                signals['volume_signal'] = 'HIGH VOLUME (STRONG)'
            elif latest['Volume_Ratio'] < 0.8:
                signals['volume_signal'] = 'LOW VOLUME (WEAK)'
            else:
                signals['volume_signal'] = 'NORMAL'
        
        return signals
    
    def _build_strategy(self, latest, support, resistance, trend, profile):
        """Build trading strategy with entry, TP, SL, accumulation zones"""
        current_price = float(latest['Close'])
        
        strategy = {
            'action': None,
            'entry_zone_min': None,
            'entry_zone_max': None,
            'take_profit_1': None,
            'take_profit_2': None,
            'take_profit_3': None,
            'cut_loss': None,
            'accumulation_zone': None,
            'risk_reward': None,
            'rationale': ''
        }
        
        if trend == 'UPTREND':
            strategy['action'] = 'BUY'
            
            # Entry zone: Pullback ke MA20 atau support
            entry_min = min(float(latest.get('MA20', support)), support)
            entry_max = current_price
            
            strategy['entry_zone_min'] = entry_min
            strategy['entry_zone_max'] = entry_max
            
            # Take Profit levels (1:1, 1:2, 1:3 risk/reward)
            risk = current_price - entry_min
            strategy['take_profit_1'] = current_price + risk
            strategy['take_profit_2'] = current_price + (risk * 2)
            strategy['take_profit_3'] = current_price + (risk * 3)
            
            # Cut Loss
            strategy['cut_loss'] = entry_min - (risk * 0.5)
            
            # Accumulation zone if price touches support
            strategy['accumulation_zone'] = {
                'trigger': support,
                'action': 'BUY MORE (DCA)',
                'suggested_quantity': '50% of intended position'
            }
            
            strategy['rationale'] = f"Uptrend confirmed. Entry on pullback to {entry_min:.0f}. Target resistance at {resistance:.0f}"
            
        elif trend == 'DOWNTREND':
            strategy['action'] = 'SELL / WAIT'
            
            # Entry zone for short: resistance
            entry_min = current_price
            entry_max = resistance
            
            strategy['entry_zone_min'] = entry_min
            strategy['entry_zone_max'] = entry_max
            
            # Take Profit
            risk = entry_max - current_price
            strategy['take_profit_1'] = current_price - risk
            strategy['take_profit_2'] = current_price - (risk * 2)
            strategy['take_profit_3'] = current_price - (risk * 3)
            
            # Cut Loss
            strategy['cut_loss'] = entry_max + (risk * 0.5)
            
            # Warning zone
            strategy['accumulation_zone'] = {
                'trigger': resistance,
                'action': 'AVOID or SHORT',
                'suggested_quantity': 'Only if confirmed bounce rejection'
            }
            
            strategy['rationale'] = f"Downtrend identified. Avoid long positions. Watch for bounce at support {support:.0f}"
        
        else:
            strategy['action'] = 'WAIT'
            strategy['rationale'] = "No clear trend. Wait for breakout confirmation."
        
        return strategy
    
    def _calculate_confidence(self, df, latest, profile):
        """
        Calculate confidence level of the strategy
        0-100 scale
        """
        confidence = 50  # Start from neutral
        
        # Check indicator alignment
        signals_positive = 0
        signals_total = 0
        
        # MA signal
        if 'MA5' in latest and 'MA20' in latest:
            signals_total += 1
            if latest['MA5'] > latest['MA20']:
                signals_positive += 1
        
        # RSI signal
        if 'RSI' in latest:
            signals_total += 1
            if 30 < latest['RSI'] < 70:
                signals_positive += 1
        
        # MACD signal
        if 'MACD_Diff' in latest:
            signals_total += 1
            if latest['MACD_Diff'] > 0:
                signals_positive += 1
        
        # Volume signal
        if 'Volume_Ratio' in latest:
            signals_total += 1
            if latest['Volume_Ratio'] > 1.0:
                signals_positive += 1
        
        # Calculate alignment score
        if signals_total > 0:
            alignment = (signals_positive / signals_total) * 100
            confidence = min(90, max(10, alignment))
        
        return confidence


class IndicatorExplainer:
    """
    Memberikan penjelasan detail untuk setiap indikator
    """
    
    explanations = {
        'MA5': {
            'name': 'Moving Average 5 hari',
            'description': 'Rata-rata harga penutupan 5 hari terakhir. Menunjukkan trend jangka pendek.',
            'interpretation': {
                'bullish': 'MA5 > MA10 > MA20 > MA50 = Tren naik kuat',
                'bearish': 'MA5 < MA10 < MA20 < MA50 = Tren turun kuat',
            },
            'usage': 'Untuk entry/exit signal jangka pendek. Saat MA5 memotong MA20 dari bawah = sinyal BUY'
        },
        'MA10': {
            'name': 'Moving Average 10 hari',
            'description': 'Rata-rata harga 10 hari, trend pendek-menengah',
            'interpretation': {
                'support': 'Saat harga pullback ke MA10, sering menjadi support point',
                'resistance': 'Saat harga di atas MA10, menjadi resistance saat pullback',
            },
            'usage': 'Konfirmasi trend dan identifikasi breakout levels'
        },
        'MA20': {
            'name': 'Moving Average 20 hari',
            'description': 'Rata-rata 20 hari, trend menengah (1 bulan trading)',
            'interpretation': {
                'key_level': 'MA20 adalah level penting untuk support/resistance',
                'trend': 'Jika Close > MA20 = Bullish, Close < MA20 = Bearish',
            },
            'usage': 'Identifikasi pullback opportunities. Entry dekat MA20 saat tren naik.'
        },
        'MA50': {
            'name': 'Moving Average 50 hari',
            'description': 'Rata-rata 50 hari (~2-3 bulan trading), trend jangka panjang',
            'interpretation': {
                'major_trend': 'MA50 menunjukkan tren major. Close > MA50 = Up, Close < MA50 = Down',
                'filter': 'Gunakan MA50 sebagai filter trend direction',
            },
            'usage': 'Gunakan sebagai major trend filter. Jangan shorting saat harga > MA50.'
        },
        'RSI': {
            'name': 'Relative Strength Index',
            'description': 'Momentum oscillator yang mengukur kecepatan dan perubahan harga (0-100)',
            'interpretation': {
                'oversold': 'RSI < 30 = Oversold, kemungkinan bounce/reversal',
                'neutral': '40-60 = Neutral, bisa naik atau turun',
                'overbought': 'RSI > 70 = Overbought, kemungkinan pullback',
            },
            'trading_rules': [
                'RSI < 30 AND Price > MA20 = HIGH probability BUY',
                'RSI > 70 AND Price below resistance = Consider TAKE PROFIT',
                'Divergence: Harga naik tapi RSI turun = Warning signal (sell pressure)',
            ],
            'usage': 'Entry confirmation saat oversold, exit confirmation saat overbought'
        },
        'RSI_Fibonacci': {
            'name': 'RSI Fibonacci Levels',
            'description': 'Fibonacci ratios (21.6%, 38.2%, 50%, 61.8%, 78.4%) diterapkan pada RSI untuk multi-level entries/exits',
            'interpretation': {
                '21.6': 'Double bottoms level, sangat oversold',
                '38.2': 'First support level, moderate oversold',
                '50': 'Middle neutral level',
                '61.8': 'First resistance level, moderate overbought',
                '78.4': 'Double tops level, sangat overbought',
            },
            'usage': 'Enter saat RSI menembus 38.2 (oversold dengan konfirmasi). Exit saat RSI mencapai 61.8.'
        },
        'Volume': {
            'name': 'Volume Trading',
            'description': 'Jumlah lembar saham yang diperdagangkan. Mengkonfirmasi strength dari price movement.',
            'interpretation': {
                'high_volume_up': 'Harga naik dengan volume tinggi = Bullish, gerakan valid',
                'high_volume_down': 'Harga turun dengan volume tinggi = Bearish, down move is strong',
                'low_volume_up': 'Harga naik tapi volume rendah = Weak, berisiko pullback',
                'volume_increase': 'Volume sudden jump = Breakout atau reversal happening',
            },
            'rules': [
                'ENTRY: Konfirmasi dengan volume > avg volume',
                'BREAKOUT: Harus dengan volume spread (volume cluster)',
                'ACCUMULATION: Volume rendah dengan sideways price = akumulasi pembeli',
            ],
            'usage': 'Konfirmasi strength dari price movement dan breakout'
        },
        'Momentum': {
            'name': 'Momentum Indicators (MACD, ROC)',
            'description': 'Mengukur kecepatan dan strength dari price movement',
            'macd': {
                'description': 'MACD = 12-EMA minus 26-EMA. Signal line = 9-EMA dari MACD',
                'bullish': 'MACD > Signal line dan keduanya > 0 = Strong uptrend',
                'bearish': 'MACD < Signal line dan keduanya < 0 = Strong downtrend',
                'divergence': 'Harga naik tapi MACD turun = Weakening momentum (sell signal)',
            },
            'usage': 'Konfirmasi trend strength dan identifikasi momentum weakness'
        },
        'SuperTrend': {
            'name': 'SuperTrend Indicator',
            'description': 'Adaptive support & resistance berdasarkan ATR. Trend-following indicator yang sangat responsive.',
            'interpretation': {
                'uptrend': 'Price > SuperTrend line dengan color GREEN = Strong uptrend',
                'downtrend': 'Price < SuperTrend line dengan color RED = Strong downtrend',
                'reversal': 'Saat price menembus SuperTrend line = Reversal terjadi',
            },
            'trading': {
                'entry': 'Entry saat price bounce dari SuperTrend line dalam tren yang sama',
                'exit': 'Exit/CutLoss saat price breakout dari SuperTrend line',
                'accumulation': 'Jika price menyentuh SuperTrend tapi tidak tembus = akumulasi lanjut',
            },
            'usage': 'Best for trend-following. Very reliable untuk exit signal.'
        },
    }
    
    @staticmethod
    def get_explanation(indicator):
        """Get detailed explanation for an indicator"""
        return IndicatorExplainer.explanations.get(
            indicator,
            {'name': indicator, 'description': 'No explanation available'}
        )
    
    @staticmethod
    def get_all_explanations():
        """Get all indicator explanations"""
        return IndicatorExplainer.explanations
