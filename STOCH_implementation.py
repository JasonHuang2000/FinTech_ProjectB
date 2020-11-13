
class Strategy():
    # option setting needed
    def __setitem__(self, key, value):
        self.options[key] = value

    # option setting needed
    def __getitem__(self, key):
        return self.options.get(key, '')

    def __init__(self):
        # strategy property
        self.subscribedBooks = {
            'Binance': {
                'pairs': ['ETH-USDT'],
            },
        }
        self.period = 5 * 60
        self.options = {}

        # user defined class attribute
        self.last_type = 'sell'
        self.last_cross_status = None
        self.close_price_trace = np.array([])
        self.high_price_trace = np.array([])
        self.low_price_trace = np.array([])
        self.ma_long = 10
        self.ma_short = 5
        self.UP = 1
        self.DOWN = 2

        self.K_80 = 3
        self.K_20 = 4
        self.K_UPCROSS = 5
        self.K_DOWNCROSS = 6

    def get_current_ma_cross(self):
        s_ma = talib.SMA(self.close_price_trace, self.ma_short)[-1]
        l_ma = talib.SMA(self.close_price_trace, self.ma_long)[-1]
        if np.isnan(s_ma) or np.isnan(l_ma):
            return None
        if s_ma > l_ma:
            return self.UP
        return self.DOWN

    def get_current_kd(self):
        # compute k, d value
        slowk, slowd = talib.STOCH(self.high_price_trace, self.low_price_trace, self.close_price_trace)
        
        if slowk.size < 2 or slowd.size < 2:
            return None

        k_flag = None   # 80-20
        cross_flag = None   # kd up-cross/down-cross

        if slowk[-1] >= 80:
            k_flag = self.K_80
        elif slowk[-1] <= 20:
            k_flag = self.K_20
        if slowk[-2] <= slowd[-2] and slowk[-1] >= slowd[-1]:
            cross_flag = self.K_UPCROSS
        elif slowk[-2] >= slowd[-2] and slowk[-1] <= slowd[-1]:
            cross_flag = self.K_DOWNCROSS
        
        Log('k_flag/cross_flag: '+str(k_flag)+str(cross_flag))
        return (k_flag, cross_flag)

    # called every self.period
    def trade(self, information):

        exchange = list(information['candles'])[0]
        pair = list(information['candles'][exchange])[0]
        
        high = information['candles'][exchange][pair][0]['high']
        low = information['candles'][exchange][pair][0]['low']
        close = information['candles'][exchange][pair][0]['close']
        
        # add latest price into trace
        self.high_price_trace = np.append(self.high_price_trace, [float(high)])
        self.low_price_trace = np.append(self.low_price_trace, [float(low)])
        self.close_price_trace = np.append(self.close_price_trace, [float(close)])
        # only keep max length of ma_long count elements
        self.high_price_trace = self.high_price_trace[-1000:]
        self.low_price_trace = self.low_price_trace[-1000:]
        self.close_price_trace = self.close_price_trace[-1000:]

        k_flag, cross_flag = self.get_current_kd()

        if cross_flag == None or k_flag == None:
            Log('cross_flag None')
            return []
        
        if self.last_type == 'sell' and cross_flag == self.K_UPCROSS and k_flag == self.K_80:
            Log('buying, opt1:' + self['opt1'])
            self.last_type = 'buy'
            return [
                {
                    'exchange': exchange,
                    'amount': 10,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        elif self.last_type == 'buy' and cross_flag == self.K_DOWNCROSS and k_flag == self.K_20:
            Log('selling, ' + exchange + ':' + pair)
            self.last_type = 'sell'
            return [
                {
                    'exchange': exchange,
                    'amount': -10,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]

        Log('failed')
        return []
