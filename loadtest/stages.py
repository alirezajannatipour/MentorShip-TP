"""بار را پله‌پله زیاد می‌کند تا نقطه‌ای که سرویس کند می‌شود پیدا شود.

همراه locustfile.py اجرا می‌شود:  -f loadtest/locustfile.py,loadtest/stages.py
"""

from locust import LoadTestShape


class StepLoad(LoadTestShape):
    # (ثانیه‌ی پایان مرحله، تعداد کاربر همزمان، نرخ اضافه شدن کاربر در ثانیه)
    stages = [
        (60, 10, 10),
        (120, 25, 10),
        (180, 50, 10),
        (240, 100, 20),
        (300, 150, 20),
    ]

    def tick(self):
        run_time = self.get_run_time()
        for end, users, spawn_rate in self.stages:
            if run_time < end:
                return users, spawn_rate
        return None
