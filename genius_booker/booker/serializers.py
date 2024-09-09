from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, get_user_model
from .models import UserProfile,Store, Staff,Appointment
from django.core.exceptions import ValidationError

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    store_name = serializers.CharField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'store_name']

    def validate(self, data):
        # Check if the username already exists
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError({"username": "A user with that username already exists."})
        
        # Check if the email already exists
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({"email": "A user with that email already exists."})
        
        return data

    def create(self, validated_data):
        store_name = validated_data.pop('store_name')
        
        # Create the user
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )

        # Create or update the UserProfile
        user_profile, _ = UserProfile.objects.update_or_create(
            user=user,
            defaults={'store_name': store_name}
        )

        return user

    
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(email=data['email'], password=data['password'])
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Invalid email or password")





class StaffSerializer(serializers.ModelSerializer):
    stores = serializers.ListField(child=serializers.CharField(), write_only=True)

    class Meta:
        model = Staff
        exclude = ['password']  # Exclude password from the serialization

    def validate_stores(self, stores):
        store_ids = []
        for store in stores:
            if isinstance(store, int):
                if Store.objects.filter(id=store).exists():
                    store_ids.append(store)
                else:
                    raise serializers.ValidationError(f"Store with ID '{store}' does not exist.")
            elif isinstance(store, str):
                if store.isdigit():
                    store_id = int(store)
                    if Store.objects.filter(id=store_id).exists():
                        store_ids.append(store_id)
                    else:
                        raise serializers.ValidationError(f"Store with ID '{store}' does not exist.")
                else:
                    try:
                        store_obj = Store.objects.get(name=store)
                        store_ids.append(store_obj.id)
                    except Store.DoesNotExist:
                        raise serializers.ValidationError(f"Store with name '{store}' does not exist.")
            else:
                raise serializers.ValidationError(f"Invalid store identifier: {store}")
        return store_ids

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        store_ids = validated_data.pop('stores', [])
        
        staff_member = super().create(validated_data)
        
        if password:
            staff_member.set_password(password)
            staff_member.save()
        
        # Assign the validated stores to the staff member
        staff_member.stores.set(store_ids)
        
        return staff_member



class StoreSerializer(serializers.ModelSerializer):
    staff = StaffSerializer(many=True, read_only=True)
    class Meta:
        model = Store
        fields = '__all__'

    def validate_name(self, value):
        """
        Check that the store name is unique.
        """
        if Store.objects.filter(name=value).exists():
            raise serializers.ValidationError("A store with this name already exists.")
        return value


class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = '__all__'

    def validate(self, data):
        therapist = data['therapist']
        store = data['store']
        start_time = data['start_time']
        end_time = data['end_time']
        date = data['date']

        # Ensure the selected therapist belongs to the selected store
        if not therapist.stores.filter(id=store.id).exists():
            raise serializers.ValidationError("The selected therapist does not belong to this store.")
        
        # Ensure that the end time is after the start time
        if start_time >= end_time:
            raise serializers.ValidationError("End time must be after the start time.")

        # Check for time conflicts with existing appointments
        existing_appointments = Appointment.objects.filter(
            therapist=therapist,
            store=store,
            date=date,
            start_time__lt=end_time,
            end_time__gt=start_time
        )

        if existing_appointments.exists():
            raise serializers.ValidationError("The selected therapist is already booked for this time slot.")
        
        return data
    
    