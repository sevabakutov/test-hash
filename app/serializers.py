from rest_framework import serializers
from .models import TelegramUser, TradeIdea, TradeInvestment

class TelegramUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramUser
        fields = "__all__"


class TradingPoolSerializer(serializers.ModelSerializer):
    username = serializers.SlugRelatedField(source='user', slug_field='username', read_only=True)

    class Meta:
        model = TradeIdea
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        return {self.snake_to_camel_case(key): value for key, value in representation.items()}

    def snake_to_camel_case(self, value):
        components = value.split('_')
        return components[0] + ''.join(x.title() for x in components[1:])


class TradeInvestmentSerializer(serializers.ModelSerializer):
    username = serializers.SlugRelatedField(source='user', slug_field='username', read_only=True)

    class Meta:
        model = TradeInvestment
        fields = "__all__"

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        return {self.snake_to_camel_case(key): value for key, value in representation.items()}

    def snake_to_camel_case(self, value):
        components = value.split('_')
        return components[0] + ''.join(x.title() for x in components[1:])
