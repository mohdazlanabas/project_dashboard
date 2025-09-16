from rest_framework import serializers
from .models import Lorry, Transaction

class LorrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Lorry
        fields = '__all__'

class TransactionSerializer(serializers.ModelSerializer):
    # Computed lorry type via lookup (no FK relation on model)
    lorry_types_id = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = (
            'transaction_id',
            'lorry_id',
            'weight',
            'delivery_time',
            'lorry_types_id',
        )

    def get_lorry_types_id(self, obj):
        try:
            l = Lorry.objects.get(lorry_id=obj.lorry_id)
            return l.types_id
        except Lorry.DoesNotExist:
            return None
