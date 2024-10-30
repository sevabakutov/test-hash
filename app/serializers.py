from rest_framework import serializers
from .models import TelegramUser, TradePool, TradeInvestment

class TelegramUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramUser
        exclude = ['created_at', 'updated_at']


class TradePoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradePool
        exclude = ['created_at', 'updated_at']


class TradeInvestmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradeInvestment
        exclude = ['created_at', 'updated_at']