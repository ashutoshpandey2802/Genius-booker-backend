from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import LoginSerializer, RegisterSerializer,StoreSerializer, StaffSerializer,AppointmentSerializer
from .models import Store, Staff,Appointment
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from twilio.rest import Client
from django.conf import settings
from rest_framework.decorators import action

from . import serializers

class RegisterUserView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()  # Save the user and associated profile
        return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)



class LoginUserView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        token, created = Token.objects.get_or_create(user=user)
        return Response(
            {
                "token": token.key, 
                "message": "User registered successfully"
            },
            status=status.HTTP_200_OK)


class LogoutUserView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        request.user.auth_token.delete()
        return Response({
            "status_code": status.HTTP_200_OK,
            "status": "success",
            "message": "Successfully logged out"
        }, status=status.HTTP_200_OK)



class StoreViewSet(viewsets.ModelViewSet):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        store = serializer.save()
        
        headers = self.get_success_headers(serializer.data)
        response_data = {
            "status_code": status.HTTP_201_CREATED,
            "status": "success",
            "message": "Store created successfully",
            "store": serializer.data
        }
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=['get'], url_path='details')
    def store_details(self, request, pk=None):
        store = self.get_object()
        store_serializer = self.get_serializer(store)
        staff_serializer = StaffSerializer(store.staff.all(), many=True)
        
        response_data = {
            "status_code": status.HTTP_200_OK,
            "status": "success",
            "message": "Store details retrieved successfully",
            "store": {
                **store_serializer.data,
                "staff": staff_serializer.data  # Include the associated staff within the store object
            }
        }
        return Response(response_data, status=status.HTTP_200_OK)



class StaffViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        staff_data = request.data.get('staff', [])
        store_ids_or_names = request.data.get('stores', [])

        # Ensure the stores are provided in the request
        if not store_ids_or_names:
            return Response({"stores": ["This field is required."]}, status=status.HTTP_400_BAD_REQUEST)

        created_staff = []

        for staff_member_data in staff_data:
            # Assign the stores to each staff member data before validation
            staff_member_data['stores'] = store_ids_or_names
            
            # Validate and create staff member
            serializer = self.get_serializer(data=staff_member_data)
            serializer.is_valid(raise_exception=True)
            staff_member = serializer.save()

            created_staff.append(staff_member)

        # Prepare response data
        response_data = {
            "status_code": status.HTTP_201_CREATED,
            "status": "success",
            "message": "Staff member(s) created and assigned to stores successfully",
            "staff": [StaffSerializer(staff).data for staff in created_staff]
        }

        return Response(response_data, status=status.HTTP_201_CREATED)



class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Save the appointment
        appointment = serializer.save()

        # Send SMS after the appointment is successfully booked
        phone_number = appointment.phone
        message_body = (
            f"Dear {appointment.username}, your appointment at {appointment.store.name} "
            f"with {appointment.therapist.username} is confirmed for {appointment.date} "
            f"from {appointment.start_time} to {appointment.end_time}. Thank you!"
        )

        # Send the SMS
        self.send_sms(phone_number, message_body)

        response_data = {
            "status_code": status.HTTP_201_CREATED,
            "status": "success",
            "message": "Appointment created successfully. You will receive a message with the details.",
            "appointment": serializer.data
        }
        return Response(response_data, status=status.HTTP_201_CREATED)

    def send_sms(self, to, message_body):
        """Helper function to send SMS using Twilio"""
        account_sid = settings.TWILIO_ACCOUNT_SID
        auth_token = settings.TWILIO_AUTH_TOKEN
        twilio_phone_number = settings.TWILIO_PHONE_NUMBER

        client = Client(account_sid, auth_token)

        try:
            message = client.messages.create(
                from_=twilio_phone_number,
                body=message_body,
                to=to
            )
            print(f"SMS sent: {message.sid}")
        except Exception as e:
            print(f"Failed to send SMS: {str(e)}")

