from django.db import models
from django.contrib.auth.models import User
from encrypted_model_fields.fields import EncryptedCharField, EncryptedTextField, EncryptedDateField

class Transaction(models.Model):
    TYPE_CHOICES = [
        ('expense', 'Expense'),
        ('income', 'Income'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = EncryptedDateField()
    category = EncryptedCharField(max_length=100)
    description = EncryptedTextField(max_length=250)
    amount = EncryptedCharField(max_length=20)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_amount(self):
        return float(self.amount)
    
    def set_amount(self, value):
        self.amount = str(value)

    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['date']),
            models.Index(fields=['type']),
            models.Index(fields=['user', 'date']),
            models.Index(fields=['user', 'type']),
            models.Index(fields=['date', 'type']),
        ]

        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.get_type_display()} - {self.category} - {self.amount}"