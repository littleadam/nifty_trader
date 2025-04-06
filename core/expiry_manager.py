from datetime import datetime, timedelta

class ExpiryManager:
    def __init__(self):
        self.holidays = self._load_holidays()

    def _load_holidays(self):
        """Fetch exchange holidays from Zerodha API"""
        try:
            return self.kite.holidays()['NFO']  # Requires Kite Connect 3+
        except:
            # Fallback to static holidays if API fails
            return ['2025-10-02', '2023-11-14']  # Example dates

    def get_monthly_expiry(self, date):
        """Get monthly expiry with holiday adjustment"""
        first_day = date.replace(day=1)
        days_needed = (3 * 7) - 1
        third_thursday = first_day + timedelta(days=days_needed - first_day.weekday())
        
        if third_thursday.month != date.month:
            third_thursday -= timedelta(weeks=1)
        
        # Adjust for holidays
        while third_thursday.strftime('%Y-%m-%d') in self.holidays:
            third_thursday -= timedelta(days=1)
        
        return third_thursday

    def get_next_weekly_expiry(self):
        """Get next weekly expiry (Thursday) with holiday check"""
        today = datetime.now()
        days_ahead = (3 - today.weekday()) % 7  # Days until next Thursday
        expiry = today + timedelta(days=days_ahead)
        
        # Adjust for holidays
        while expiry.strftime('%Y-%m-%d') in self.holidays:
            expiry -= timedelta(days=1)
        
        return expiry

    def is_expiry_day(self, date=None):
        """Check if given date is an expiry day"""
        date = date or datetime.now()
        monthly_expiry = self.get_monthly_expiry(date)
        weekly_expiry = self.get_next_weekly_expiry()
        return date.date() in [monthly_expiry.date(), weekly_expiry.date()]
