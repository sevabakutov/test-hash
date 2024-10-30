import uuid
from django.db import models

class TelegramUser(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, unique=True, editable=False)
    username = models.CharField(max_length=150, null=True, unique=True)
    pnl = models.IntegerField(default=0)
    img = models.CharField(max_length=300, null=True)
    created_at = models.DateTimeField(verbose_name='created at', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='updated at', auto_now=True)

    def __str__(self) -> str:
        return f"{self.username} with {self.pnl} pnl, created at {self.created_at}. Last update was {self.updated_at}"

    class Meta:
        verbose_name = "telegram user"
        verbose_name_plural = "telegram users"
        db_table = "test_telegram_user"
        get_latest_by = "updated_at"


class TradePool(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, unique=True, editable=False)
    user_id = models.UUIDField(unique=True, editable=False)
    active = models.CharField(max_length=10)
    is_long = models.BooleanField(verbose_name='is long')
    is_order = models.BooleanField(verbose_name='is order')
    order = models.DecimalField(max_digits=20, decimal_places=10, null=True)
    final_amount = models.DecimalField(verbose_name='final amount', max_digits=10, decimal_places=2)
    stop_loss = models.SmallIntegerField(verbose_name='stop loss')
    take_profit = models.PositiveIntegerField(verbose_name='take profit')
    leverage = models.DecimalField(max_digits=5, decimal_places=2)
    curr_value = models.DecimalField(verbose_name='curr value', max_digits=10, decimal_places=2, default=0)
    in_amount = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(verbose_name='created at', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='updated at', auto_now=True)

    def __str__(self) -> str:
        return f"trade pool, creator id: {self.user_id}, final amount: {self.final_amount}, current value: {self.curr_value}"

    class Meta:
        verbose_name = "trade pool"
        verbose_name_plural = "trade pools"
        db_table = "test_trade_pool"
        get_latest_by = "updated_at"


class TradeInvestment(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, unique=True, editable=False)
    user_id = models.UUIDField(editable=False)
    pool_id = models.UUIDField(editable=False)
    input = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(verbose_name='created at', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='updated at', auto_now=True)

    def __str__(self) -> str:
        return f"user id: {self.user_id}, pool id: {self.pool_id}, amount: {self.input}, last update: {self.updated_at}"

    class Meta:
        verbose_name = "trade investment"
        verbose_name_plural = "trade investments"
        db_table = "test_trade_investment"
        get_latest_by = "updated_at"
