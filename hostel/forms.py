from django import forms

from .models import Room


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['room_number', 'capacity']
        widgets = {
            'room_number': forms.TextInput(attrs={'class': 'form-control'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

    def clean_capacity(self):
        capacity = self.cleaned_data.get('capacity')
        if capacity is not None and capacity < 1:
            raise forms.ValidationError("Capacity must be at least 1.")

        if self.instance and self.instance.pk:
            current_occupancy = self.instance.occupancy
            if capacity is not None and capacity < current_occupancy:
                raise forms.ValidationError(
                    f"Capacity cannot be reduced below current occupancy ({current_occupancy} students assigned)."
                )

        return capacity
