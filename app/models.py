from django.contrib.auth.base_user import AbstractBaseUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Active(models.Model):
    name = models.CharField(max_length=255, null=False, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'app'


class TelegramUser(AbstractBaseUser):
    username = models.CharField(max_length=150, blank=False, null=False, unique=True)
    telegram_wallet = models.CharField(max_length=1000, null=True, unique=True)
    pnl = models.IntegerField(null=True)

    img = models.ImageField(null=True)

    USERNAME_FIELD = "username"

    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username

    class Meta:
        app_label = 'app'


class TradeIdea(models.Model):
    user = models.ForeignKey(TelegramUser, related_name="created_trade_ideas", on_delete=models.CASCADE)

    active_id = models.ForeignKey(Active, related_name="trade_active_ideas", on_delete=models.CASCADE)

    isLong = models.BooleanField(null=False)
    isOrder = models.BooleanField(null=False, default=False)

    order = models.DecimalField(max_digits=20, decimal_places=10, validators=[MinValueValidator(0)], null=True, default=None)
    final_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    stop_loss = models.SmallIntegerField(
        validators=[MinValueValidator(-100), MaxValueValidator(0)],
        null=True
    )
    take_profit = models.PositiveIntegerField(
        validators=[MinValueValidator(25), MaxValueValidator(300)]
    )
    leverage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(1), MaxValueValidator(50)]
    )
    curr_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=False
    )

    in_amount = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        null=False
    )

    created_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "app"


class TradeInvestment(models.Model):
    user = models.ForeignKey(TelegramUser, related_name='user_tradeinvestments', on_delete=models.CASCADE)
    trade_idea = models.ForeignKey(TradeIdea, related_name='trade_investments', on_delete=models.CASCADE)

    amount_invested = models.DecimalField(max_digits=10, decimal_places=2)
    invested_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'app'
