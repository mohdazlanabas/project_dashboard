from django.db import models

class Lorry(models.Model):
    lorry_id = models.CharField(max_length=100, db_column='LORRY_ID', primary_key=True)
    types_id = models.CharField(max_length=100, db_column='TYPES_ID')
    client_id = models.CharField(max_length=100, db_column='CLIENT_ID')
    make_id = models.CharField(max_length=100, db_column='MAKE_ID')

    def __str__(self):
        return self.lorry_id

    class Meta:
        db_table = 'lorries'

class Transaction(models.Model):
    transaction_id = models.CharField(max_length=100, db_column='Transaction_ID')
    lorry_id = models.CharField(max_length=100, db_column='LORRY_ID')
    weight = models.FloatField(db_column='WEIGHT')
    delivery_time = models.CharField(max_length=64, db_column='DELIVERY_TIME')

    def __str__(self):
        return f"Transaction {self.transaction_id} - {self.lorry_id} on {self.delivery_time}"

    class Meta:
        db_table = 'deliveries'  # Use the existing collection name
        ordering = ['-delivery_time']
