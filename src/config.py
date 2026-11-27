from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24

    # اندازه‌ی pool کانکشن (برای هر پروسه‌ی uvicorn):
    #  - min: کانکشن‌هایی که همیشه باز می‌مانند؛ ۱ یعنی در ترافیک کم کانکشن بیکار نگه نمی‌داریم
    #    و pool در صورت نیاز تا max بزرگ می‌شود.
    #  - max: سقف کار همزمان با دیتابیس در این پروسه (همین عدد اندازه‌ی semaphore کنترل ورود هم هست).
    #    باید workerها × max کمتر از max_connections دیتابیس (پیش‌فرض ۱۰۰) بماند.
    #  مقدارها محافظه‌کارانه‌اند و در تست بار تأیید شدند: PostgreSQL کمتر از ۱۲٪ CPU
    #  می‌گرفت و گلوگاه خود API بود، نه pool.
    # اندازه‌ی pool کانکشن‌ها. این‌ها مقدار شروع هستند و با تست بار باید تنظیم شوند:
    #   max: حدود (۲ × تعداد هسته‌ی CPU دیتابیس) + ۱ تا ۲؛ مجموع (تعداد worker × max)
    #        باید خیلی کمتر از max_connections پستگرس (پیش‌فرض ۱۰۰) بماند.
    #   min: کانکشن‌هایی که همیشه باز می‌مانند؛ کمتر یعنی منابع کمتر، ولی در لحظه‌ی افزایش
    #        ناگهانی بار، باز کردن کانکشن تازه چند ده میلی‌ثانیه به تأخیر اضافه می‌کند.
    # با DB_POOL_MIN_SIZE و DB_POOL_MAX_SIZE در .env قابل تغییرند.
    db_pool_min_size: int = 1
    db_pool_max_size: int = 10
    # حداکثر انتظار یک درخواست برای گرفتن کانکشن (ثانیه)؛ بعدش 503
    db_acquire_timeout: float = 10.0


settings = Settings()
