from rest_framework import viewsets, status, serializers as drf_serializers
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.contrib.auth import authenticate, get_user_model
from django.conf import settings
from django.utils import timezone
from asgiref.sync import sync_to_async
from .models import Agent, ComposioConnection, ChatMessage, FileAttachment, Trigger, TriggerExecution, Workflow, WorkflowExecution, UserProfile, User, AgentTemplate, UsageLog, MessagingChannel, MessagingSession
from . import serializers
from .serializers import (
    UserSerializer, UserRegistrationSerializer, AgentSerializer,
    ComposioConnectionSerializer, ChatMessageSerializer, ChatRequestSerializer,
    FileAttachmentSerializer, TriggerSerializer, TriggerExecutionSerializer,
    WorkflowSerializer, WorkflowExecutionSerializer,
    ConnectionCreateRequestSerializer, ConnectionAuthResponseSerializer,
    DisconnectResponseSerializer, AgentChatRequestSerializer, AgentChatResponseSerializer,
    RegistrationResponseSerializer, LoginRequestSerializer, LoginResponseSerializer,
    LogoutResponseSerializer,
    EmailVerificationResendResponseSerializer, EmailVerificationConfirmResponseSerializer,
    TokenRefreshCookieResponseSerializer, PasswordResetRequestSerializer,
    PasswordResetRequestResponseSerializer, PasswordResetConfirmRequestSerializer,
    PasswordResetConfirmResponseSerializer, AvailableToolsResponseSerializer,
    AgentAvailableToolsResponseSerializer, SuggestedPromptsRequestSerializer,
    SuggestedPromptsResponseSerializer, AgentToolsResponseSerializer,
    AddAgentToolRequestSerializer, AddAgentToolResponseSerializer,
    AgentTemplateSerializer, InstantiateTemplateRequestSerializer,
    InstantiateTemplateResponseSerializer, CreditBalanceSerializer,
    UsageLogSerializer, AddCreditsRequestSerializer, AddCreditsResponseSerializer,
    MessagingChannelSerializer, ConnectTelegramBotSerializer, DisconnectMessagingChannelSerializer,
    AppConnectionDisplaySerializer, ManualAgentCreateSerializer, ManualAgentCreateResponseSerializer
)
from .agent_service import AgentService
from .composio_config import APP_SLUGS, APP_METADATA, TOP_SLUGS_BY_APP
from .agent_tools_config import AGENT_TOOLS, get_all_tool_names, is_valid_tool
import traceback
import asyncio
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from rest_framework_simplejwt.tokens import RefreshToken
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.encoding import force_str, force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.core.mail import send_mail
from allauth.account.models import EmailAddress
import requests
import os
from pathlib import Path
from openai import OpenAI
import qrcode
from io import BytesIO
import base64
from PIL import Image
from django.http import StreamingHttpResponse
from .streaming_utils import (
    format_sse_event, send_status_event, send_tool_call_start_event,
    send_tool_call_result_event, send_content_delta_event,
    send_message_complete_event, send_done_event, send_error_event
)

# The FAILURE_KEYWORDS list has been removed as we are using the
# "dynamic selection on every message" model, not "try/fail/adapt".


def convert_image_to_base64(file_attachment):
    """
    Convert a FileAttachment image to base64 data URI for GPT-5 nano vision.

    Args:
        file_attachment: FileAttachment model instance with image data

    Returns:
        str: Base64 data URI (e.g., "data:image/jpeg;base64,/9j/4AAQ...")
        None: If conversion fails or file is not an image
    """
    try:
        # Get file content from database
        image_data = file_attachment.get_file_content() if hasattr(file_attachment, 'get_file_content') else file_attachment.file_content

        if not image_data:
            return None

        # Convert memoryview to bytes if needed
        if isinstance(image_data, memoryview):
            image_data = bytes(image_data)

        # Encode to base64
        base64_image = base64.b64encode(image_data).decode('utf-8')

        # Get MIME type (default to jpeg if not available)
        mime_type = file_attachment.mime_type or 'image/jpeg'

        # Return data URI
        return f"data:{mime_type};base64,{base64_image}"

    except Exception as e:
        print(f"❌ Error converting image to base64: {e}")
        return None


@extend_schema(
    tags=['auth'],
    operation_id='auth_register',
    request=UserRegistrationSerializer,
    responses={
        201: OpenApiResponse(response=RegistrationResponseSerializer, description='User created'),
        400: OpenApiResponse(description='Validation error')
    },
    description='Register a new user with username, email, password and password_confirm. On success, JWT tokens are set as HttpOnly cookies; the response contains the user only.'
)
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Handles new user registration without auto-login.
    """
    import uuid
    from django.utils import timezone

    print(f"📝 Registration attempt with data: {request.data}")
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()

        # Generate custom verification token and set user as unverified
        verification_token = str(uuid.uuid4())
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.is_verified = False
        profile.verification_token = verification_token
        profile.verification_token_created_at = timezone.now()
        profile.save()

        # Ensure EmailAddress record exists and send verification
        EmailAddress.objects.update_or_create(
            user=user, email=user.email,
            defaults={'verified': False, 'primary': True}
        )
        _send_email_verification_with_token(request, user, verification_token)

        print(f"✅ User created: {user.username} (verification email sent with custom token, is_verified=False, NO auto-login)")

        # Return user data WITHOUT setting JWT cookies (no auto-login)
        response = Response({
            'user': UserSerializer(user).data,
            'detail': 'Registration successful. Please check your email to verify your account.'
        }, status=status.HTTP_201_CREATED)
        return response
    print(f"❌ Registration validation errors: {serializer.errors}")
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['auth'],
    operation_id='auth_login',
    summary='Authenticate user and set JWT cookies',
    description='Authenticates a user with username (or email alias) and password, verifies email ownership, then issues new HttpOnly JWT cookies. The response includes the serialized user profile with UUID identifiers.',
    request=LoginRequestSerializer,
    responses={
        200: OpenApiResponse(
            response=LoginResponseSerializer,
            description='Login succeeded. HttpOnly access/refresh cookies were issued.',
            examples=[
                OpenApiExample(
                    'Login success',
                    value={
                        'user': {
                            'id': '8d8d8a34-8a0c-4a0b-92bb-6de93882e298',
                            'username': 'founder1',
                            'email': 'founder1@example.com',
                            'agent_count': 2
                        }
                    },
                    response_only=True,
                    status_codes=['200']
                )
            ]
        ),
        400: OpenApiResponse(description='Missing username/email or password.'),
        401: OpenApiResponse(description='Credentials are invalid.'),
        403: OpenApiResponse(description='Email verification required.')
    },
    examples=[
        OpenApiExample(
            'Login with username',
            value={'username': 'founder1', 'password': 'StrongPass123!'},
            request_only=True
        ),
        OpenApiExample(
            'Login with email',
            value={'username': 'founder1@example.com', 'password': 'StrongPass123!'},
            summary='When frontend sends email via username field',
            request_only=True
        )
    ]
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Handles user login with username and password.
    """
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response(
            {'error': 'Please provide both username and password'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = authenticate(username=username, password=password)
    
    if not user:
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Check if user is verified (using UserProfile)
    profile, _ = UserProfile.objects.get_or_create(user=user)
    if not profile.is_verified:
        # Send verification email if not verified
        email_rec, _ = EmailAddress.objects.get_or_create(
            user=user, email=user.email, defaults={'verified': False, 'primary': True}
        )
        _send_email_verification(request, user)
        return Response(
            {'detail': 'Email verification required. Verification email sent.'},
            status=status.HTTP_403_FORBIDDEN
        )

    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)
    response = Response({
        'user': UserSerializer(user).data
    })
    cookie_secure = False if settings.DEBUG else True
    response.set_cookie('access', access_token, httponly=True, secure=cookie_secure, samesite='Lax', max_age=24 * 60 * 60)
    response.set_cookie('refresh', refresh_token, httponly=True, secure=cookie_secure, samesite='Lax', max_age=7 * 24 * 60 * 60)
    return response


@extend_schema(
    tags=['auth'],
    operation_id='auth_logout',
    summary='Logout current user and clear JWT cookies',
    description='Removes the HttpOnly `access` and `refresh` cookies for the authenticated user and deletes any DRF token if present. No request body is required—authentication comes from the cookies.',
    responses={
        200: OpenApiResponse(
            response=LogoutResponseSerializer,
            description='Logout success. Cookies cleared.',
            examples=[
                OpenApiExample(
                    'Logout success',
                    value={'message': 'Successfully logged out'},
                    response_only=True,
                    status_codes=['200']
                )
            ]
        ),
        401: OpenApiResponse(description='Authentication required.')
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Handles user logout by deleting their auth token.
    """
    try:
        request.user.auth_token.delete()
    except Exception:
        pass
    response = Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)
    response.delete_cookie('access')
    response.delete_cookie('refresh')
    return response


@extend_schema(
    tags=['auth'],
    operation_id='auth_me',
    summary='Retrieve authenticated user profile',
    description='Returns the authenticated user profile (UUID id, username, email, agent_count). Authentication relies on the JWT access token stored in the HttpOnly cookie. This is the single source of truth for “current user”.',
    responses={
        200: OpenApiResponse(
            response=UserSerializer,
            description='Current user profile.',
            examples=[
                OpenApiExample(
                    'Current user',
                    value={
                        'id': '8d8d8a34-8a0c-4a0b-92bb-6de93882e298',
                        'username': 'founder1',
                        'email': 'founder1@example.com',
                        'agent_count': 2
                    },
                    response_only=True,
                    status_codes=['200']
                )
            ]
        ),
        401: OpenApiResponse(description='Authentication required.')
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    """
    Returns information about the currently authenticated user.
    Authentication is handled via JWT token stored in HttpOnly 'access' cookie.
    """
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
@ensure_csrf_cookie
@extend_schema(
    tags=['auth'],
    operation_id='auth_csrf_token',
    responses={
        200: OpenApiResponse(
            response=drf_serializers.Serializer,
            description='CSRF cookie set successfully',
            examples=[
                OpenApiExample(
                    'Success',
                    value={'detail': 'CSRF cookie set'},
                    response_only=True
                )
            ]
        )
    },
    description='Sets a CSRF token cookie for the client. This endpoint is used by SPAs (Single Page Applications) to obtain a CSRF token for making authenticated requests. The CSRF token is automatically included in subsequent requests via the cookie.'
)
def csrf_token(request):
    """
    Sets a CSRF token cookie for the client.
    This is needed for SPAs using cookie-based authentication to prevent CSRF attacks.
    """
    return Response({'detail': 'CSRF cookie set'})


@extend_schema(
    tags=['credits'],
    operation_id='credits_balance',
    summary='Get user credit balance',
    responses=CreditBalanceSerializer,
    examples=[
        OpenApiExample(
            'Success Response',
            value={
                'total_credits': 95,
                'credits_used': 5,
                'credit_refresh_date': '2025-11-01T10:30:00Z',
                'next_refresh_date': '2025-12-01T10:30:00Z'
            },
            response_only=True,
            status_codes=['200']
        )
    ],
    description='Returns the current user\'s credit balance and historical usage. Credits are deducted for each message sent to an agent (1 credit per message) and refresh monthly.\n\n**Response Fields:**\n- `total_credits`: Current available credits\n- `credits_used`: Total credits consumed (historical)\n- `credit_refresh_date`: When credits were last refreshed\n- `next_refresh_date`: When credits will refresh next (one month from credit_refresh_date)'
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def credit_balance(request):
    """
    Get the current user's credit balance.
    Also checks and refreshes credits if a month has passed.
    """
    # Check and refresh credits if needed
    request.user.check_and_refresh_credits()
    # Refresh the user object to get updated values
    request.user.refresh_from_db()

    return Response({
        'total_credits': request.user.total_credits,
        'credits_used': request.user.credits_used,
        'credit_refresh_date': request.user.credit_refresh_date,
        'next_refresh_date': request.user.get_next_refresh_date()
    })


@extend_schema(
    tags=['credits'],
    operation_id='credits_usage_history',
    summary='Get credit usage history',
    responses=UsageLogSerializer(many=True),
    examples=[
        OpenApiExample(
            'Success Response',
            value=[
                {
                    'id': 1,
                    'action_type': 'message',
                    'action_type_display': 'Chat Message',
                    'credits_used': 1,
                    'credits_remaining': 99,
                    'description': 'Chat message to Email Assistant',
                    'metadata': {
                        'message_length': 45,
                        'agent_id': '3fa85f64-5717-4562-b3fc-2c963f66afa6',
                        'agent_name': 'Email Assistant'
                    },
                    'agent_name': 'Email Assistant',
                    'created_at': '2025-11-26T10:30:00Z'
                },
                {
                    'id': 2,
                    'action_type': 'admin_add',
                    'action_type_display': 'Admin Credit Addition',
                    'credits_used': -50,
                    'credits_remaining': 100,
                    'description': 'Welcome bonus',
                    'metadata': {'credits_added': 50},
                    'agent_name': None,
                    'created_at': '2025-11-26T10:00:00Z'
                }
            ],
            response_only=True,
            status_codes=['200']
        )
    ],
    description='Returns the user\'s credit usage history, showing all transactions including messages sent, credits added, etc. Ordered by most recent first. Returns last 50 transactions.\n\n**Note:** Negative `credits_used` values indicate credits were added (not deducted).'
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def credit_usage_history(request):
    """Get the user's credit usage history"""
    logs = UsageLog.objects.filter(user=request.user)[:50]  # Last 50 transactions
    serializer = UsageLogSerializer(logs, many=True)
    return Response(serializer.data)


@extend_schema(
    tags=['credits'],
    operation_id='credits_add',
    summary='Add credits to a user (Admin only)',
    request=AddCreditsRequestSerializer,
    responses=AddCreditsResponseSerializer,
    examples=[
        OpenApiExample(
            'Request Example',
            value={
                'user_id': '3fa85f64-5717-4562-b3fc-2c963f66afa6',
                'amount': 50,
                'description': 'Welcome bonus'
            },
            request_only=True
        ),
        OpenApiExample(
            'Success Response',
            value={
                'message': 'Successfully added 50 credits to user john',
                'user_id': '3fa85f64-5717-4562-b3fc-2c963f66afa6',
                'credits_added': 50,
                'new_balance': 150
            },
            response_only=True,
            status_codes=['200']
        )
    ],
    description='Add credits to a user account. This endpoint is restricted to admin users only (staff/superuser). Regular users cannot add credits to their own or other accounts.\n\n**Request Body:**\n- `user_id`: UUID of the user to credit\n- `amount`: Number of credits to add (minimum 1)\n- `description`: Optional reason for adding credits'
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_credits(request):
    """Add credits to a user (admin only)"""
    # Check if user is staff/admin
    if not request.user.is_staff:
        return Response(
            {'error': 'Admin access required'},
            status=status.HTTP_403_FORBIDDEN
        )

    serializer = AddCreditsRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user_id = serializer.validated_data['user_id']
    amount = serializer.validated_data['amount']
    description = serializer.validated_data.get('description', 'Admin credit addition')

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Add credits
    from .credits import add_credits as add_credits_util
    add_credits_util(user, amount, action_type='admin_add', description=description)

    return Response({
        'message': f'Successfully added {amount} credits to user {user.username}',
        'user_id': str(user.id),
        'credits_added': amount,
        'new_balance': user.total_credits
    })


@api_view(['POST'])
@permission_classes([AllowAny])
@extend_schema(
    tags=['auth'],
    operation_id='auth_token_refresh_cookie',
    responses={
        200: OpenApiResponse(response=TokenRefreshCookieResponseSerializer, description='New access cookie issued'),
        401: OpenApiResponse(description='Invalid or missing refresh cookie')
    },
    description='Refreshes the JWT access token for cookie-based authentication. Reads the refresh token from the HttpOnly "refresh" cookie, validates it, and issues a new access token stored in the HttpOnly "access" cookie. No request body required. This endpoint is essential for maintaining authenticated sessions when the access token expires (after 24 hours).'
)
def refresh_access_cookie(request):
    """
    Refreshes the JWT access token using the refresh token from cookies.

    Flow:
    1. Reads the 'refresh' HttpOnly cookie
    2. Validates the refresh token
    3. Generates a new access token
    4. Sets the new access token in the 'access' HttpOnly cookie (24 hours expiry)
    5. Returns success message

    This is needed because access tokens expire after 24 hours, and the frontend
    needs to refresh them periodically to maintain authentication.
    """
    refresh_cookie = request.COOKIES.get('refresh')
    if not refresh_cookie:
        raise AuthenticationFailed('Missing refresh cookie')
    try:
        refresh = RefreshToken(refresh_cookie)
        new_access = str(refresh.access_token)
    except Exception:
        raise AuthenticationFailed('Invalid refresh token')
    cookie_secure = False if settings.DEBUG else True
    resp = Response({'detail': 'Access token refreshed'})
    resp.set_cookie('access', new_access, httponly=True, secure=cookie_secure, samesite='Lax', max_age=24 * 60 * 60)
    return resp

@extend_schema(
    tags=['auth'],
    operation_id='auth_password_reset_request',
    summary='Send password reset email',
    description='Initiates the password reset flow for the provided email. Always returns success to avoid leaking which accounts exist. Generates a uid/token pair and emails a reset link that expires using Django’s default token generator.',
    request=PasswordResetRequestSerializer,
    responses={
        200: PasswordResetRequestResponseSerializer
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request(request):
    print(f"🔐 Password reset request received")
    serializer = PasswordResetRequestSerializer(data=request.data)
    if not serializer.is_valid():
        print(f"❌ Password reset request validation errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    email = serializer.validated_data['email']
    print(f"📧 Password reset requested for email: {email}")
    try:
        user = User.objects.get(email__iexact=email)
        print(f"✅ User found: {user.username} (ID: {user.id})")
        _send_password_reset_email(request, user)
    except User.DoesNotExist:
        print(f"⚠️ Password reset requested for non-existent email: {email} (returning generic success to avoid email enumeration)")
        # Return generic response to avoid leaking which emails exist
    
    return Response(
        {'detail': 'If an account exists for that email, a reset link has been sent.'},
        status=status.HTTP_200_OK
    )


@extend_schema(
    tags=['auth'],
    operation_id='auth_password_reset_confirm',
    summary='Reset password using uid/token',
    description='Completes the password reset flow using the uid/token pair from the email link. Validates password strength and sets the new password for the matching user.',
    request=PasswordResetConfirmRequestSerializer,
    responses={
        200: PasswordResetConfirmResponseSerializer,
        400: OpenApiResponse(description='Invalid uid/token or password validation error')
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    print(f"🔐 Password reset confirm request received")
    serializer = PasswordResetConfirmRequestSerializer(data=request.data)
    if not serializer.is_valid():
        print(f"❌ Password reset confirm validation errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    uid = serializer.validated_data['uid']
    token = serializer.validated_data['token']
    password = serializer.validated_data['password']
    
    print(f"🔍 Attempting to decode uid and validate token...")
    try:
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id)
        print(f"✅ User found: {user.username} (ID: {user.id}, Email: {user.email})")
    except (User.DoesNotExist, ValueError, TypeError) as e:
        print(f"❌ Invalid uid or user not found: {e}")
        return Response({'detail': 'Invalid or expired link.'}, status=status.HTTP_400_BAD_REQUEST)
    
    if not default_token_generator.check_token(user, token):
        print(f"❌ Invalid or expired token for user: {user.username} (ID: {user.id})")
        return Response({'detail': 'Invalid or expired link.'}, status=status.HTTP_400_BAD_REQUEST)
    
    print(f"✅ Token validated successfully for user: {user.username}")
    
    try:
        validate_password(password, user=user)
        print(f"✅ Password strength validation passed")
    except ValidationError as e:
        print(f"❌ Password validation failed: {e.messages}")
        return Response({'password': e.messages}, status=status.HTTP_400_BAD_REQUEST)
    
    user.set_password(password)
    user.save()
    print(f"✅ Password reset successful for user: {user.username} (ID: {user.id})")
    
    return Response({'detail': 'Password has been reset successfully.'}, status=status.HTTP_200_OK)


def _send_email_verification(request, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    verify_url = request.build_absolute_uri(
        reverse('auth_email_verify_confirm')
    ) + f'?uid={uid}&token={token}'
    
    # EmailJS configuration
    # NOTE: To use EmailJS from server-side, you must enable "Allow server-side API calls" 
    # in your EmailJS dashboard: https://dashboard.emailjs.com/admin/integration
    emailjs_service_id = os.getenv('EMAILJS_SERVICE_ID')
    emailjs_template_id = os.getenv('EMAILJS_TEMPLATE_ID')
    emailjs_public_key = os.getenv('EMAILJS_PUBLIC_KEY')
    emailjs_private_key = os.getenv('EMAILJS_PRIVATE_KEY')
    
    # If EmailJS is configured, use it; otherwise fall back to Django's send_mail
    if emailjs_service_id and emailjs_template_id and emailjs_public_key and emailjs_private_key:
        try:
            # EmailJS API endpoint
            emailjs_url = 'https://api.emailjs.com/api/v1.0/email/send'
            
            # Prepare EmailJS payload
            # Note: The HTML template should be created in EmailJS platform using verification_email.html
            # Template variables {{username}} and {{verify_url}} will be replaced by EmailJS
            payload = {
                'service_id': emailjs_service_id,
                'template_id': emailjs_template_id,
                'user_id': emailjs_public_key,
                'template_params': {
                    'to_email': user.email,
                    'email': user.email,  # Some templates use 'email' instead of 'to_email'
                    'username': user.username,
                    'verify_url': verify_url,
                    'subject': 'Verify your email',
                }
            }
            
            # Send email via EmailJS
            # EmailJS v1.0 API: accessToken can be in request body or as query param
            # Try both methods for compatibility
            try:
                # Method 1: accessToken in request body
                payload_with_token = payload.copy()
                payload_with_token['accessToken'] = emailjs_private_key
                response = requests.post(
                    emailjs_url,
                    json=payload_with_token,
                    timeout=10
                )
                response.raise_for_status()
            except Exception as e1:
                # Method 2: accessToken as query parameter (fallback)
                print(f"⚠️ EmailJS method 1 failed, trying query param: {e1}")
                response = requests.post(
                    emailjs_url,
                    json=payload,
                    params={'accessToken': emailjs_private_key},
                    timeout=10
                )
                response.raise_for_status()
            print(f"✅ Verification email sent via EmailJS to {user.email}")
        except Exception as e:
            error_details = 'No response'
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_details = e.response.text[:200]  # First 200 chars
                except:
                    error_details = str(e.response.status_code)
            print(f"❌ EmailJS error: {e}. Response: {error_details}. Falling back to Django send_mail.")
            # Fallback to Django's send_mail
            subject = 'Verify your email'
            message = f'Hi {user.username},\n\nPlease verify your email by clicking this link:\n{verify_url}\n\nIf you did not sign up, you can ignore this email.'
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
    else:
        # Use Django's send_mail if EmailJS is not configured
        subject = 'Verify your email'
        message = f'Hi {user.username},\n\nPlease verify your email by clicking this link:\n{verify_url}\n\nIf you did not sign up, you can ignore this email.'
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)


def _send_email_verification_with_token(request, user, verification_token):
    """Send email verification with custom token using EmailJS, linking to frontend verification page"""
    from django.utils.http import urlsafe_base64_encode
    from django.utils.encoding import force_bytes

    # Encode user ID for URL
    uid = urlsafe_base64_encode(force_bytes(user.pk))

    # Build verification URL pointing to FRONTEND (not backend API)
    frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
    verify_url = f"{frontend_url}/auth/verify?userId={uid}&token={verification_token}"

    # EmailJS configuration
    emailjs_service_id = os.getenv('EMAILJS_SERVICE_ID')
    emailjs_template_id = os.getenv('EMAILJS_TEMPLATE_ID')
    emailjs_public_key = os.getenv('EMAILJS_PUBLIC_KEY')
    emailjs_private_key = os.getenv('EMAILJS_PRIVATE_KEY')

    # If EmailJS is configured, use it; otherwise fall back to Django's send_mail
    if emailjs_service_id and emailjs_template_id and emailjs_public_key and emailjs_private_key:
        try:
            # EmailJS API endpoint
            emailjs_url = 'https://api.emailjs.com/api/v1.0/email/send'

            # Prepare EmailJS payload with custom token
            payload = {
                'service_id': emailjs_service_id,
                'template_id': emailjs_template_id,
                'user_id': emailjs_public_key,
                'template_params': {
                    'to_email': user.email,
                    'email': user.email,
                    'username': user.username,
                    'verify_url': verify_url,  # Frontend URL with custom token
                    'subject': 'Verify your email',
                }
            }

            # Send email via EmailJS
            try:
                # Method 1: accessToken in request body
                payload_with_token = payload.copy()
                payload_with_token['accessToken'] = emailjs_private_key
                response = requests.post(
                    emailjs_url,
                    json=payload_with_token,
                    timeout=10
                )
                response.raise_for_status()
            except Exception as e1:
                # Method 2: accessToken as query parameter (fallback)
                print(f"⚠️ EmailJS method 1 failed, trying query param: {e1}")
                response = requests.post(
                    emailjs_url,
                    json=payload,
                    params={'accessToken': emailjs_private_key},
                    timeout=10
                )
                response.raise_for_status()
            print(f"✅ Custom verification email sent via EmailJS to {user.email} with token: {verification_token[:8]}...")
        except Exception as e:
            error_details = 'No response'
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_details = e.response.text[:200]
                except:
                    error_details = str(e.response.status_code)
            print(f"❌ EmailJS error: {e}. Response: {error_details}. Falling back to Django send_mail.")
            # Fallback to Django's send_mail
            subject = 'Verify your email'
            message = f'Hi {user.username},\n\nPlease verify your email by clicking this link:\n{verify_url}\n\nIf you did not sign up, you can ignore this email.'
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
    else:
        # Use Django's send_mail if EmailJS is not configured
        subject = 'Verify your email'
        message = f'Hi {user.username},\n\nPlease verify your email by clicking this link:\n{verify_url}\n\nIf you did not sign up, you can ignore this email.'
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
        print(f"✅ Verification email sent via Django to {user.email}")


def _send_password_reset_email(request, user):
    print(f"📧 Preparing password reset email for user: {user.username} (Email: {user.email})")
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000').rstrip('/')
    reset_path = os.getenv('PASSWORD_RESET_PATH', '/reset-password')
    if not reset_path.startswith('/'):
        reset_path = f'/{reset_path}'
    reset_link = f"{frontend_url}{reset_path}?uid={uid}&token={token}"
    print(f"🔗 Generated reset link: {reset_link[:50]}... (uid: {uid[:20]}..., token: {token[:10]}...)")
    
    emailjs_service_id = os.getenv('EMAILJS_SERVICE_ID')
    password_reset_template_id = os.getenv('EMAILJS_PASSWORD_RESET_TEMPLATE_ID')
    emailjs_public_key = os.getenv('EMAILJS_PUBLIC_KEY')
    emailjs_private_key = os.getenv('EMAILJS_PRIVATE_KEY')
    
    if emailjs_service_id and password_reset_template_id and emailjs_public_key and emailjs_private_key:
        print(f"📤 Using EmailJS to send password reset email (Service: {emailjs_service_id}, Template: {password_reset_template_id})")
        payload = {
            'service_id': emailjs_service_id,
            'template_id': password_reset_template_id,
            'user_id': emailjs_public_key,
            'template_params': {
                'to_email': user.email,
                'email': user.email,
                'username': user.username,
                'link': reset_link,
                'expires_in': '1 hour'
            }
        }
        try:
            # Method 1: accessToken in request body
            payload_with_token = payload.copy()
            payload_with_token['accessToken'] = emailjs_private_key
            response = requests.post('https://api.emailjs.com/api/v1.0/email/send', json=payload_with_token, timeout=10)
            response.raise_for_status()
            print(f"✅ Password reset email sent via EmailJS (method 1) to {user.email}")
            print(f"📊 EmailJS Response Status: {response.status_code}")
            try:
                response_data = response.json() if response.text else {}
                print(f"📊 EmailJS Response Body: {response_data}")
            except:
                print(f"📊 EmailJS Response Text: {response.text[:200]}")
        except Exception as e1:
            print(f"⚠️ Password reset email (method 1 - body token) failed: {e1}")
            error_details = 'No response'
            if hasattr(e1, 'response') and e1.response is not None:
                try:
                    error_details = e1.response.text[:200]  # First 200 chars
                except:
                    error_details = str(e1.response.status_code)
            print(f"📊 EmailJS Error Response: {error_details}")
            
            # Method 2: accessToken as query parameter (fallback)
            try:
                print(f"🔄 Trying EmailJS method 2 (query param token)...")
                response = requests.post(
                    'https://api.emailjs.com/api/v1.0/email/send',
                    json=payload,
                    params={'accessToken': emailjs_private_key},
                    timeout=10
                )
                response.raise_for_status()
                print(f"✅ Password reset email sent via EmailJS (method 2) to {user.email}")
                print(f"📊 EmailJS Response Status: {response.status_code}")
                try:
                    response_data = response.json() if response.text else {}
                    print(f"📊 EmailJS Response Body: {response_data}")
                except:
                    print(f"📊 EmailJS Response Text: {response.text[:200]}")
            except Exception as e2:
                error_details = 'No response'
                if hasattr(e2, 'response') and e2.response is not None:
                    try:
                        error_details = e2.response.text[:200]  # First 200 chars
                    except:
                        error_details = str(e2.response.status_code)
                print(f"❌ EmailJS error (both methods failed): {e2}. Response: {error_details}. Falling back to Django send_mail.")
                # Fallback to Django's send_mail
                subject = 'Reset your password'
                message = (
                    f'Hi {user.username},\n\n'
                    f'We received a request to reset your password. Click the link below to set a new one:\n'
                    f'{reset_link}\n\n'
                    f'If you did not request this, you can safely ignore this email.\n\n'
                    f'Thanks,\nThe AgentCreator Team'
                )
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
                print(f"✅ Password reset email sent via Django send_mail fallback to {user.email}")
        return
    
    # Fallback to Django send_mail if EmailJS is not configured
    print(f"⚠️ EmailJS not configured, using Django send_mail fallback")
    subject = 'Reset your password'
    message = (
        f'Hi {user.username},\n\n'
        f'We received a request to reset your password. Click the link below to set a new one:\n'
        f'{reset_link}\n\n'
        f'If you did not request this, you can safely ignore this email.\n\n'
        f'Thanks,\nThe AgentCreator Team'
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
    print(f"✅ Password reset email sent via Django send_mail to {user.email}")


@extend_schema(
    tags=['auth'],
    operation_id='auth_email_verify_resend',
    summary='Resend email verification',
    description='Resends the email verification link to the authenticated user\'s email address. The email address is automatically retrieved from the authenticated user account (request.user.email), so no email parameter or request body is required. This endpoint uses the user from the authentication token (JWT in HttpOnly cookie). A new verification token is generated and sent to the user\'s email address via EmailJS (if configured) or Django send_mail. The verification link expires after a set period and can only be used once.',
    responses={
        200: OpenApiResponse(
            response=EmailVerificationResendResponseSerializer,
            description='Verification email sent successfully to the authenticated user\'s email address',
            examples=[
                OpenApiExample(
                    'Success Response',
                    value={
                        'detail': 'Verification email sent.'
                    },
                    response_only=True,
                    status_codes=['200']
                )
            ]
        ),
        401: OpenApiResponse(description='Authentication required. User must be logged in with valid JWT token. The email address is taken from the authenticated user account.')
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resend_email_verification(request):
    _send_email_verification(request, request.user)
    return Response({'detail': 'Verification email sent.'})

# Public endpoint for resending email verification (no auth required)
@extend_schema(
    tags=['auth'],
    operation_id='auth_email_verify_resend_public',
    summary='Resend email verification (public)',
    description='Public endpoint to resend email verification link. Does not require authentication. Accepts an email address in the request body.',
    request={'application/json': {'type': 'object', 'properties': {'email': {'type': 'string', 'format': 'email'}}, 'required': ['email']}},
    responses={
        200: OpenApiResponse(
            response=EmailVerificationResendResponseSerializer,
            description='Verification email sent if the email exists in the system',
            examples=[
                OpenApiExample(
                    'Success Response',
                    value={
                        'detail': 'If this email is registered, a verification link has been sent.'
                    },
                    response_only=True,
                    status_codes=['200']
                )
            ]
        ),
        400: OpenApiResponse(description='Invalid email format')
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def resend_email_verification_public(request):
    from django.contrib.auth import get_user_model
    import uuid
    from django.utils import timezone

    User = get_user_model()

    email = request.data.get('email')
    if not email:
        return Response({'error': 'Email is required'}, status=400)

    # Always return success to prevent email enumeration
    # But only send email if user exists
    try:
        user = User.objects.get(email=email)
        # Generate new verification token
        new_token = str(uuid.uuid4())
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.verification_token = new_token
        profile.verification_token_created_at = timezone.now()
        profile.save()
        # Send email with new token
        _send_email_verification_with_token(request, user, new_token)
        print(f"✅ New verification email sent to {user.email} with token: {new_token[:8]}...")
    except User.DoesNotExist:
        # Don't reveal if email exists or not
        pass

    return Response({'detail': 'If this email is registered, a verification link has been sent.'})


@extend_schema(
    tags=['auth'],
    operation_id='auth_email_verify_confirm',
    responses={200: EmailVerificationConfirmResponseSerializer},
    description='Confirms email verification using uid and token from the verification link.',
    parameters=[
        OpenApiParameter(name='uid', type=OpenApiTypes.STR, location='query', required=True, description='Base64 user id'),
        OpenApiParameter(name='token', type=OpenApiTypes.STR, location='query', required=True, description='Verification token'),
    ]
)
@api_view(['GET'])
@permission_classes([AllowAny])
def email_verify_confirm(request):
    uidb64 = request.GET.get('uid')
    token = request.GET.get('token')
    
    # Frontend URL for redirect
    frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
    verify_page_url = f"{frontend_url}/verify-email"
    
    if not uidb64 or not token:
        # Redirect to frontend with error
        from django.http import HttpResponseRedirect
        return HttpResponseRedirect(f"{verify_page_url}?status=error&message=Invalid verification link")
    
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError):
        from django.http import HttpResponseRedirect
        return HttpResponseRedirect(f"{verify_page_url}?status=error&message=Invalid verification link")
    
    if not default_token_generator.check_token(user, token):
        from django.http import HttpResponseRedirect
        return HttpResponseRedirect(f"{verify_page_url}?status=error&message=Invalid or expired token")
    
    # Verify the email - update both EmailAddress and UserProfile
    EmailAddress.objects.update_or_create(
        user=user, email=user.email,
        defaults={'verified': True, 'primary': True}
    )
    
    # Mark user as verified in UserProfile
    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.is_verified = True
    profile.save()
    
    # Redirect to frontend with success
    from django.http import HttpResponseRedirect
    return HttpResponseRedirect(f"{verify_page_url}?status=success")


@extend_schema(
    tags=['auth'],
    operation_id='auth_verify_custom_token',
    summary='Verify email with custom token',
    description='Verifies user email using custom verification token stored in UserProfile. Accepts userId and token in request body.',
    request={'application/json': {
        'type': 'object',
        'properties': {
            'userId': {'type': 'string', 'description': 'Base64 encoded user ID'},
            'token': {'type': 'string', 'description': 'Verification token (UUID)'}
        },
        'required': ['userId', 'token']
    }},
    responses={
        200: OpenApiResponse(
            description='Email verified successfully',
            examples=[
                OpenApiExample(
                    'Success Response',
                    value={'detail': 'Email verified successfully', 'user': {'id': 'uuid', 'username': 'user', 'email': 'user@example.com', 'is_verified': True}},
                    response_only=True
                )
            ]
        ),
        400: OpenApiResponse(description='Invalid or expired token'),
        404: OpenApiResponse(description='User not found')
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email_with_token(request):
    """Verify email using custom token from UserProfile"""
    from django.utils.http import urlsafe_base64_decode
    from django.utils.encoding import force_str
    from datetime import timedelta
    from django.utils import timezone

    userId = request.data.get('userId')
    token = request.data.get('token')

    if not userId or not token:
        return Response({'error': 'Missing userId or token'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Decode user ID
        uid = force_str(urlsafe_base64_decode(userId))
        User = get_user_model()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response({'error': 'Invalid user ID'}, status=status.HTTP_404_NOT_FOUND)

    # Get user profile and check token
    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        return Response({'error': 'User profile not found'}, status=status.HTTP_404_NOT_FOUND)

    # Check if token matches
    if profile.verification_token != token:
        return Response({'error': 'Invalid verification token'}, status=status.HTTP_400_BAD_REQUEST)

    # Check if token has expired (optional: 24 hours expiry)
    if profile.verification_token_created_at:
        token_age = timezone.now() - profile.verification_token_created_at
        if token_age > timedelta(hours=24):
            return Response({'error': 'Verification token has expired. Please request a new one.'}, status=status.HTTP_400_BAD_REQUEST)

    # Mark user as verified
    profile.is_verified = True
    profile.verification_token = None  # Clear the token after use
    profile.verification_token_created_at = None
    profile.save()

    # Also update EmailAddress if using django-allauth
    EmailAddress.objects.filter(user=user, email=user.email).update(verified=True)

    print(f"✅ Email verified for user: {user.username}")

    # Return success with user data
    return Response({
        'detail': 'Email verified successfully',
        'user': {
            'id': str(user.id),
            'username': user.username,
            'email': user.email,
            'is_verified': True
        }
    }, status=status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(
        tags=['agents'],
        operation_id='agents_list',
        summary='List all agents',
        description='Returns list of all agents owned by the authenticated user. Agents are ordered by creation date (newest first).',
        responses={
            200: OpenApiResponse(
                response=AgentSerializer(many=True),
                description='List of agents',
                examples=[
                    OpenApiExample(
                        'Agents List Response',
                        value=[
                            {
                                'id': '3fa85f64-5717-4562-b3fc-2c963f66afa6',
                                'user': 'username',
                                'name': 'Email Manager',
                                'prompt': 'Help me manage my emails',
                                'tools': ['GMAIL_SEND_EMAIL', 'GMAIL_FETCH_EMAILS'],
                                'app_connections': ['GMAIL'],
                                'message_count': 5,
                                'created_at': '2024-01-01T00:00:00Z',
                                'updated_at': '2024-01-01T00:00:00Z'
                            }
                        ],
                        response_only=True,
                        status_codes=['200']
                    )
                ]
            ),
            401: OpenApiResponse(description='Authentication required')
        }
    ),
    create=extend_schema(
        tags=['agents'],
        operation_id='agents_create',
        summary='Create a new agent',
        description='''
        Creates a new AI agent with a prompt. The agent name is automatically generated from the prompt using AI.
        
        **New Flow:**
        - **`prompt`** (required): The agent's purpose/instructions
        - **`name`** (optional): If not provided, will be auto-generated from the prompt
        - **`app_connections`** (optional): List of app names (e.g., ["GMAIL", "SLACK"]). If empty or omitted, agent is created with no tools and can be added later.
        
        **Response:**
        - Returns the created agent with generated name and tools (if app_connections provided)
        - If no app_connections provided, tools will be empty array
        ''',
        request=AgentSerializer,
        responses={
            201: OpenApiResponse(
                response=AgentSerializer,
                description='Agent created successfully',
                examples=[
                    OpenApiExample(
                        'Agent Created (with tools)',
                        value={
                            'id': '3fa85f64-5717-4562-b3fc-2c963f66afa6',
                            'user': 'username',
                            'name': 'Email And Meeting Manager',  # Auto-generated
                            'prompt': 'Help me manage my emails and schedule meetings',
                            'tools': ['GMAIL_SEND_EMAIL', 'GMAIL_FETCH_EMAILS', 'GOOGLECALENDAR_CREATE_EVENT'],
                            'app_connections': ['GMAIL', 'GOOGLECALENDAR'],
                            'message_count': 0,
                            'created_at': '2024-01-01T00:00:00Z',
                            'updated_at': '2024-01-01T00:00:00Z'
                        },
                        response_only=True,
                        status_codes=['201']
                    ),
                    OpenApiExample(
                        'Agent Created (no tools)',
                        value={
                            'id': '3fa85f64-5717-4562-b3fc-2c963f66afa6',
                            'user': 'username',
                            'name': 'Email Assistant',  # Auto-generated
                            'prompt': 'Help me with emails',
                            'tools': [],  # Empty - can add tools later
                            'app_connections': [],  # Empty - can add later
                            'message_count': 0,
                            'created_at': '2024-01-01T00:00:00Z',
                            'updated_at': '2024-01-01T00:00:00Z'
                        },
                        response_only=True,
                        status_codes=['201']
                    )
                ]
            ),
            400: OpenApiResponse(description='Validation error'),
            401: OpenApiResponse(description='Authentication required')
        },
        examples=[
            OpenApiExample(
                'Create Agent (prompt only)',
                value={
                    'prompt': 'Help me manage my emails and schedule meetings'
                },
                request_only=True,
                description='Create agent with just a prompt. Name will be auto-generated.'
            ),
            OpenApiExample(
                'Create Agent (with tools)',
                value={
                    'prompt': 'Help me manage my emails',
                    'app_connections': ['GMAIL', 'SLACK']
                },
                request_only=True,
                description='Create agent with prompt and tools. Name will be auto-generated.'
            )
        ]
    ),
    retrieve=extend_schema(
        tags=['agents'],
        operation_id='agents_retrieve',
        summary='Get agent details',
        description='Returns details of a specific agent by ID. Users can only retrieve their own agents.',
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='Agent UUID',
                required=True
            )
        ],
        responses={
            200: OpenApiResponse(response=AgentSerializer, description='Agent details'),
            401: OpenApiResponse(description='Authentication required'),
            404: OpenApiResponse(description='Agent not found')
        }
    ),
    update=extend_schema(
        tags=['agents'],
        operation_id='agents_update',
        summary='Update agent (full)',
        description='Fully updates an agent. All fields are required. The tools list is automatically regenerated from app_connections.',
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='Agent UUID',
                required=True
            )
        ],
        request=AgentSerializer,
        responses={
            200: OpenApiResponse(response=AgentSerializer, description='Agent updated'),
            400: OpenApiResponse(description='Validation error'),
            401: OpenApiResponse(description='Authentication required'),
            404: OpenApiResponse(description='Agent not found')
        }
    ),
    partial_update=extend_schema(
        tags=['agents'],
        operation_id='agents_partial_update',
        summary='Update agent (partial)',
        description='Partially updates an agent. Only provided fields will be updated. If app_connections is updated, the tools list is automatically regenerated.',
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='Agent UUID',
                required=True
            )
        ],
        request=AgentSerializer,
        responses={
            200: OpenApiResponse(response=AgentSerializer, description='Agent updated'),
            400: OpenApiResponse(description='Validation error'),
            401: OpenApiResponse(description='Authentication required'),
            404: OpenApiResponse(description='Agent not found')
        },
        examples=[
            OpenApiExample(
                'Add Tools to Agent',
                value={
                    'app_connections': ['GMAIL', 'SLACK']
                },
                request_only=True,
                description='Add tools to an existing agent by updating app_connections'
            )
        ]
    ),
    destroy=extend_schema(
        tags=['agents'],
        operation_id='agents_destroy',
        summary='Delete agent',
        description='Deletes an agent by ID. Users can only delete their own agents.',
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='Agent UUID',
                required=True
            )
        ],
        responses={
            204: OpenApiResponse(description='Agent deleted successfully'),
            401: OpenApiResponse(description='Authentication required'),
            404: OpenApiResponse(description='Agent not found')
        }
    )
)
class AgentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing AI Agents (CRUD operations).

    Features:
    - Tools are automatically generated from app_connections
    - All operations are scoped to the authenticated user
    - Supports avatar upload via multipart/form-data in create and update endpoints
    """
    serializer_class = AgentSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_queryset(self):
        """
        Ensures users can only see their own agents.
        """
        return Agent.objects.filter(user=self.request.user)
    
    def _generate_agent_name(self, prompt: str) -> str:
        """
        Generates an agent name from the prompt using OpenAI.
        Returns a short, descriptive name (max 200 chars).
        """
        try:
            agent_service = AgentService(self.request.user)
            if not agent_service.openai_client:
                # Fallback if OpenAI is not configured
                return f"Agent {prompt[:50]}..." if len(prompt) > 50 else f"Agent {prompt}"
            
            system_prompt = (
                "You are a naming assistant. Generate a short, descriptive name for an AI agent "
                "based on its purpose/prompt. The name should be:\n"
                "1. 2-5 words maximum\n"
                "2. Descriptive of the agent's function\n"
                "3. Professional and clear\n"
                "4. No quotes or special characters\n"
                "5. Capitalize each word (Title Case)\n\n"
                "Return ONLY the name, nothing else."
            )
            
            response = agent_service.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Generate a name for an agent with this prompt:\n\n{prompt}"}
                ],
                temperature=0.7,
                max_completion_tokens=50
            )
            
            generated_name = response.choices[0].message.content.strip()
            
            # Clean up the name (remove quotes, extra whitespace)
            generated_name = generated_name.strip('"\'')
            generated_name = ' '.join(generated_name.split())  # Normalize whitespace
            
            # Ensure it's not too long
            if len(generated_name) > 200:
                generated_name = generated_name[:197] + "..."
            
            # Fallback if empty
            if not generated_name:
                generated_name = f"Agent {prompt[:50]}..." if len(prompt) > 50 else f"Agent {prompt}"
            
            return generated_name
            
        except Exception as e:
            print(f"Error generating agent name: {e}")
            # Fallback to a simple name based on prompt
            fallback_name = prompt[:50].strip() if len(prompt) > 50 else prompt.strip()
            if not fallback_name:
                fallback_name = "My Agent"
            return fallback_name
    
    def _generate_tools_for_agent(self, serializer, user):
        """
        Called on agent create/update.
        Populates the agent's 'tools' list with the "starter pack" of slugs
        from the hardcoded config file based on selected 'app_connections'.

        Validates that the user has connected each tool at the account level first.
        """
        app_connections = serializer.validated_data.get('app_connections', [])

        # If no app_connections provided, create agent with empty tools
        if not app_connections:
            serializer.save(
                user=user,
                tools=[],
                app_connections=[]
            )
            return

        # Auto-sync connections from Composio before validation
        # This ensures we have the latest connection status from Composio (ground truth)
        print(f"🔄 Auto-syncing connections from Composio before validation...")
        try:
            agent_service = AgentService(user)
            connection_details = agent_service.get_connection_details()

            # Update local database with fresh connection statuses
            entity_id = f"user_{user.id}"

            for conn_detail in connection_details:
                # Get existing connection to preserve auth_config_id
                existing_conn = ComposioConnection.objects.filter(
                    user=user,
                    tool_name=conn_detail['tool_name'].upper()
                ).first()

                # Skip if this connection was soft-deleted by user
                if existing_conn and existing_conn.deleted_at:
                    print(f"⏭️  Skipping soft-deleted connection: {conn_detail['tool_name']}")
                    continue

                defaults = {
                    'is_active': True,
                    'composio_connection_id': conn_detail.get('id', ''),
                    'composio_entity_id': entity_id,
                    'metadata': {'status': 'connected', 'synced_at': str(timezone.now())},
                    'deleted_at': None,
                }

                # Preserve auth_config_id from initial OAuth flow
                if existing_conn and existing_conn.auth_config_id:
                    defaults['auth_config_id'] = existing_conn.auth_config_id

                ComposioConnection.objects.update_or_create(
                    user=user,
                    tool_name=conn_detail['tool_name'].upper(),
                    defaults=defaults
                )

            print(f"✅ Synced {len(connection_details)} connections from Composio")

        except Exception as e:
            print(f"⚠️  Warning: Failed to sync connections from Composio: {e}")
            print(f"   Falling back to local database for validation")
            # Continue with validation using local DB data

        # Validate that each tool is connected at the account level
        # Get active connections (not soft-deleted)
        user_active_connections = ComposioConnection.objects.filter(
            user=user,
            is_active=True,
            deleted_at__isnull=True
        ).values_list('tool_name', flat=True)

        user_connected_tools = set(conn.upper() for conn in user_active_connections)

        # Check each requested app_connection
        not_connected = []
        for app_name in app_connections:
            app_name_upper = app_name.upper()
            if app_name_upper not in user_connected_tools:
                not_connected.append(app_name_upper)

        # If any tools are not connected at account level, raise validation error
        if not_connected:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({
                'app_connections': f"You must connect these tools in the integrations page first: {', '.join(not_connected)}. "
                                   f"Visit /integrations to connect them."
            })

        # All tools are connected, proceed with generating slugs
        agent_service = AgentService(user)
        hardcoded_tools = agent_service.TOP_SLUGS_BY_APP

        initial_tools = set()
        for app_name in app_connections:
            app_name_upper = app_name.upper()
            if app_name_upper in hardcoded_tools:
                for slug in hardcoded_tools[app_name_upper]:
                    initial_tools.add(slug)

        print(f"Generated {len(initial_tools)} hardcoded tools for agent with validated connections.")

        # Save the agent with this initial list of tools
        serializer.save(
            user=user,
            tools=list(initial_tools),
            app_connections=[app.upper() for app in app_connections]  # Normalize to uppercase
        )

    def _get_random_default_avatar(self):
        """
        Randomly selects a default avatar image from static/default_avatars/ folder.
        Returns tuple: (binary_data, filename, mime_type) or (None, None, None) if no images found.
        """
        import os
        import random
        import mimetypes
        from django.conf import settings

        # Path to default avatars folder
        default_avatars_path = os.path.join(settings.BASE_DIR, 'static', 'default_avatars')

        try:
            # Check if directory exists
            if not os.path.exists(default_avatars_path):
                print(f"⚠️  Default avatars directory not found: {default_avatars_path}")
                return None, None, None

            # List all image files in the directory
            image_extensions = ['.jpg', '.jpeg', '.png']
            available_images = [
                f for f in os.listdir(default_avatars_path)
                if os.path.isfile(os.path.join(default_avatars_path, f))
                and os.path.splitext(f.lower())[1] in image_extensions
            ]

            if not available_images:
                print(f"⚠️  No default avatar images found in {default_avatars_path}")
                return None, None, None

            # Randomly select an image
            selected_image = random.choice(available_images)
            image_path = os.path.join(default_avatars_path, selected_image)

            # Read the image file
            with open(image_path, 'rb') as f:
                image_data = f.read()

            # Detect MIME type
            mime_type, _ = mimetypes.guess_type(image_path)
            if not mime_type:
                mime_type = 'image/jpeg'  # Default fallback

            print(f"✅ Selected default avatar: {selected_image} ({mime_type})")
            return image_data, selected_image, mime_type

        except Exception as e:
            print(f"❌ Error loading default avatar: {e}")
            import traceback
            traceback.print_exc()
            return None, None, None

    def perform_create(self, serializer):
        """
        Called when a new agent is created (POST).
        Generates agent name from prompt if not provided.
        Handles avatar image processing if provided, or assigns random default avatar.
        """
        prompt = serializer.validated_data.get('prompt', '')
        name = serializer.validated_data.get('name', '').strip()

        # Generate name from prompt if not provided
        if not name:
            name = self._generate_agent_name(prompt)
            serializer.validated_data['name'] = name

        # Process avatar if provided, otherwise assign random default avatar
        avatar_file = serializer.validated_data.get('avatar')
        if avatar_file:
            # User uploaded custom avatar - process it
            processed_image_data = self._process_avatar_image(avatar_file)
            if processed_image_data:
                serializer.validated_data['avatar_image'] = processed_image_data
                serializer.validated_data['avatar_filename'] = avatar_file.name
                serializer.validated_data['avatar_mime_type'] = 'image/jpeg'
            # Remove the avatar field (it's write-only)
            serializer.validated_data.pop('avatar', None)
        else:
            # No avatar uploaded - assign random default avatar
            default_avatar_data, default_filename, default_mime = self._get_random_default_avatar()
            if default_avatar_data:
                serializer.validated_data['avatar_image'] = default_avatar_data
                serializer.validated_data['avatar_filename'] = default_filename
                serializer.validated_data['avatar_mime_type'] = default_mime
                print(f"✅ Assigned default avatar: {default_filename}")

        # Generate tools from app_connections (if any)
        self._generate_tools_for_agent(serializer, self.request.user)
        
    def perform_update(self, serializer):
        """
        Called when an agent is updated (PUT/PATCH).
        Handles avatar image processing if provided.
        """
        # Process avatar if provided
        avatar_file = serializer.validated_data.get('avatar')
        if avatar_file:
            processed_image_data = self._process_avatar_image(avatar_file)
            if processed_image_data:
                serializer.validated_data['avatar_image'] = processed_image_data
                serializer.validated_data['avatar_filename'] = avatar_file.name
                serializer.validated_data['avatar_mime_type'] = 'image/jpeg'
            # Remove the avatar field (it's write-only)
            serializer.validated_data.pop('avatar', None)

        self._generate_tools_for_agent(serializer, self.request.user)

    def _process_avatar_image(self, avatar_file) -> bytes:
        """
        Process and optimize avatar image.
        Converts to JPEG, resizes if needed, and returns binary data.
        """
        try:
            # Open and verify image
            image = Image.open(avatar_file)
            image.verify()

            # Re-open after verify (verify closes the file)
            avatar_file.seek(0)
            image = Image.open(avatar_file)

            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')

            # Resize if too large (max 800x800)
            max_dimension = 800
            if image.width > max_dimension or image.height > max_dimension:
                image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

            # Save to BytesIO
            output = BytesIO()
            image.save(output, format='JPEG', quality=85, optimize=True)
            return output.getvalue()

        except Exception as e:
            print(f"Error processing avatar image: {e}")
            return None
    
    @extend_schema(
        tags=['agents'],
        operation_id='agents_messages_retrieve',
        summary='Get agent chat messages',
        responses={
            200: OpenApiResponse(
                response=ChatMessageSerializer(many=True),
                description='List of chat messages for the agent. Messages are returned in chronological order (oldest first).'
            ),
            401: OpenApiResponse(description='Authentication required'),
            404: OpenApiResponse(description='Agent not found')
        },
        description='Retrieves all chat messages for a specific agent. Messages are returned in chronological order (oldest first). Each message includes the role (user/assistant), content, attachments, and timestamp.',
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='Agent UUID',
                required=True
            )
        ]
    )
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """
        Gets all chat messages for a specific agent.
        Returns messages in chronological order with all metadata including attachments.

        If this is the first time loading the chat (no messages exist), automatically
        generates and saves a greeting message from the agent.
        """
        agent = self.get_object()
        messages = ChatMessage.objects.filter(agent=agent)

        # If no messages exist, create a greeting message
        if messages.count() == 0:
            try:
                print(f"📝 No messages found for agent {agent.name} (ID={agent.id}). Generating greeting...")
                agent_service = AgentService(request.user)
                # ✅ generate_greeting_message is now async
                greeting_content = asyncio.run(agent_service.generate_greeting_message(agent))

                # Create the greeting message
                ChatMessage.objects.create(
                    agent=agent,
                    role='assistant',
                    content=greeting_content,
                    attachments=[]
                )
                print(f"✅ Greeting message created for agent {agent.name}")

                # Refresh query to include the new greeting
                messages = ChatMessage.objects.filter(agent=agent)

            except Exception as e:
                print(f"❌ Error generating greeting for agent {agent.name}: {e}")
                import traceback
                traceback.print_exc()
                # Fall through - return empty messages if greeting fails

        serializer = ChatMessageSerializer(messages, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        tags=['agents'],
        operation_id='agents_chat_create',
        summary='Chat with agent',
        request=AgentChatRequestSerializer,
        responses={
            200: OpenApiResponse(
                response=AgentChatResponseSerializer,
                description='Chat response with user and assistant messages'
            ),
            400: OpenApiResponse(description='Validation error (e.g., message is required)'),
            401: OpenApiResponse(description='Authentication required'),
            404: OpenApiResponse(description='Agent not found'),
            500: OpenApiResponse(description='Server error during chat execution')
        },
        description='Sends a message to the agent and receives a response. This is the core chat functionality. The agent dynamically selects tools based on the message content and chat history, then executes the appropriate actions. Supports file attachments via file_ids. The response includes both the user message and the assistant response, both saved to the database.',
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='Agent UUID',
                required=True
            )
        ]
    )
    @action(detail=True, methods=['post'])
    def chat(self, request, pk=None):
        """
        Handles sending a message to the agent and getting a streaming response via SSE.
        This is the core "chat" logic with real-time updates.

        Flow:
        1. Validates message is provided
        2. Processes file attachments (if any)
        3. Saves user message to database
        4. Builds chat history (last 6 messages)
        5. Dynamically selects tools based on prompt and history
        6. Executes chat with streaming callbacks
        7. Saves assistant response
        8. Returns SSE stream with real-time updates

        SSE Events:
        - status: Agent state updates (thinking, tool_calling, responding, complete)
        - tool_call_start: Tool execution started
        - tool_call_result: Tool execution completed
        - content_delta: Partial response text chunks
        - message_complete: Final saved message
        - done: Stream finished
        - error: Error occurred
        """
        agent = self.get_object()

        # Use serializer for proper validation
        serializer = AgentChatRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        message = serializer.validated_data['message']
        inline_files = serializer.validated_data.get('files', [])
        is_ephemeral = serializer.validated_data.get('is_ephemeral', False)

        # ===== AUTO-LOAD PERSISTENT FILES =====
        # Load all persistent files for this agent from database
        persistent_file_ids = list(
            FileAttachment.objects.filter(
                agent=agent,
                user=request.user,
                is_temporary=False
            ).values_list('id', flat=True)[:10]  # Limit to 10 files
        )
        print(f"📚 Auto-loaded {len(persistent_file_ids)} persistent file(s) from agent database")
        # ======================================

        # ===== PROCESS INLINE FILE UPLOADS =====
        # Handle inline file uploads - save as temporary files
        temp_file_ids = []
        for file_obj in inline_files:
            try:
                # Read and save inline file with is_temporary=True
                file_content = file_obj.read()
                attachment = FileAttachment.objects.create(
                    user=request.user,
                    agent=agent,
                    file_content=file_content,
                    original_filename=file_obj.name,
                    file_size=file_obj.size,
                    mime_type=file_obj.content_type or 'application/octet-stream',
                    is_temporary=True  # 👈 Automatically mark as temporary
                )
                temp_file_ids.append(attachment.id)
                print(f"📎 Inline file uploaded as temporary: {file_obj.name} (ID={attachment.id})")
            except Exception as e:
                print(f"❌ Error uploading inline file {file_obj.name}: {e}")
                # Continue with other files

        # Combine persistent file IDs (from DB) and temporary file IDs (inline uploads)
        file_ids = persistent_file_ids + temp_file_ids
        # =======================================

        # ===== CREDIT CHECK =====
        # Check if user has sufficient credits before processing (skip for ephemeral mode)
        user = request.user
        if not is_ephemeral and not user.has_credits(1):
            return Response(
                {
                    'error': 'Insufficient credits',
                    'detail': f'You need at least 1 credit to send a message. You have {user.total_credits} credit(s) remaining.',
                    'credits_required': 1,
                    'credits_remaining': user.total_credits
                },
                status=status.HTTP_402_PAYMENT_REQUIRED
            )
        # ========================

        # Define the streaming generator
        async def event_stream():
            try:
                # Emit initial status
                yield send_status_event('thinking', 'Analyzing your request...')

                # 1. Get full file info for *newly* attached files
                attachments = []
                if file_ids:
                    files = await sync_to_async(list)(FileAttachment.objects.filter(
                        id__in=file_ids,
                        user=request.user
                    ))
                    attachments = [{
                        'id': str(f.id),
                        'filename': f.original_filename,
                        'download_url': request.build_absolute_uri(f'/api/files/{f.id}/download/'),
                        'mime_type': f.mime_type,
                        'size': f.file_size
                    } for f in files]

                # 2. Save the new user message to the database (only if not ephemeral)
                user_msg = None
                if not is_ephemeral:
                    user_msg = await sync_to_async(ChatMessage.objects.create)(
                        agent=agent,
                        role='user',
                        content=message,
                        attachments=attachments  # Save the rich attachment data
                    )


                # 3. Build the rich chat history (for agent memory)
                # For ephemeral mode: use empty history (stateless)
                # For persistent mode: use last 6 messages from database
                chat_history_formatted = []

                if not is_ephemeral:
                    print("Building rich chat history from database...")
                    chat_history_qs = ChatMessage.objects.filter(agent=agent).order_by('-created_at')[:6]
                    chat_history = await sync_to_async(list)(chat_history_qs)
                    chat_history.reverse()  # Put in chronological order (oldest first)

                    for msg in chat_history:
                        msg_content = msg.content

                        # Re-build the file context for *all* messages in history
                        # Support vision for images, text metadata for non-images
                        if msg.attachments and isinstance(msg.attachments, list):
                            content_parts = [{"type": "text", "text": msg_content}]
                            non_image_files = []

                            for att in msg.attachments:
                                mime_type = att.get('mime_type', '')

                                # Handle images with vision
                                if mime_type.startswith('image/'):
                                    try:
                                        # Get FileAttachment from database
                                        file_id = att.get('id')
                                        if file_id:
                                            file_obj = await sync_to_async(FileAttachment.objects.get)(id=file_id)
                                            image_url = convert_image_to_base64(file_obj)

                                            if image_url:
                                                content_parts.append({
                                                    "type": "image_url",
                                                    "image_url": {"url": image_url}
                                                })
                                                print(f"📷 Added image to vision: {att.get('filename', 'image')}")
                                            else:
                                                non_image_files.append(att)
                                        else:
                                            non_image_files.append(att)
                                    except Exception as e:
                                        print(f"❌ Error loading image {att.get('filename')}: {e}")
                                        non_image_files.append(att)
                                else:
                                    # Non-image files
                                    non_image_files.append(att)

                            # Add non-image files as text context
                            if non_image_files:
                                file_context = "\n\nAttached files:\n"
                                for att in non_image_files:
                                    file_context += f"- {att.get('filename', 'file.unknown')}\n"
                                    if att.get('download_url'):
                                        file_context += f"  Download URL: {att.get('download_url')}\n"
                                    elif att.get('file_path'):
                                        file_context += f"  File path: {att.get('file_path')}\n"
                                content_parts[0]["text"] += file_context

                            chat_history_formatted.append({
                                "role": msg.role,
                                "content": content_parts if len(content_parts) > 1 else msg_content
                            })
                        else:
                            chat_history_formatted.append({
                                "role": msg.role,
                                "content": msg_content
                            })
                else:
                    print("Ephemeral mode: Using empty history (stateless session)")

                # 4. Initialize the agent service
                agent_service = AgentService(request.user)

                # 5. Dynamically select tools (with history and file attachment info)
                print(f"Dynamically selecting tools for prompt: '{message[:50]}...'")
                # ✅ select_tools_for_prompt is now async, no need for sync_to_async wrapper
                specific_tools_slugs = await agent_service.select_tools_for_prompt(
                    user_prompt=message,
                    app_names=agent.app_connections,
                    chat_history=chat_history_formatted,  # Pass rich history
                    has_file_attachments=bool(file_ids)  # Indicate if files are attached
                )


                # 6. Execute the chat with streaming callbacks
                # Determine which tools are available and route to appropriate handler
                has_composio_tools = bool(specific_tools_slugs and agent_service.composio_client)
                has_agent_tools = bool(agent.agent_tools)

                # Create async queue for real-time event streaming
                event_queue = asyncio.Queue()
                response_container = {'response': ''}

                # Define callback for streaming events - yields immediately
                async def stream_callback(event_type, data):
                    event_str = None
                    if event_type == 'status':
                        event_str = send_status_event(data['status'], data.get('message', ''))
                    elif event_type == 'tool_call_start':
                        event_str = send_tool_call_start_event(data['tool'], data['parameters'])
                    elif event_type == 'tool_call_result':
                        event_str = send_tool_call_result_event(
                            data['tool'],
                            data['success'],
                            data.get('result'),
                            data.get('error')
                        )
                    elif event_type == 'content_delta':
                        event_str = send_content_delta_event(data['content'], data.get('index', 0))
                    elif event_type == 'heartbeat':
                        event_str = format_sse_event('heartbeat', data)
                    elif event_type == 'error':
                        event_str = send_error_event(data.get('error', 'Unknown error'))

                    if event_str:
                        await event_queue.put(event_str)

                # === WRITE FILES TO DISK FOR COMPOSIO ===
                # If there are file attachments, write them to a temporary directory for Composio to access
                import tempfile
                import os
                temp_file_paths = []  # Track disk file paths for cleanup
                file_attachments_for_composio = []

                if file_ids:
                    temp_dir = tempfile.mkdtemp(prefix='composio_files_')
                    print(f"📁 Writing {len(file_ids)} file(s) to temporary directory: {temp_dir}")

                    for file_id in file_ids:
                        try:
                            # Get file from database
                            file_obj = await sync_to_async(FileAttachment.objects.get)(
                                id=file_id,
                                user=request.user
                            )

                            # Write file content to disk
                            file_path = os.path.join(temp_dir, file_obj.original_filename)
                            file_content = file_obj.get_file_content()

                            if file_content:
                                await sync_to_async(lambda: open(file_path, 'wb').write(file_content))()
                                temp_file_paths.append(file_path)

                                # Add to file_attachments list for Composio
                                file_attachments_for_composio.append({
                                    'filename': file_obj.original_filename,
                                    'file_path': file_path,
                                    'size': file_obj.file_size,
                                    'mime_type': file_obj.mime_type
                                })
                                print(f"📄 Wrote file to disk: {file_path}")
                        except Exception as e:
                            print(f"❌ Error writing file {file_id} to disk: {e}")
                # ==========================================

                # Execute chat in background task
                async def run_chat():
                    try:
                        print("🚀 Starting chat execution in background task...")
                        if has_composio_tools and has_agent_tools:
                            # Agent has both Composio and agent tools
                            print(f"Executing chat with mixed tools: {len(specific_tools_slugs)} Composio + {len(agent.agent_tools)} agent tools")
                            response = await agent_service._chat_with_mixed_tools(
                                agent_model=agent,
                                message=message,
                                composio_tool_slugs=specific_tools_slugs,
                                chat_history=chat_history_formatted,
                                callback=stream_callback
                            )
                        elif has_composio_tools:
                            # Only Composio tools
                            print(f"Executing chat with {len(specific_tools_slugs)} Composio tools")
                            response = await agent_service._chat_with_composio(
                                agent_model=agent,
                                message=message,
                                specific_tools_slugs=specific_tools_slugs,
                                chat_history=chat_history_formatted,
                                callback=stream_callback,
                                file_attachments=file_attachments_for_composio if file_attachments_for_composio else None
                            )
                        elif has_agent_tools:
                            # Only agent tools
                            print(f"Executing chat with {len(agent.agent_tools)} agent tools")
                            response = await agent_service._chat_with_agent_tools(
                                agent_model=agent,
                                message=message,
                                chat_history=chat_history_formatted,
                                callback=stream_callback
                            )
                        else:
                            # No tools needed. Fallback to basic chat.
                            print("No tools available. Falling back to basic chat.")
                            response = await agent_service._chat_without_tools(
                                agent_model=agent,
                                message=message,
                                chat_history=chat_history_formatted,
                                callback=stream_callback
                            )

                        print(f"✅ Chat execution completed. Response length: {len(response)}")
                        response_container['response'] = response
                    except Exception as e:
                        print(f"❌ Error in run_chat: {e}")
                        import traceback
                        traceback.print_exc()
                        # Send error event
                        error_event = send_error_event(str(e))
                        await event_queue.put(error_event)
                    finally:
                        # Signal completion by putting None
                        print("🏁 Signaling chat completion")
                        await event_queue.put(None)

                # Start chat execution in background
                chat_task = asyncio.create_task(run_chat())

                # Yield events as they arrive in real-time
                while True:
                    event = await event_queue.get()
                    if event is None:
                        # Chat completed
                        break
                    yield event

                # Wait for chat task to complete
                await chat_task
                response = response_container['response']

                # 7. Save assistant message (only if not ephemeral)
                assistant_msg = None
                if not is_ephemeral:
                    assistant_msg = await sync_to_async(ChatMessage.objects.create)(
                        agent=agent,
                        role='assistant',
                        content=response
                    )

                # ===== DEDUCT CREDITS =====
                # Deduct credits for the message and log usage (only if not ephemeral)
                if not is_ephemeral:
                    from .credits import deduct_credits_for_message
                    await sync_to_async(deduct_credits_for_message)(
                        user=request.user,
                        agent=agent,
                        message_content=message
                    )
                # ==========================

                # Emit message complete event
                if assistant_msg:
                    yield send_message_complete_event(
                        str(assistant_msg.id),
                        response,
                        assistant_msg.created_at.isoformat()
                    )
                else:
                    # For ephemeral mode, send message complete without ID/timestamp
                    yield send_message_complete_event(
                        None,
                        response,
                        None
                    )

                # ===== CLEANUP TEMPORARY DISK FILES FOR COMPOSIO =====
                # Delete the files we wrote to disk for Composio (but keep database records)
                if temp_file_paths:
                    import shutil
                    for file_path in temp_file_paths:
                        try:
                            if os.path.exists(file_path):
                                os.remove(file_path)
                        except Exception as e:
                            print(f"⚠️ Failed to delete temp file {file_path}: {e}")

                    # Clean up the temp directory
                    try:
                        if file_attachments_for_composio:
                            temp_dir = os.path.dirname(temp_file_paths[0])
                            if os.path.exists(temp_dir):
                                shutil.rmtree(temp_dir)
                                print(f"🗑️ Cleaned up temporary disk directory: {temp_dir}")
                    except Exception as e:
                        print(f"⚠️ Failed to delete temp directory: {e}")
                # =====================================================

                # ===== CLEANUP TEMPORARY DATABASE FILES =====
                # Delete any temporary files from database (inline uploads)
                if file_ids:
                    deleted_count = await sync_to_async(
                        lambda: FileAttachment.objects.filter(
                            id__in=file_ids,
                            user=request.user,
                            is_temporary=True
                        ).delete()[0]
                    )()
                    if deleted_count > 0:
                        print(f"🗑️ Cleaned up {deleted_count} temporary database file(s) after message completion")
                # ============================================

                # Emit done event
                yield send_done_event()

            except Exception as e:
                traceback.print_exc()

                # Cleanup temporary disk files even on error
                if temp_file_paths:
                    import shutil
                    for file_path in temp_file_paths:
                        try:
                            if os.path.exists(file_path):
                                os.remove(file_path)
                        except Exception as cleanup_error:
                            print(f"⚠️ Failed to delete temp file {file_path}: {cleanup_error}")

                    # Clean up the temp directory
                    try:
                        if file_attachments_for_composio:
                            temp_dir = os.path.dirname(temp_file_paths[0])
                            if os.path.exists(temp_dir):
                                shutil.rmtree(temp_dir)
                    except Exception as cleanup_error:
                        print(f"⚠️ Failed to delete temp directory: {cleanup_error}")

                # Cleanup temporary database files even on error
                if file_ids:
                    try:
                        deleted_count = await sync_to_async(
                            lambda: FileAttachment.objects.filter(
                                id__in=file_ids,
                                user=request.user,
                                is_temporary=True
                            ).delete()[0]
                        )()
                        if deleted_count > 0:
                            print(f"🗑️ Cleaned up {deleted_count} temporary database file(s) after error")
                    except Exception as cleanup_error:
                        print(f"⚠️ Failed to cleanup temporary database files: {cleanup_error}")

                yield send_error_event(str(e))
                yield send_done_event()

        # Convert async generator to sync for Django
        def sync_event_stream():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                async_gen = event_stream()
                while True:
                    try:
                        event = loop.run_until_complete(async_gen.__anext__())
                        yield event
                    except StopAsyncIteration:
                        break
            finally:
                loop.close()

        # Return SSE streaming response
        response = StreamingHttpResponse(
            sync_event_stream(),
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response

    @extend_schema(
        tags=['agents'],
        operation_id='agents_reset_chat',
        summary='Reset agent chat history',
        request=None,  # No request body needed
        description=(
            'Resets the chat history for a specific agent. This endpoint performs a complete reset:\n\n'
            '**Effects:**\n'
            '1. Deletes all conversation history (ChatMessage records)\n'
            '2. Clears all stored memories and context\n'
            '3. Removes all previous message context\n'
            '4. Starts fresh with no conversation history\n\n'
            '**Use case:** Call this when the user wants to start a new conversation from scratch, '
            'clearing all previous interactions and context. This is useful for privacy, testing, '
            'or when the conversation becomes too long or off-track.\n\n'
            '**Note:** This action is irreversible. All chat messages for this agent will be permanently deleted.'
        ),
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='Agent UUID',
                required=True
            )
        ],
        responses={
            200: OpenApiResponse(
                description='Chat history reset successfully',
                examples=[
                    OpenApiExample(
                        'Reset Success',
                        value={
                            'success': True,
                            'message': 'Chat history has been reset. All messages deleted.',
                            'deleted_count': 42
                        },
                        response_only=True,
                        status_codes=['200']
                    )
                ]
            ),
            401: OpenApiResponse(description='Authentication required'),
            404: OpenApiResponse(description='Agent not found or not owned by user')
        }
    )
    @action(detail=True, methods=['post'], url_path='reset-chat')
    def reset_chat(self, request, pk=None):
        """
        Resets the chat history for the agent.
        Deletes all ChatMessage records associated with this agent.
        """
        try:
            agent = self.get_object()

            # Delete all chat messages for this agent
            deleted_count, _ = ChatMessage.objects.filter(agent=agent).delete()

            print(f"✅ Chat history reset for agent {agent.name} (ID={agent.id}). Deleted {deleted_count} messages.")

            return Response({
                'success': True,
                'message': 'Chat history has been reset. All messages deleted.',
                'deleted_count': deleted_count
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"❌ Error resetting chat history: {e}")
            traceback.print_exc()
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        tags=['agents'],
        operation_id='agents_suggested_prompts',
        summary='Generate suggested prompts for agent',
        description=(
            'Generates 3 ready-to-use example prompts based on the agent\'s purpose and available tools. '
            '**No authentication required for this endpoint.** '
            '\n\n'
            'This endpoint is useful when creating a new agent - it provides the frontend with '
            'suggested example prompts that users can click to quickly interact with their agent.'
            '\n\n'
            'For example, if creating an email assistant with Gmail, it might suggest:\n'
            '- "Check my latest emails"\n'
            '- "Send an email to..."\n'
            '- "Delete specific emails"'
        ),
        request=SuggestedPromptsRequestSerializer,
        responses={
            200: OpenApiResponse(
                response=SuggestedPromptsResponseSerializer,
                description='Successfully generated suggested prompts'
            ),
            400: OpenApiResponse(description='Invalid request data'),
            500: OpenApiResponse(description='Internal server error')
        }
    )
    @action(detail=False, methods=['post'], url_path='suggested-prompts', permission_classes=[AllowAny])
    def suggested_prompts(self, request):
        """
        Generates suggested prompts based on agent purpose and tools.
        This endpoint doesn't require authentication and can be called during agent creation.
        """
        serializer = SuggestedPromptsRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        prompt = serializer.validated_data['prompt']
        app_connections = serializer.validated_data.get('app_connections', [])

        try:
            # Use OpenAI to generate contextual suggested prompts
            openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

            # Build tools context
            tools_context = ""
            if app_connections:
                tools_list = ", ".join(app_connections)
                tools_context = f"\n\nThe agent has access to these tools: {tools_list}"

            system_prompt = (
                "You are an expert at generating example prompts for AI agents. "
                "Based on the agent's purpose and available tools, generate exactly 3 short, "
                "actionable example prompts that a user could send to this agent."
                "\n\n"
                "Requirements:\n"
                "1. Each prompt should be 3-8 words\n"
                "2. Prompts should be realistic use cases\n"
                "3. Prompts should leverage the available tools if specified\n"
                "4. Make them conversational and natural\n"
                "5. Return ONLY a JSON object with a 'prompts' array containing 3 strings\n"
                "6. Do not add numbering or bullet points - just the prompt text"
            )

            user_prompt = (
                f"Agent purpose: {prompt}"
                f"{tools_context}"
                "\n\n"
                "Generate 3 example prompts."
            )

            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Using gpt-4o-mini as fallback - gpt-4o-mini may not be available yet
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_completion_tokens=200,
                response_format={"type": "json_object"}
            )

            response_content = response.choices[0].message.content
            print(f"Generated suggested prompts: {response_content}")
            print(f"Response object: {response}")

            # Check if response is empty
            if not response_content or not response_content.strip():
                print("⚠️ Empty response from GPT-5 nano, using fallback prompts")
                suggested_prompts = []
            else:
                # Parse the JSON response
                import json
                try:
                    data = json.loads(response_content)
                    suggested_prompts = data.get('prompts', [])
                except json.JSONDecodeError as e:
                    print(f"⚠️ JSON decode error: {e}, using fallback prompts")
                    suggested_prompts = []

            # Ensure we have exactly 3 prompts
            if len(suggested_prompts) < 3:
                # Fallback prompts based on agent purpose
                fallback_prompts = [
                    "Help me get started",
                    "What can you do?",
                    "Show me an example"
                ]
                suggested_prompts.extend(fallback_prompts[:(3 - len(suggested_prompts))])
            elif len(suggested_prompts) > 3:
                suggested_prompts = suggested_prompts[:3]

            return Response({
                'suggested_prompts': suggested_prompts
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Error generating suggested prompts: {e}")
            traceback.print_exc()

            # Return generic fallback prompts
            fallback_prompts = [
                "Help me get started",
                "What can you do?",
                "Show me an example"
            ]

            return Response({
                'suggested_prompts': fallback_prompts
            }, status=status.HTTP_200_OK)

    @extend_schema(
        tags=['agents'],
        operation_id='agents_agent_tools_list',
        summary='Get all available agent-specific tools',
        description=(
            'Returns list of all agent-specific tools (weather, calculator, etc.) '
            'that can be added to agents. **No authentication required.** '
            '\n\n'
            'These are different from Composio connection tools. Agent tools:\n'
            '- Don\'t require external OAuth connections\n'
            '- Are managed entirely by the backend\n'
            '- Users can simply enable/disable them for each agent\n'
            '\n\n'
            'Available tools: weather (Open-Meteo), calculator, yahoo_finance, youtube, web_search, website_reader'
        ),
        responses={
            200: OpenApiResponse(
                response=AgentToolsResponseSerializer,
                description='List of agent tools with metadata'
            )
        }
    )
    @action(detail=False, methods=['get'], url_path='agent-tools', permission_classes=[AllowAny])
    def agent_tools_list(self, request):
        """
        Get list of all available agent-specific tools.
        No authentication required - this is public information.
        """
        tools = []
        for tool_name, tool_config in AGENT_TOOLS.items():
            tools.append({
                'tool_name': tool_name,
                'name': tool_config['name'],
                'description': tool_config['description'],
                'icon': tool_config['icon'],
                'category': tool_config['category'],
                'is_enabled': False  # Default, will be set per-agent in other endpoint
            })

        return Response({
            'tools': tools,
            'count': len(tools)
        }, status=status.HTTP_200_OK)

    @extend_schema(
        tags=['agents'],
        operation_id='agents_available_agent_tools',
        summary='Get agent tools with enabled status for specific agent',
        description=(
            'Returns all agent-specific tools with their enabled/disabled status for this agent. '
            '**Authentication required.** '
            '\n\n'
            'Shows which tools are currently enabled in agent.agent_tools list.'
        ),
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='Agent UUID',
                required=True
            )
        ],
        responses={
            200: OpenApiResponse(
                response=AgentToolsResponseSerializer,
                description='Agent tools with enabled status'
            ),
            404: OpenApiResponse(description='Agent not found or not owned by user')
        }
    )
    @action(detail=True, methods=['get'], url_path='available-agent-tools')
    def available_agent_tools(self, request, pk=None):
        """
        Get agent tools with enabled status for a specific agent.
        """
        agent = self.get_object()
        enabled_tools = set(agent.agent_tools or [])

        tools = []
        for tool_name, tool_config in AGENT_TOOLS.items():
            tools.append({
                'tool_name': tool_name,
                'name': tool_config['name'],
                'description': tool_config['description'],
                'icon': tool_config['icon'],
                'category': tool_config['category'],
                'is_enabled': tool_name in enabled_tools
            })

        return Response({
            'tools': tools,
            'count': len(tools)
        }, status=status.HTTP_200_OK)

    @extend_schema(
        tags=['agents'],
        operation_id='agents_add_agent_tool',
        summary='Add/enable an agent tool for this agent',
        description=(
            'Enables a specific agent tool for this agent. '
            '**Authentication required.** '
            '\n\n'
            'Adds the tool name to agent.agent_tools list if not already present.'
        ),
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='Agent UUID',
                required=True
            )
        ],
        request=AddAgentToolRequestSerializer,
        responses={
            200: OpenApiResponse(
                response=AddAgentToolResponseSerializer,
                description='Tool added successfully'
            ),
            400: OpenApiResponse(description='Invalid tool name or tool already enabled'),
            404: OpenApiResponse(description='Agent not found or not owned by user')
        }
    )
    @action(detail=True, methods=['post'], url_path='add-agent-tool')
    def add_agent_tool(self, request, pk=None):
        """
        Add/enable an agent tool for this agent.
        """
        serializer = AddAgentToolRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        tool_name = serializer.validated_data['tool_name']

        # Validate tool exists
        if not is_valid_tool(tool_name):
            return Response({
                'success': False,
                'message': f'Invalid tool name: {tool_name}. Available tools: {", ".join(get_all_tool_names())}'
            }, status=status.HTTP_400_BAD_REQUEST)

        agent = self.get_object()

        # Check if already enabled
        if tool_name in (agent.agent_tools or []):
            return Response({
                'success': False,
                'message': f'Tool "{tool_name}" is already enabled for this agent',
                'agent_tools': agent.agent_tools
            }, status=status.HTTP_400_BAD_REQUEST)

        # Add tool to list
        if not agent.agent_tools:
            agent.agent_tools = []
        agent.agent_tools.append(tool_name)
        agent.save()

        print(f"✅ Added agent tool '{tool_name}' to agent {agent.name} (ID: {agent.id})")

        return Response({
            'success': True,
            'message': f'Tool "{tool_name}" enabled successfully',
            'agent_tools': agent.agent_tools
        }, status=status.HTTP_200_OK)

    @extend_schema(
        tags=['agents'],
        operation_id='agents_remove_agent_tool',
        summary='Remove/disable an agent tool from this agent',
        description=(
            'Disables a specific agent tool for this agent. '
            '**Authentication required.** '
            '\n\n'
            'Removes the tool name from agent.agent_tools list.'
        ),
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='Agent UUID',
                required=True
            ),
            OpenApiParameter(
                name='tool_name',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description='Tool name to remove (e.g., "weather", "calculator")',
                required=True
            )
        ],
        responses={
            200: OpenApiResponse(
                response=AddAgentToolResponseSerializer,
                description='Tool removed successfully'
            ),
            400: OpenApiResponse(description='Tool not enabled or invalid tool name'),
            404: OpenApiResponse(description='Agent not found or not owned by user')
        }
    )
    @action(detail=True, methods=['delete'], url_path='remove-agent-tool/(?P<tool_name>[^/.]+)')
    def remove_agent_tool(self, request, pk=None, tool_name=None):
        """
        Remove/disable an agent tool from this agent.
        """
        if not tool_name:
            return Response({
                'success': False,
                'message': 'Tool name is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate tool exists
        if not is_valid_tool(tool_name):
            return Response({
                'success': False,
                'message': f'Invalid tool name: {tool_name}'
            }, status=status.HTTP_400_BAD_REQUEST)

        agent = self.get_object()

        # Check if tool is enabled
        if not agent.agent_tools or tool_name not in agent.agent_tools:
            return Response({
                'success': False,
                'message': f'Tool "{tool_name}" is not enabled for this agent',
                'agent_tools': agent.agent_tools or []
            }, status=status.HTTP_400_BAD_REQUEST)

        # Remove tool from list
        agent.agent_tools.remove(tool_name)
        agent.save()

        print(f"✅ Removed agent tool '{tool_name}' from agent {agent.name} (ID: {agent.id})")

        return Response({
            'success': True,
            'message': f'Tool "{tool_name}" disabled successfully',
            'agent_tools': agent.agent_tools
        }, status=status.HTTP_200_OK)

    @extend_schema(
        tags=['agents'],
        operation_id='agents_create_manual',
        summary='Create agent in Manual Mode',
        description=(
            'Creates a new agent with full manual configuration. '
            '**Authentication required.** '
            '\n\n'
            'This endpoint is for Manual Mode agent creation, where the user provides:\n'
            '- Name (required)\n'
            '- Prompt (required)\n'
            '- Avatar (optional)\n'
            '- App connections (optional - list of app slugs like GMAIL, SLACK)\n'
            '- Agent tools (optional - list of tool names like weather, calculator)\n'
            '- Files (optional - list of files to attach for persistent context)\n'
            '\n\n'
            '**Note:** Use multipart/form-data for file uploads.'
        ),
        request=ManualAgentCreateSerializer,
        responses={
            201: ManualAgentCreateResponseSerializer,
            400: OpenApiResponse(description='Invalid input or validation error'),
            401: OpenApiResponse(description='Authentication required')
        },
        examples=[
            OpenApiExample(
                'Success Response',
                value={
                    'agent': {
                        'id': '3fa85f64-5717-4562-b3fc-2c963f66afa6',
                        'name': 'Email Assistant',
                        'prompt': 'You are a helpful email assistant',
                        'app_connections': ['GMAIL'],
                        'agent_tools': ['weather'],
                        'tools': ['GMAIL_SEND_EMAIL', 'GMAIL_FETCH_EMAILS'],
                        'created_at': '2025-11-27T10:00:00Z'
                    },
                    'message': 'Agent created successfully',
                    'files_attached': 2
                },
                response_only=True,
                status_codes=['201']
            )
        ]
    )
    @action(detail=False, methods=['post'], url_path='create-manual')
    def create_manual(self, request):
        """
        Create agent in Manual Mode with full manual configuration.
        """
        serializer = ManualAgentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            validated_data = serializer.validated_data

            # Extract data
            name = validated_data['name']
            prompt = validated_data['prompt']
            avatar = validated_data.get('avatar')
            app_connections = validated_data.get('app_connections', [])
            agent_tools = validated_data.get('agent_tools', [])
            files = validated_data.get('files', [])

            # Validate agent tools
            invalid_tools = [tool for tool in agent_tools if not is_valid_tool(tool)]
            if invalid_tools:
                return Response({
                    'error': f'Invalid agent tools: {", ".join(invalid_tools)}. Available: {", ".join(get_all_tool_names())}'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Process avatar
            avatar_data = None
            avatar_filename = None
            avatar_mime = 'image/jpeg'

            if avatar:
                avatar_data = self._process_avatar_image(avatar)
                avatar_filename = avatar.name
            else:
                # Assign random default avatar
                avatar_data, avatar_filename, avatar_mime = self._get_random_default_avatar()

            # Create the agent
            agent = Agent.objects.create(
                user=request.user,
                name=name,
                prompt=prompt,
                avatar_image=avatar_data,
                avatar_filename=avatar_filename,
                avatar_mime_type=avatar_mime,
                app_connections=app_connections,
                agent_tools=agent_tools,
                tools=[]  # Will be populated by _sync_agent_tools
            )

            # Sync tools from app_connections
            self._sync_agent_tools(agent, app_connections)

            # Handle file attachments
            files_count = 0
            if files:
                for file in files:
                    # Read file content
                    file_content = file.read()

                    # Create file attachment
                    FileAttachment.objects.create(
                        user=request.user,
                        agent=agent,
                        file_content=file_content,
                        original_filename=file.name,
                        file_size=file.size,
                        mime_type=file.content_type or 'application/octet-stream',
                        is_temporary=False  # Persistent files
                    )
                    files_count += 1
                    print(f"📎 Attached file: {file.name} ({file.size} bytes) to agent {agent.name}")

            # Serialize response
            agent_serializer = AgentSerializer(agent)

            return Response({
                'agent': agent_serializer.data,
                'message': 'Agent created successfully',
                'files_attached': files_count
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            traceback.print_exc()
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _sync_agent_tools(self, agent, app_connections):
        """
        Syncs agent tools from app_connections.
        Updates the agent's 'tools' field with action slugs from composio_config.
        """
        if not app_connections:
            agent.tools = []
            agent.save()
            return

        # Auto-sync connections from Composio
        agent_service = AgentService(agent.user)
        connection_details = agent_service.get_connection_details()
        connected_apps = {conn['tool_name'] for conn in connection_details}

        # Validate connections
        missing_connections = [app for app in app_connections if app not in connected_apps]
        if missing_connections:
            print(f"⚠️  Warning: Missing connections: {missing_connections}")

        # Get action slugs from config
        all_slugs = []
        for app in app_connections:
            if app in TOP_SLUGS_BY_APP:
                all_slugs.extend(TOP_SLUGS_BY_APP[app])

        agent.tools = all_slugs
        agent.save()
        print(f"✅ Synced {len(all_slugs)} tool slugs for agent {agent.name}")

    @extend_schema(
        tags=['agents'],
        operation_id='agents_available_tools',
        summary='Get available tools for agent with connection status',
        description=(
            'Returns all available tools with their connection status for a specific agent. '
            '**Authentication required.** '
            '\n\n'
            'This endpoint shows which tools are:\n'
            '1. Connected at the **account level** (via /api/connections/)\n'
            '2. Enabled for **this specific agent** (in agent.app_connections)\n'
            '\n\n'
            '**Use case:** Call this when user visits agent configuration page to show which tools '
            'can be enabled/disabled for this agent. Only tools connected at account level can be '
            'enabled for agents.'
        ),
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='Agent UUID',
                required=True
            )
        ],
        responses={
            200: OpenApiResponse(
                response=AgentAvailableToolsResponseSerializer,
                description='List of all available tools with connection status',
                examples=[
                    OpenApiExample(
                        'Agent Available Tools',
                        value={
                            'tools': [
                                {
                                    'tool_name': 'GMAIL',
                                    'name': 'Gmail',
                                    'description': 'Send, receive, and manage emails',
                                    'category': 'communication',
                                    'is_connected_to_account': True,
                                    'is_connected_to_agent': True,
                                    'connection_id': 42
                                },
                                {
                                    'tool_name': 'SLACK',
                                    'name': 'Slack',
                                    'description': 'Send messages and manage workspace',
                                    'category': 'messaging',
                                    'is_connected_to_account': True,
                                    'is_connected_to_agent': False,
                                    'connection_id': 87
                                },
                                {
                                    'tool_name': 'NOTION',
                                    'name': 'Notion',
                                    'description': 'Create pages and databases',
                                    'category': 'productivity',
                                    'is_connected_to_account': False,
                                    'is_connected_to_agent': False,
                                    'connection_id': None
                                }
                            ],
                            'count': 18
                        },
                        response_only=True,
                        status_codes=['200']
                    )
                ]
            ),
            401: OpenApiResponse(description='Authentication required'),
            404: OpenApiResponse(description='Agent not found'),
            500: OpenApiResponse(description='Server error')
        }
    )
    @action(detail=True, methods=['get'])
    def available_tools(self, request, pk=None):
        """
        Returns list of all available tools with connection status for this agent.
        Shows which tools are connected at account level and enabled for this agent.
        """
        try:
            agent = self.get_object()

            # Get account-level connections (active and not soft-deleted)
            user_connections = ComposioConnection.objects.filter(
                user=request.user,
                is_active=True,
                deleted_at__isnull=True
            )
            # Map: tool_name -> connection_id
            account_connections_map = {conn.tool_name: conn.id for conn in user_connections}

            # Get agent's connected tools
            agent_tools = set(tool.upper() for tool in (agent.app_connections or []))

            # Build tools list
            tools_list = []
            for app_key in sorted(APP_SLUGS.keys()):
                tool_info = {
                    "tool_name": app_key,
                    "is_connected_to_account": app_key in account_connections_map,
                    "is_connected_to_agent": app_key in agent_tools,
                    "connection_id": account_connections_map.get(app_key, None)
                }

                # Add metadata if available
                if app_key in APP_METADATA:
                    tool_info.update({
                        "name": APP_METADATA[app_key]["name"],
                        "description": APP_METADATA[app_key]["description"],
                        "category": APP_METADATA[app_key]["category"]
                    })
                else:
                    tool_info.update({
                        "name": app_key,
                        "description": f"Integration with {app_key}",
                        "category": "other"
                    })

                tools_list.append(tool_info)

            return Response({
                'tools': tools_list,
                'count': len(tools_list)
            })

        except Exception as e:
            traceback.print_exc()
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



@extend_schema_view(
    list=extend_schema(
        tags=['files'],
        operation_id='files_list',
        summary='List all files',
        description='Returns list of all file attachments owned by the authenticated user. Files are stored in the database as binary data. Files are ordered by upload date (newest first). Users can only see their own files. Each file includes a download_url to retrieve the binary content and agent_name showing which agent it belongs to. Can be filtered by agent_id query parameter to get files for a specific agent.',
        parameters=[
            OpenApiParameter(
                name='agent_id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                description='Filter files by agent (optional)',
                required=False
            )
        ],
        responses={
            200: OpenApiResponse(
                response=FileAttachmentSerializer(many=True),
                description='List of file attachments',
                examples=[
                    OpenApiExample(
                        'Files List Response',
                        value=[
                            {
                                'id': '550e8400-e29b-41d4-a716-446655440000',
                                'agent_id': '3fa85f64-5717-4562-b3fc-2c963f66afa6',
                                'agent_name': 'Email Assistant',
                                'original_filename': 'document.pdf',
                                'file_size': 1024,
                                'mime_type': 'application/pdf',
                                'uploaded_at': '2024-01-01T00:00:00Z',
                                'download_url': 'http://localhost:8000/api/files/550e8400-e29b-41d4-a716-446655440000/download/'
                            },
                            {
                                'id': '550e8400-e29b-41d4-a716-446655440001',
                                'agent_id': '3fa85f64-5717-4562-b3fc-2c963f66afa6',
                                'agent_name': 'Email Assistant',
                                'original_filename': 'image.jpg',
                                'file_size': 2048,
                                'mime_type': 'image/jpeg',
                                'uploaded_at': '2024-01-01T01:00:00Z',
                                'download_url': 'http://localhost:8000/api/files/550e8400-e29b-41d4-a716-446655440001/download/'
                            }
                        ],
                        response_only=True,
                        status_codes=['200']
                    )
                ]
            ),
            401: OpenApiResponse(description='Authentication required')
        }
    ),
    create=extend_schema(
        tags=['files'],
        operation_id='files_create',
        summary='Upload a file',
        description='Uploads a new file attachment using `multipart/form-data`. **Important:** `agent_id` (UUID) is required - files must be associated with a specific agent. The file content is stored in the database as binary data (not on the filesystem). Original filename, file size, and MIME type are automatically detected. The user is automatically set from the authentication token. Files can be attached to agent chat messages using the returned file ID. Use the `download_url` to retrieve the file content. **Request format:** `multipart/form-data` with a `file` field (binary file data) and `agent_id` field (UUID string).',
        responses={
            201: OpenApiResponse(
                response=FileAttachmentSerializer,
                description='File uploaded successfully',
                examples=[
                    OpenApiExample(
                        'File Upload Success',
                        value={
                            'id': '550e8400-e29b-41d4-a716-446655440000',
                            'agent_id': '3fa85f64-5717-4562-b3fc-2c963f66afa6',
                            'agent_name': 'Email Assistant',
                            'original_filename': 'document.pdf',
                            'file_size': 1024,
                            'mime_type': 'application/pdf',
                            'uploaded_at': '2024-01-01T00:00:00Z',
                            'download_url': 'http://localhost:8000/api/files/550e8400-e29b-41d4-a716-446655440000/download/'
                        },
                        response_only=True,
                        status_codes=['201']
                    )
                ]
            ),
            400: OpenApiResponse(
                description='No file provided, no agent_id provided, agent not found, or validation error',
                examples=[
                    OpenApiExample(
                        'No File Error',
                        value={'error': 'No file provided'},
                        response_only=True,
                        status_codes=['400']
                    ),
                    OpenApiExample(
                        'No Agent ID Error',
                        value={'error': 'agent_id is required'},
                        response_only=True,
                        status_codes=['400']
                    ),
                    OpenApiExample(
                        'Agent Not Found Error',
                        value={'error': 'Agent not found or does not belong to you'},
                        response_only=True,
                        status_codes=['400']
                    )
                ]
            ),
            401: OpenApiResponse(description='Authentication required'),
            500: OpenApiResponse(
                description='Server error during upload',
                examples=[
                    OpenApiExample(
                        'Server Error',
                        value={'error': 'Internal server error'},
                        response_only=True,
                        status_codes=['500']
                    )
                ]
            )
        }
    ),
    retrieve=extend_schema(
        tags=['files'],
        operation_id='files_retrieve',
        summary='Get file details',
        description='Returns detailed information about a specific file attachment stored in the database. Users can only retrieve their own files. The response includes metadata and a download_url to retrieve the binary file content.',
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='File attachment UUID',
                required=True
            )
        ],
        responses={
            200: OpenApiResponse(
                response=FileAttachmentSerializer,
                description='File details',
                examples=[
                    OpenApiExample(
                        'File Details',
                        value={
                            'id': '550e8400-e29b-41d4-a716-446655440000',
                            'agent_id': '3fa85f64-5717-4562-b3fc-2c963f66afa6',
                            'agent_name': 'Email Assistant',
                            'original_filename': 'document.pdf',
                            'file_size': 1024,
                            'mime_type': 'application/pdf',
                            'uploaded_at': '2024-01-01T00:00:00Z',
                            'download_url': 'http://localhost:8000/api/files/550e8400-e29b-41d4-a716-446655440000/download/'
                        },
                        response_only=True,
                        status_codes=['200']
                    )
                ]
            ),
            401: OpenApiResponse(description='Authentication required'),
            404: OpenApiResponse(
                description='File not found or not owned by user',
                examples=[
                    OpenApiExample(
                        'Not Found',
                        value={'detail': 'Not found.'},
                        response_only=True,
                        status_codes=['404']
                    )
                ]
            )
        }
    ),
    update=extend_schema(
        tags=['files'],
        operation_id='files_update',
        summary='Update file (full)',
        description='Fully updates a file attachment. Note: This endpoint is typically not used as file metadata is usually immutable after upload.',
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='File attachment UUID',
                required=True
            )
        ],
        responses={
            200: OpenApiResponse(response=FileAttachmentSerializer, description='File updated'),
            400: OpenApiResponse(description='Validation error'),
            401: OpenApiResponse(description='Authentication required'),
            404: OpenApiResponse(description='File not found')
        }
    ),
    partial_update=extend_schema(
        tags=['files'],
        operation_id='files_partial_update',
        summary='Update file (partial)',
        description='Partially updates a file attachment. Note: This endpoint is typically not used as file metadata is usually immutable after upload.',
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='File attachment UUID',
                required=True
            )
        ],
        responses={
            200: OpenApiResponse(response=FileAttachmentSerializer, description='File updated'),
            400: OpenApiResponse(description='Validation error'),
            401: OpenApiResponse(description='Authentication required'),
            404: OpenApiResponse(description='File not found')
        }
    ),
    destroy=extend_schema(
        tags=['files'],
        operation_id='files_destroy',
        summary='Delete file',
        description='Deletes a file attachment from the database. Users can only delete their own files. The file record and binary content are permanently removed from the database. No filesystem cleanup is needed since files are stored in the database.',
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='File attachment UUID',
                required=True
            )
        ],
        responses={
            204: OpenApiResponse(description='File deleted successfully (no content)'),
            401: OpenApiResponse(description='Authentication required'),
            404: OpenApiResponse(
                description='File not found or not owned by user',
                examples=[
                    OpenApiExample(
                        'Not Found',
                        value={'detail': 'Not found.'},
                        response_only=True,
                        status_codes=['404']
                    )
                ]
            )
        }
    )
)


class AgentTemplateViewSet(viewsets.GenericViewSet,
                               viewsets.mixins.ListModelMixin,
                               viewsets.mixins.RetrieveModelMixin):
    """
    API endpoint for browsing agent templates.

    Features:
    - Lists all active templates
    - Read-only (no create/update/delete for users)
    - Public access (no authentication required)
    - Templates can be instantiated via /api/agents/instantiate-template/
    """
    serializer_class = AgentTemplateSerializer
    permission_classes = [AllowAny]  # Public endpoint
    queryset = AgentTemplate.objects.filter(is_active=True)

    @extend_schema(
        tags=['agent-templates'],
        operation_id='agent_templates_list',
        summary='List all active agent templates grouped by category',
        description=(
            'Returns all active agent templates grouped by category. '
            'Authentication not required - this is a public endpoint.'
            '\n\n'
            'Response structure:\n'
            '```json\n'
            '{\n'
            '  "research": [\n'
            '    { "id": "uuid", "name": "Research Assistant", ... },\n'
            '    { "id": "uuid", "name": "Data Analyst", ... },\n'
            '    { "id": "uuid", "name": "Market Research", ... }\n'
            '  ],\n'
            '  "project_mgmt": [ ... ],\n'
            '  "developer": [ ... ],\n'
            '  ...\n'
            '}\n'
            '```'
        ),
        responses={
            200: OpenApiResponse(
                description='Templates grouped by category'
            )
        }
    )
    def list(self, request, *args, **kwargs):
        """List all active agent templates grouped by category"""
        queryset = self.get_queryset()

        # Group templates by category
        grouped_templates = {}
        for template in queryset:
            category = template.category
            if category not in grouped_templates:
                grouped_templates[category] = []

            serializer = self.get_serializer(template)
            grouped_templates[category].append(serializer.data)

        return Response(grouped_templates)

    @extend_schema(
        tags=['agent-templates'],
        operation_id='agent_templates_retrieve',
        summary='Get a specific agent template',
        description='Returns detailed information about a specific agent template. Authentication not required.',
        responses={
            200: OpenApiResponse(
                response=AgentTemplateSerializer,
                description='Agent template details'
            ),
            404: OpenApiResponse(description='Template not found')
        }
    )
    def retrieve(self, request, *args, **kwargs):
        """Get a specific agent template"""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        tags=['agent-templates'],
        operation_id='agent_templates_instantiate',
        summary='Instantiate an agent from a template',
        request=InstantiateTemplateRequestSerializer,
        responses={
            201: OpenApiResponse(
                response=InstantiateTemplateResponseSerializer,
                description='Agent created successfully from template'
            ),
            400: OpenApiResponse(description='Validation error (e.g., missing required connections, invalid template)'),
            401: OpenApiResponse(description='Authentication required'),
            404: OpenApiResponse(description='Template not found')
        },
        description=(
            'Creates a new agent from a template for the authenticated user. '
            'The agent is created with the template\'s system prompt, default tools, and default agent tools. '
            '\n\n'
            'Response includes:\n'
            '- The newly created agent\n'
            '- A success message\n'
            '- List of missing_connections: tools that are configured but not yet connected at account level\n'
            '\n\n'
            'After receiving the response, the frontend should:\n'
            '1. If missing_connections is empty: Navigate to agent chat\n'
            '2. If missing_connections exists: Navigate to agent configuration page to set up connections'
        )
    )
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def instantiate_template(self, request):
        """
        Instantiate an agent from a template.
        Creates a new agent with template configuration.
        """
        serializer = InstantiateTemplateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        template_id = serializer.validated_data['template_id']

        try:
            template = AgentTemplate.objects.get(id=template_id, is_active=True)
        except AgentTemplate.DoesNotExist:
            return Response(
                {'error': 'Template not found or is not active'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check which connections are missing at account level
        user_connections = ComposioConnection.objects.filter(
            user=request.user,
            is_active=True,
            deleted_at__isnull=True
        ).values_list('tool_name', flat=True)

        missing_connections = [
            tool for tool in template.default_tools
            if tool not in user_connections
        ]

        # Create the agent with template configuration
        agent = Agent.objects.create(
            user=request.user,
            name=template.name,
            prompt=template.system_prompt,
            app_connections=template.default_tools,
            agent_tools=template.default_agent_tools,
            tools=[]  # Will be populated by the agent service
        )

        # Increment usage count
        template.usage_count += 1
        template.save(update_fields=['usage_count'])

        # Serialize the response
        agent_serializer = AgentSerializer(agent, context={'request': request})

        return Response({
            'agent': agent_serializer.data,
            'message': f'Agent "{agent.name}" created successfully from template',
            'missing_connections': missing_connections
        }, status=status.HTTP_201_CREATED)


class FileAttachmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for uploading and managing file attachments.

    Features:
    - Users can upload files of any type
    - Files are stored in the database as binary data (not on filesystem)
    - Original filename, size, and MIME type are automatically detected
    - Files can be attached to agent chat messages
    - Files can be downloaded via the download endpoint
    - All operations are scoped to the authenticated user
    """
    serializer_class = FileAttachmentSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    http_method_names = ['get', 'post', 'delete']  # Exclude PUT and PATCH
    
    def get_queryset(self):
        """
        Ensures users can only see their own files.
        Optionally filter by agent_id query parameter.
        """
        queryset = FileAttachment.objects.filter(user=self.request.user)

        # Filter by agent if agent_id is provided
        agent_id = self.request.query_params.get('agent_id')
        if agent_id:
            queryset = queryset.filter(agent_id=agent_id)

        return queryset
    
    def create(self, request, *args, **kwargs):
        """
        Handles file uploads - stores file content in database.
        Requires agent_id in request data.
        """
        try:
            print(f"📤 File upload attempt by user: {request.user.username}")
            print(f"📋 Request FILES: {request.FILES}")
            print(f"📋 Request data: {request.data}")

            # Validate agent_id is provided
            agent_id = request.data.get('agent_id')
            if not agent_id:
                print("❌ No agent_id provided in request")
                return Response(
                    {'error': 'agent_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate agent exists and belongs to user
            try:
                agent = Agent.objects.get(id=agent_id, user=request.user)
                print(f"✅ Agent validated: {agent.name} (ID={agent.id})")
            except Agent.DoesNotExist:
                print(f"❌ Agent not found or doesn't belong to user: {agent_id}")
                return Response(
                    {'error': 'Agent not found or does not belong to you'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            file = request.FILES.get('file')
            if not file:
                print("❌ No file provided in request")
                return Response(
                    {'error': 'No file provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            print(f"📎 File received: {file.name}, size: {file.size}, type: {file.content_type}")

            # Get is_temporary flag from request (default: False)
            is_temporary = request.data.get('is_temporary', 'false').lower() in ['true', '1', 'yes']

            # ===== CHECK FILE LIMIT =====
            # Only check limit for persistent files (not temporary)
            if not is_temporary:
                current_file_count = FileAttachment.objects.filter(
                    agent=agent,
                    user=request.user,
                    is_temporary=False
                ).count()

                if current_file_count >= 10:
                    print(f"❌ File limit reached: {current_file_count}/10 files")
                    return Response(
                        {
                            'error': 'File limit reached',
                            'detail': f'You can only upload up to 10 persistent files per agent. Current count: {current_file_count}. Please delete some files before uploading new ones.'
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
            # ============================

            # Read file content into memory
            file_content = file.read()

            # Store in database with agent relationship
            attachment = FileAttachment.objects.create(
                user=request.user,
                agent=agent,
                file_content=file_content,
                original_filename=file.name,
                file_size=file.size,
                mime_type=file.content_type or 'application/octet-stream',
                is_temporary=is_temporary
            )

            temp_status = " (TEMPORARY)" if is_temporary else ""
            print(f"✅ File uploaded successfully{temp_status}: ID={attachment.id}, Agent={agent.name}, Size={file.size} bytes")

            serializer = self.get_serializer(attachment)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            print(f"❌ File upload error: {e}")
            traceback.print_exc()
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        tags=['files'],
        operation_id='files_download',
        summary='Download file content',
        description='Retrieves the binary file content from the database. Returns the file with appropriate Content-Type header based on the stored MIME type.',
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='File attachment UUID',
                required=True
            )
        ],
        responses={
            200: OpenApiResponse(
                description='File content (binary). Returns the file with appropriate Content-Type header based on the stored MIME type.'
            ),
            401: OpenApiResponse(description='Authentication required'),
            404: OpenApiResponse(description='File not found or not owned by user')
        }
    )
    @action(detail=True, methods=['get'], url_path='download')
    def download(self, request, pk=None):
        """
        Downloads the file content from the database.
        """
        file_attachment = self.get_object()
        
        try:
            file_content = file_attachment.get_file_content()
            if not file_content:
                return Response(
                    {'error': 'File content not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            from django.http import HttpResponse
            response = HttpResponse(file_content, content_type=file_attachment.mime_type)
            response['Content-Disposition'] = f'attachment; filename="{file_attachment.original_filename}"'
            response['Content-Length'] = str(file_attachment.file_size)
            return response
            
        except Exception as e:
            print(f"❌ File download error: {e}")
            traceback.print_exc()
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@extend_schema_view(
    list=extend_schema(
        tags=['connections'],
        description='Composio connections API. Security & scoping: All endpoints require authentication (IsAuthenticated). The request is authenticated via your configured auth (e.g., JWT in HttpOnly cookies). DRF authenticators verify the token, load the user, and set request.user. Every query is scoped with get_queryset() to request.user, so users can only list/retrieve/delete their own connections.',
    ),
    retrieve=extend_schema(
        tags=['connections'],
        description='Composio connections API. Security & scoping: All endpoints require authentication (IsAuthenticated). The request is authenticated via your configured auth (e.g., JWT in HttpOnly cookies). DRF authenticators verify the token, load the user, and set request.user. Every query is scoped with get_queryset() to request.user, so users can only list/retrieve/delete their own connections. The {id} path param refers to the local primary key of the ComposioConnection row (not the external Composio connection id).',
        parameters=[
            OpenApiParameter(name='id', type=OpenApiTypes.INT, location='path', description='Connection ID (integer)')
        ]
    ),
    destroy=extend_schema(
        tags=['connections'],
        description='Composio connections API. Security & scoping: All endpoints require authentication (IsAuthenticated). The request is authenticated via your configured auth (e.g., JWT in HttpOnly cookies). DRF authenticators verify the token, load the user, and set request.user. Every query is scoped with get_queryset() to request.user, so users can only list/retrieve/delete their own connections. The {id} path param refers to the local primary key of the ComposioConnection row (not the external Composio connection id).',
        parameters=[
            OpenApiParameter(name='id', type=OpenApiTypes.INT, location='path', description='Connection ID (integer)')
        ]
    ),
)
class ComposioConnectionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Composio tool connections.
    """
    serializer_class = ComposioConnectionSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'delete']
    
    def get_queryset(self):
        """
        Ensures users can only see their own active connections.
        Excludes pending_auth (OAuth not completed) and soft-deleted connections.
        """
        return ComposioConnection.objects.filter(
            user=self.request.user,
            is_active=True,
            deleted_at__isnull=True
        )
    
    def perform_create(self, serializer):
        """
        Associates the connection with the current user.
        """
        serializer.save(user=self.request.user)
    
    @extend_schema(
        operation_id='connections_create',
        request=ConnectionCreateRequestSerializer,
        responses={
            201: OpenApiResponse(response=ConnectionAuthResponseSerializer, description='Created and initialized auth flow'),
            200: OpenApiResponse(response=ConnectionAuthResponseSerializer, description='Updated existing pending connection and returned auth URL'),
            400: OpenApiResponse(description='Validation or Composio error'),
            401: OpenApiResponse(description='Authentication credentials were not provided or are invalid'),
            500: OpenApiResponse(description='Unexpected server error'),
        },
        description='Starts Composio auth and upserts a local connection. **Authentication required.** Flow: (1) Authenticates user (returns 401 if not authenticated). (2) Reads tool_name from body (WhatsApp may include waba_id, phone_number_id). (3) Calls AgentService.authenticate_tool(tool_name, ...), which contacts Composio and returns auth_url and auth_config_id. (4) Upserts a local ComposioConnection for request.user with is_active=False and metadata.status="pending_auth". (5) Returns { success, auth_url, connection }. Security: Authentication enforced via IsAuthenticated permission. User context is always derived from the verified token, never from request body. Status codes: 201 if a new local record was created, 200 if an existing record was updated.'
    )
    def create(self, request, *args, **kwargs):
        """
        Starts the Composio auth flow and upserts a local connection record.
        Returns the auth_url and the local connection.
        """
        tool_name = request.data.get('tool_name')

        print(f"🔌 Connection request received")
        print(f"   Tool name (raw): {tool_name}")
        print(f"   Request data: {request.data}")

        if not tool_name:
            return Response(
                {'error': 'tool_name is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Normalize tool name: remove spaces and convert to uppercase
        # "Google Calendar" -> "GOOGLECALENDAR"
        # "Gmail" -> "GMAIL"
        tool_name = str(tool_name).replace(' ', '').upper()
        print(f"   Tool name (normalized): {tool_name}")

        try:
            additional_fields = {}
            
            # Special handling for WhatsApp optional fields
            if str(tool_name).upper() == 'WHATSAPP':
                waba_id = request.data.get('waba_id')
                phone_number_id = request.data.get('phone_number_id')
                
                if waba_id: additional_fields['waba_id'] = waba_id
                if phone_number_id: additional_fields['phone_number_id'] = phone_number_id
            
            agent_service = AgentService(request.user)
            result = agent_service.authenticate_tool(
                tool_name, 
                additional_fields if additional_fields else None
            )
            
            if result.get('success'):
                metadata = {}
                if additional_fields:
                    metadata['additional_fields'] = additional_fields
                
                # Save or update the local connection as pending until OAuth completes
                connection, created = ComposioConnection.objects.update_or_create(
                    user=request.user,
                    tool_name=str(tool_name).upper(),
                    defaults={
                        'is_active': False,
                        'auth_config_id': result.get('auth_config_id', ''),
                        'deleted_at': None,  # Clear soft-delete flag on reconnection
                        'metadata': {
                            **metadata,
                            'status': 'pending_auth'
                        }
                    }
                )
                
                resp_data = {
                    'success': True,
                    'auth_url': result.get('auth_url'),
                    'connection': ComposioConnectionSerializer(connection).data
                }
                return Response(resp_data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
            else:
                # Log the full error for debugging
                print(f"❌ Connection failed for {tool_name}")
                print(f"   Error details: {result}")
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            traceback.print_exc()
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        operation_id='connections_destroy',
        parameters=[
            OpenApiParameter(
                name='id',
                type=int,
                location=OpenApiParameter.PATH,
                description='The database ID of the connection to delete. **Important:** You can only delete connections that belong to your authenticated account. The system automatically filters by user - attempting to delete another user\'s connection will return 404 (not found) even if that ID exists.',
                required=True
            )
        ],
        responses={
            200: OpenApiResponse(response=DisconnectResponseSerializer, description='Disconnected from Composio and deleted local record'),
            401: OpenApiResponse(description='Authentication credentials were not provided or are invalid'),
            404: OpenApiResponse(description='Connection not found or not owned by user'),
            500: OpenApiResponse(description='Unexpected server error'),
        },
        description='Disconnects a tool connection. **Authentication required.** Flow: (1) Authenticates user (returns 401 if not authenticated). (2) Looks up the connection by {id} - only returns connections owned by authenticated user (returns 404 if not found or not owned). (3) Disconnects from Composio using AgentService.disconnect_tool(). (4) Deletes the entire local database record (all fields). Security: Authentication is enforced via IsAuthenticated permission class. User scope filtering is enforced via get_queryset() - users can only delete their own connections. The {id} parameter must be from your own connections list (GET /api/connections/).'
    )
    def destroy(self, request, *args, **kwargs):
        """
        Disconnects from Composio and soft-deletes the local connection record.
        Authentication is required and users can only delete their own connections.

        Uses soft delete (sets deleted_at timestamp) to prevent immediate recreation
        by the available_tools sync endpoint if Composio API has a delay.
        """
        # get_object() automatically filters by user via get_queryset() and returns 404 if not found/not owned
        instance = self.get_object()
        tool_name = instance.tool_name
        connection_id = instance.id

        try:
            # Attempt to disconnect from Composio
            agent_service = AgentService(request.user)
            composio_result = agent_service.disconnect_tool(tool_name)

            # Soft delete: mark as deleted and inactive instead of hard deleting
            # This prevents available_tools from immediately recreating it if Composio sync has a delay
            instance.deleted_at = timezone.now()
            instance.is_active = False
            instance.save()

            return Response({
                'success': True,
                'message': f"Connection {connection_id} for {tool_name} has been disconnected",
                'composio_disconnect': composio_result
            }, status=status.HTTP_200_OK)

        except Exception as e:
            traceback.print_exc()
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        tags=['connections'],
        operation_id='connections_available_tools',
        summary='Get available tools with connection status',
        description=(
            'Returns all available tools that can be connected with their metadata and connection status. '
            '**Authentication required.** This endpoint automatically syncs connections from Composio API '
            '(ground truth) and returns the current connection status for each tool. '
            '\n\n'
            '**Behavior:**\n'
            '1. Fetches active connections from Composio API\n'
            '2. Updates local database with ground truth\n'
            '3. Preserves auth_config_id from initial OAuth flow\n'
            '4. Marks connections no longer in Composio as inactive\n'
            '5. Returns all available tools with is_active status and connection_id\n'
            '\n'
            '**Response fields:**\n'
            '- `is_active`: Boolean indicating if the tool is currently connected\n'
            '- `connection_id`: Database ID of the connection (null if not connected). Use this ID to delete the connection via DELETE /api/connections/{id}/\n'
            '\n'
            '**Side effects:** Writes to database (updates connection status)\n'
            '\n'
            '**Use case:** Call this endpoint when user visits the integrations page to display '
            'all available tools with real-time connection status. This replaces the need to call '
            'check_connections separately.'
        ),
        parameters=[],
        responses={
            200: OpenApiResponse(
                response=AvailableToolsResponseSerializer,
                description='List of all available tools with metadata and connection status',
                examples=[
                    OpenApiExample(
                        'Available Tools with Connection Status',
                        value={
                            'tools': [
                                {
                                    'tool_name': 'GMAIL',
                                    'name': 'Gmail',
                                    'description': 'Send, receive, and manage emails with Gmail integration',
                                    'category': 'communication',
                                    'is_active': True,
                                    'connection_id': 42
                                },
                                {
                                    'tool_name': 'GOOGLEDRIVE',
                                    'name': 'Google Drive',
                                    'description': 'Upload, download, and manage files in Google Drive',
                                    'category': 'productivity',
                                    'is_active': False,
                                    'connection_id': None
                                },
                                {
                                    'tool_name': 'SLACK',
                                    'name': 'Slack',
                                    'description': 'Send messages and manage Slack workspace communications',
                                    'category': 'messaging',
                                    'is_active': True,
                                    'connection_id': 87
                                },
                                {
                                    'tool_name': 'TWITTER',
                                    'name': 'Twitter',
                                    'description': 'Post tweets, manage followers, and interact on Twitter',
                                    'category': 'social',
                                    'is_active': False,
                                    'connection_id': None
                                }
                            ],
                            'count': 18
                        },
                        response_only=True,
                        status_codes=['200']
                    )
                ]
            ),
            401: OpenApiResponse(description='Authentication credentials not provided or invalid'),
            500: OpenApiResponse(description='Unexpected server error')
        }
    )
    @action(detail=False, methods=['get'])
    def available_tools(self, request):
        """
        Returns the list of available tools with metadata from composio_config.py.
        Each tool object contains name, description, category, and connection status.

        Automatically syncs connections from Composio and returns is_active status.
        Authentication required.
        """
        try:
            # Sync connections from Composio (check_connections logic)
            user_connections = {}
            try:
                # Call check_connections logic internally
                agent_service = AgentService(request.user)
                connection_details = agent_service.get_connection_details()

                # Update database with ground truth from Composio
                entity_id = f"user_{request.user.id}"

                for conn_detail in connection_details:
                    # Get existing connection to preserve auth_config_id
                    existing_conn = ComposioConnection.objects.filter(
                        user=request.user,
                        tool_name=conn_detail['tool_name'].upper()
                    ).first()

                    # Skip if this connection was soft-deleted by user
                    # Don't recreate connections the user explicitly disconnected
                    if existing_conn and existing_conn.deleted_at:
                        print(f"⏭️  Skipping soft-deleted connection: {conn_detail['tool_name']}")
                        continue

                    defaults = {
                        'is_active': True,
                        'composio_connection_id': conn_detail.get('connection_id', ''),
                        'composio_entity_id': conn_detail.get('entity_id', entity_id),
                        'deleted_at': None,
                    }

                    # Preserve auth_config_id and clear pending_auth status
                    if existing_conn and existing_conn.auth_config_id:
                        defaults['auth_config_id'] = existing_conn.auth_config_id

                    # Update metadata to mark as connected
                    if existing_conn and existing_conn.metadata:
                        metadata = existing_conn.metadata.copy()
                        metadata['status'] = 'connected'
                        defaults['metadata'] = metadata
                    else:
                        defaults['metadata'] = {'status': 'connected'}

                    ComposioConnection.objects.update_or_create(
                        user=request.user,
                        tool_name=conn_detail['tool_name'].upper(),
                        defaults=defaults
                    )

                connected_tool_names = [c['tool_name'].upper() for c in connection_details]

                # Mark tools no longer in Composio as inactive
                ComposioConnection.objects.filter(
                    user=request.user
                ).exclude(
                    tool_name__in=connected_tool_names
                ).update(is_active=False)

                # Cleanup: Hard delete soft-deleted connections older than 24 hours
                # This keeps the database clean while preventing immediate recreation
                old_deleted_threshold = timezone.now() - timezone.timedelta(hours=24)
                deleted_count = ComposioConnection.objects.filter(
                    user=request.user,
                    deleted_at__isnull=False,
                    deleted_at__lt=old_deleted_threshold
                ).delete()[0]
                if deleted_count > 0:
                    print(f"🗑️  Cleaned up {deleted_count} old soft-deleted connection(s)")

                # Build a map of tool_name -> connection info (is_active, connection_id)
                # Exclude soft-deleted connections from the active list
                connections = ComposioConnection.objects.filter(
                    user=request.user,
                    is_active=True,
                    deleted_at__isnull=True
                )
                user_connections = {conn.tool_name: {'is_active': True, 'connection_id': conn.id} for conn in connections}

            except Exception as e:
                # If connection sync fails, log it but continue with tool list
                traceback.print_exc()
                print(f"Failed to sync connections: {str(e)}")

            # Build tools list with connection status
            tools_list = []
            for app_key in sorted(APP_SLUGS.keys()):
                connection_info = user_connections.get(app_key, {'is_active': False, 'connection_id': None})
                tool_info = {
                    "tool_name": app_key,
                    "is_active": connection_info['is_active'],
                    "connection_id": connection_info['connection_id']
                }

                if app_key in APP_METADATA:
                    tool_info.update({
                        "name": APP_METADATA[app_key]["name"],
                        "description": APP_METADATA[app_key]["description"],
                        "category": APP_METADATA[app_key]["category"]
                    })
                else:
                    # Fallback for apps not in metadata
                    tool_info.update({
                        "name": app_key,
                        "description": f"Integration with {app_key}",
                        "category": "other"
                    })

                tools_list.append(tool_info)

            return Response({
                'tools': tools_list,
                'count': len(tools_list)
            })
        except Exception as e:
            traceback.print_exc()
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        tags=['connections'],
        operation_id='connections_tool_slugs',
        summary='Get tool slugs for a specific tool',
        description=(
            'Returns the list of action slugs available for a specific tool. '
            '**Authentication required.** '
            '\n\n'
            'This endpoint retrieves the predefined list of tool slugs (actions) that are available '
            'for a given tool from the composio_config.py configuration. '
            '\n\n'
            '**Parameters:**\n'
            '- `tool_name` (query parameter): The name of the tool (e.g., "GMAIL", "GOOGLEDRIVE")\n'
            '\n'
            '**Returns:**\n'
            '- List of action slugs for the specified tool\n'
            '- Tool name that was queried\n'
            '- Count of slugs returned'
        ),
        parameters=[
            OpenApiParameter(
                name='tool_name',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='The name of the tool to get slugs for (e.g., GMAIL, GOOGLEDRIVE)',
                required=True
            )
        ],
        responses={
            200: OpenApiResponse(
                description='List of tool slugs',
                examples=[
                    OpenApiExample(
                        'Gmail Tool Slugs',
                        value={
                            'tool_name': 'GMAIL',
                            'slugs': [
                                'GMAIL_FETCH_EMAILS',
                                'GMAIL_GET_MESSAGE_BY_MESSAGE_ID',
                                'GMAIL_CREATE_EMAIL_DRAFT',
                                'GMAIL_SEND_EMAIL'
                            ],
                            'count': 4
                        },
                        response_only=True,
                        status_codes=['200']
                    )
                ]
            ),
            400: OpenApiResponse(description='Tool name not provided or tool not found'),
            401: OpenApiResponse(description='Authentication credentials not provided or invalid'),
            500: OpenApiResponse(description='Unexpected server error')
        }
    )
    @action(detail=False, methods=['get'])
    def tool_slugs(self, request):
        """
        Returns the list of action slugs for a specific tool.
        Authentication required.
        """
        try:
            tool_name = request.query_params.get('tool_name')

            if not tool_name:
                return Response(
                    {'error': 'tool_name query parameter is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Normalize tool name to uppercase
            tool_name = tool_name.upper()

            # Check if tool exists in our configuration
            if tool_name not in TOP_SLUGS_BY_APP:
                return Response(
                    {'error': f'Tool "{tool_name}" not found. Available tools: {", ".join(sorted(TOP_SLUGS_BY_APP.keys()))}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get the slugs for this tool
            slugs = TOP_SLUGS_BY_APP[tool_name]

            return Response({
                'tool_name': tool_name,
                'slugs': slugs,
                'count': len(slugs)
            })

        except Exception as e:
            traceback.print_exc()
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        tags=['connections'],
        operation_id='connections_for_display',
        summary='Get all available tools for display',
        description=(
            'Returns a list of all available tools (agent tools + Composio apps) with their metadata '
            'and connection status. **Authentication required.** '
            '\n\n'
            'This endpoint combines two types of tools:\n'
            '1. **Agent Tools**: Built-in tools like Weather, Calculator, Yahoo Finance (always available)\n'
            '2. **Composio Apps**: External integrations like Gmail, Slack, GitHub (require OAuth connection)\n'
            '\n\n'
            'Use the `is_composio_app` flag to distinguish between the two types.'
            '\n\n'
            '**Returns:**\n'
            '- List of all available tools with:\n'
            '  - `app_slug`: Tool identifier (e.g., "weather", "GMAIL", "calculator")\n'
            '  - `name`: Display name (e.g., "Weather", "Gmail")\n'
            '  - `description`: What the tool does\n'
            '  - `category`: Category (e.g., "email", "productivity", "information")\n'
            '  - `icon`: Emoji icon (only for agent tools, null for Composio apps)\n'
            '  - `is_connected`: Connection status (always true for agent tools)\n'
            '  - `is_composio_app`: Boolean flag (false = agent tool, true = Composio app)\n'
            '  - `requires_api_key`: Whether the agent tool needs an API key (only relevant for agent tools)'
        ),
        responses={
            200: AppConnectionDisplaySerializer(many=True),
            401: OpenApiResponse(description='Authentication credentials not provided or invalid'),
            500: OpenApiResponse(description='Unexpected server error')
        },
        examples=[
            OpenApiExample(
                'Success Response',
                value=[
                    {
                        'app_slug': 'weather',
                        'name': 'Weather',
                        'description': 'Get current weather and forecasts for any location worldwide',
                        'category': 'information',
                        'icon': '🌤️',
                        'is_connected': True,
                        'is_composio_app': False,
                        'requires_api_key': False
                    },
                    {
                        'app_slug': 'calculator',
                        'name': 'Calculator',
                        'description': 'Perform mathematical calculations and evaluate expressions',
                        'category': 'utility',
                        'icon': '🧮',
                        'is_connected': True,
                        'is_composio_app': False,
                        'requires_api_key': False
                    },
                    {
                        'app_slug': 'GMAIL',
                        'name': 'Gmail',
                        'description': 'Gmail integration',
                        'category': 'email',
                        'icon': None,
                        'is_connected': True,
                        'is_composio_app': True,
                        'requires_api_key': False
                    },
                    {
                        'app_slug': 'SLACK',
                        'name': 'Slack',
                        'description': 'Slack integration',
                        'category': 'communication',
                        'icon': None,
                        'is_connected': False,
                        'is_composio_app': True,
                        'requires_api_key': False
                    }
                ],
                response_only=True,
                status_codes=['200']
            )
        ]
    )
    @action(detail=False, methods=['get'])
    def connections_for_display(self, request):
        """
        Returns all available tools (Composio apps + agent tools) for display.
        Used for displaying available connections in Manual Mode agent creation.
        """
        try:
            # Get user's active connections from Composio
            agent_service = AgentService(request.user)
            user_connections = agent_service.get_connection_details()

            # Create a set of connected app names for quick lookup
            connected_apps = {conn['tool_name'] for conn in user_connections}

            result = []

            # 1. Add agent tools first (they're always available, no connection needed)
            for tool_slug, tool_config in AGENT_TOOLS.items():
                result.append({
                    'app_slug': tool_slug,
                    'name': tool_config['name'],
                    'description': tool_config['description'],
                    'category': tool_config.get('category', 'utility'),
                    'icon': tool_config.get('icon', '🛠️'),
                    'is_connected': True,  # Agent tools are always "connected"
                    'is_composio_app': False,
                    'requires_api_key': tool_config.get('requires_api_key', False)
                })

            # 2. Add Composio apps
            for app_slug in sorted(APP_SLUGS.keys()):
                # Get metadata from APP_METADATA, or use defaults
                metadata = APP_METADATA.get(app_slug, {
                    'name': app_slug.title(),
                    'description': f'{app_slug} integration',
                    'category': 'other'
                })

                result.append({
                    'app_slug': app_slug,
                    'name': metadata['name'],
                    'description': metadata['description'],
                    'category': metadata['category'],
                    'icon': None,  # Composio apps don't have icons in metadata
                    'is_connected': app_slug in connected_apps,
                    'is_composio_app': True,
                    'requires_api_key': False  # Composio handles auth via OAuth
                })

            return Response(result)

        except Exception as e:
            traceback.print_exc()
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(exclude=True)  # Hide from Swagger UI - internal use only
    @action(detail=False, methods=['get'])
    def check_connections(self, request):
        """
        Syncs connection status from Composio to the local database.
        """
        try:
            agent_service = AgentService(request.user)
            
            # Get the ground truth from Composio
            connection_details = agent_service.get_connection_details()
            
            # Update our database to reflect the ground truth
            entity_id = f"user_{request.user.id}"

            for conn_detail in connection_details:
                # Get existing connection to preserve auth_config_id if it exists
                existing_conn = ComposioConnection.objects.filter(
                    user=request.user,
                    tool_name=conn_detail['tool_name'].upper()
                ).first()

                # Skip if this connection was soft-deleted by user
                # Don't recreate connections the user explicitly disconnected
                if existing_conn and existing_conn.deleted_at:
                    print(f"⏭️  Skipping soft-deleted connection: {conn_detail['tool_name']}")
                    continue

                defaults = {
                    'is_active': True,
                    'composio_connection_id': conn_detail.get('connection_id', ''),
                    'composio_entity_id': conn_detail.get('entity_id', entity_id),
                    'deleted_at': None,
                }

                # Preserve auth_config_id and clear pending_auth status
                if existing_conn and existing_conn.auth_config_id:
                    defaults['auth_config_id'] = existing_conn.auth_config_id

                # Update metadata to mark as connected (remove pending_auth status)
                if existing_conn and existing_conn.metadata:
                    metadata = existing_conn.metadata.copy()
                    metadata['status'] = 'connected'
                    defaults['metadata'] = metadata
                else:
                    defaults['metadata'] = {'status': 'connected'}

                ComposioConnection.objects.update_or_create(
                    user=request.user,
                    tool_name=conn_detail['tool_name'].upper(),
                    defaults=defaults
                )
            
            connected_tool_names = [c['tool_name'].upper() for c in connection_details]
            
            # Mark any tools no longer in Composio as inactive
            ComposioConnection.objects.filter(
                user=request.user
            ).exclude(
                tool_name__in=connected_tool_names
            ).update(is_active=False)
            
            connections = ComposioConnection.objects.filter(user=request.user, is_active=True)
            serializer = ComposioConnectionSerializer(connections, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            traceback.print_exc()
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@extend_schema_view(
    list=extend_schema(
        tags=['triggers'],
        operation_id='triggers_list',
        summary='List all triggers',
        description='Returns list of all triggers owned by the authenticated user. Automation triggers API. All endpoints require authentication.',
        responses={
            200: OpenApiResponse(response=TriggerSerializer(many=True), description='List of triggers'),
            401: OpenApiResponse(description='Authentication required')
        }
    ),
    create=extend_schema(
        tags=['triggers'],
        operation_id='triggers_create',
        summary='Create a new trigger',
        description='Creates a new automation trigger. All endpoints require authentication.',
        request=TriggerSerializer,
        responses={
            201: OpenApiResponse(response=TriggerSerializer, description='Trigger created'),
            400: OpenApiResponse(description='Validation error'),
            401: OpenApiResponse(description='Authentication required')
        }
    ),
    retrieve=extend_schema(
        tags=['triggers'],
        operation_id='triggers_retrieve',
        summary='Get trigger details',
        description='Returns details of a specific trigger by ID. All endpoints require authentication.',
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Trigger ID (integer)',
                required=True
            )
        ],
        responses={
            200: OpenApiResponse(response=TriggerSerializer, description='Trigger details'),
            401: OpenApiResponse(description='Authentication required'),
            404: OpenApiResponse(description='Trigger not found')
        }
    ),
    update=extend_schema(
        tags=['triggers'],
        operation_id='triggers_update',
        summary='Update trigger (full)',
        description='Fully updates a trigger. All fields are required. All endpoints require authentication.',
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Trigger ID (integer)',
                required=True
            )
        ],
        request=TriggerSerializer,
        responses={
            200: OpenApiResponse(response=TriggerSerializer, description='Trigger updated'),
            400: OpenApiResponse(description='Validation error'),
            401: OpenApiResponse(description='Authentication required'),
            404: OpenApiResponse(description='Trigger not found')
        }
    ),
    partial_update=extend_schema(
        tags=['triggers'],
        operation_id='triggers_partial_update',
        summary='Update trigger (partial)',
        description='Partially updates a trigger. Only provided fields will be updated. All endpoints require authentication.',
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Trigger ID (integer)',
                required=True
            )
        ],
        request=TriggerSerializer,
        responses={
            200: OpenApiResponse(response=TriggerSerializer, description='Trigger updated'),
            400: OpenApiResponse(description='Validation error'),
            401: OpenApiResponse(description='Authentication required'),
            404: OpenApiResponse(description='Trigger not found')
        }
    ),
    destroy=extend_schema(
        tags=['triggers'],
        operation_id='triggers_destroy',
        summary='Delete trigger',
        description='Deletes a trigger by ID. All endpoints require authentication.',
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Trigger ID (integer)',
                required=True
            )
        ],
        responses={
            204: OpenApiResponse(description='Trigger deleted successfully'),
            401: OpenApiResponse(description='Authentication required'),
            404: OpenApiResponse(description='Trigger not found')
        }
    )
)
class TriggerViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Triggers (e.g., "on new email...").
    """
    serializer_class = TriggerSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Ensures users can only see their own triggers.
        """
        return Trigger.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def available(self, request):
        """
        Returns the hardcoded list of available trigger types for the UI.
        """
        agent_service = AgentService(request.user)
        triggers = agent_service.get_available_triggers()
        return Response(triggers)
    
    def perform_create(self, serializer):
        """
        Called when a new trigger is created.
        """
        trigger = serializer.save(user=self.request.user)
        
        # If it's an event-based trigger, register it with Composio
        if trigger.trigger_type == 'event':
            try:
                agent_service = AgentService(self.request.user)
                result = agent_service.create_trigger(trigger)
                
                if result.get('success'):
                    trigger.composio_trigger_id = result.get('trigger_id', '')
                    trigger.save()
                    print(f"✅ Trigger created in Composio: {trigger.composio_trigger_id}")
                else:
                    print(f"⚠️ Failed to create trigger in Composio: {result.get('error')}")
                    
            except Exception as e:
                print(f"❌ Error creating trigger in Composio: {e}")
                traceback.print_exc()
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Sets a trigger's status to 'active'.
        """
        trigger = self.get_object()
        trigger.status = 'active'
        trigger.save()
        return Response({'status': 'Trigger activated'})
    
    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """
        Sets a trigger's status to 'paused'.
        """
        trigger = self.get_object()
        trigger.status = 'paused'
        trigger.save()
        return Response({'status': 'Trigger paused'})
    
    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        """
        Sets a trigger's status to 'stopped'.
        """
        trigger = self.get_object()
        trigger.status = 'stopped'
        trigger.save()
        return Response({'status': 'Trigger stopped'})
    
    @action(detail=True, methods=['get'])
    def executions(self, request, pk=None):
        """
        Gets the 50 most recent execution logs for a trigger.
        """
        trigger = self.get_object()
        executions = TriggerExecution.objects.filter(trigger=trigger)[:50]
        serializer = TriggerExecutionSerializer(executions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """
        Manually runs a trigger's action prompt.
        """
        trigger = self.get_object()
        
        try:
            agent_service = AgentService(request.user)
            print("--- [TEST TRIGGER] ---")
            
            # 1. Get history (to provide context)
            chat_history_qs = ChatMessage.objects.filter(agent=trigger.agent).order_by('-created_at')[:6]
            chat_history = list(chat_history_qs)
            chat_history.reverse()
            chat_history_formatted = [{"role": msg.role, "content": msg.content} for msg in chat_history]
            
            # 2. Get test prompt
            test_prompt = f"[TEST TRIGGER] {trigger.action_prompt}"
            chat_history_formatted.append({"role": "user", "content": test_prompt})

            # 3. Select tools for this prompt
            specific_tools_slugs = agent_service.select_tools_for_prompt(
                user_prompt=test_prompt,
                app_names=trigger.agent.app_connections,
                chat_history=chat_history_formatted
            )

            # 4. Execute
            if not specific_tools_slugs:
                response = asyncio.run(agent_service._chat_without_tools(
                    agent_model=trigger.agent, 
                    message=test_prompt,
                    chat_history=chat_history_formatted
                ))
            else:
                response = asyncio.run(agent_service._chat_with_composio(
                    agent_model=trigger.agent, 
                    message=test_prompt, 
                    specific_tools_slugs=specific_tools_slugs,
                    chat_history=chat_history_formatted
                ))

            # 5. Log the execution
            execution = TriggerExecution.objects.create(
                trigger=trigger,
                event_data={'test': True, 'manual_trigger': True},
                agent_response=response,
                success=True
            )
            
            trigger.trigger_count += 1
            trigger.save()
            
            return Response({
                'success': True,
                'response': response,
                'execution_id': execution.id
            })
            
        except Exception as e:
            traceback.print_exc()
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@extend_schema_view(
    list=extend_schema(
        tags=['workflows'],
        operation_id='workflows_list',
        summary='List all workflows',
        description='Returns list of all workflows owned by the authenticated user. Visual workflow management API. All endpoints require authentication.',
        responses={
            200: OpenApiResponse(response=WorkflowSerializer(many=True), description='List of workflows'),
            401: OpenApiResponse(description='Authentication required')
        }
    ),
    create=extend_schema(
        tags=['workflows'],
        operation_id='workflows_create',
        summary='Create a new workflow',
        description='Creates a new visual workflow. All endpoints require authentication.',
        request=WorkflowSerializer,
        responses={
            201: OpenApiResponse(response=WorkflowSerializer, description='Workflow created'),
            400: OpenApiResponse(description='Validation error'),
            401: OpenApiResponse(description='Authentication required')
        }
    ),
    retrieve=extend_schema(
        tags=['workflows'],
        operation_id='workflows_retrieve',
        summary='Get workflow details',
        description='Returns details of a specific workflow by ID. All endpoints require authentication.',
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Workflow ID (integer)',
                required=True
            )
        ],
        responses={
            200: OpenApiResponse(response=WorkflowSerializer, description='Workflow details'),
            401: OpenApiResponse(description='Authentication required'),
            404: OpenApiResponse(description='Workflow not found')
        }
    ),
    update=extend_schema(
        tags=['workflows'],
        operation_id='workflows_update',
        summary='Update workflow (full)',
        description='Fully updates a workflow. All fields are required. All endpoints require authentication.',
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Workflow ID (integer)',
                required=True
            )
        ],
        request=WorkflowSerializer,
        responses={
            200: OpenApiResponse(response=WorkflowSerializer, description='Workflow updated'),
            400: OpenApiResponse(description='Validation error'),
            401: OpenApiResponse(description='Authentication required'),
            404: OpenApiResponse(description='Workflow not found')
        }
    ),
    partial_update=extend_schema(
        tags=['workflows'],
        operation_id='workflows_partial_update',
        summary='Update workflow (partial)',
        description='Partially updates a workflow. Only provided fields will be updated. All endpoints require authentication.',
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Workflow ID (integer)',
                required=True
            )
        ],
        request=WorkflowSerializer,
        responses={
            200: OpenApiResponse(response=WorkflowSerializer, description='Workflow updated'),
            400: OpenApiResponse(description='Validation error'),
            401: OpenApiResponse(description='Authentication required'),
            404: OpenApiResponse(description='Workflow not found')
        }
    ),
    destroy=extend_schema(
        tags=['workflows'],
        operation_id='workflows_destroy',
        summary='Delete workflow',
        description='Deletes a workflow by ID. All endpoints require authentication.',
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Workflow ID (integer)',
                required=True
            )
        ],
        responses={
            204: OpenApiResponse(description='Workflow deleted successfully'),
            401: OpenApiResponse(description='Authentication required'),
            404: OpenApiResponse(description='Workflow not found')
        }
    )
)
class WorkflowViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing visual Workflows (e.g., React Flow).
    """
    serializer_class = WorkflowSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Ensures users can only see their own workflows.
        """
        return Workflow.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """
        Associates the workflow with the current user.
        """
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['get'])
    def executions(self, request, pk=None):
        """
        Gets the 50 most recent execution logs for a workflow.
        """
        workflow = self.get_object()
        executions = WorkflowExecution.objects.filter(workflow=workflow)[:50]
        serializer = WorkflowExecutionSerializer(executions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """
        Manually executes a workflow.
        (Currently a mock implementation).
        """
        workflow = self.get_object()
        
        try:
            import time
            start_time = time.time()
            
            # TODO: Implement actual workflow execution logic
            input_data = request.data.get('input', {})
            
            execution = WorkflowExecution.objects.create(
                workflow=workflow,
                input_data=input_data,
                output_data={'status': 'success', 'message': 'Workflow executed successfully (MOCK)'},
                execution_trace=[
                    {'step': 1, 'node': 'start', 'status': 'completed'},
                    {'step': 2, 'node': 'action', 'status': 'completed'},
                ],
                success=True,
                execution_time_ms=int((time.time() - start_time) * 1000)
            )
            
            workflow.execution_count += 1
            workflow.last_executed = execution.executed_at
            workflow.save()
            
            return Response({
                'success': True,
                'execution': WorkflowExecutionSerializer(execution).data
            })
            
        except Exception as e:
            traceback.print_exc()
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Sets a workflow's status to 'active'.
        """
        workflow = self.get_object()
        workflow.status = 'active'
        workflow.save()
        return Response(WorkflowSerializer(workflow).data)
    
    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """
        Sets a workflow's status to 'paused'.
        """
        workflow = self.get_object()
        workflow.status = 'paused'
        workflow.save()
        return Response(WorkflowSerializer(workflow).data)
    
    @action(detail=False, methods=['post'])
    def duplicate(self, request):
        """
        Creates a copy of an existing workflow.
        """
        try:
            workflow_id = request.data.get('workflow_id')
            original = Workflow.objects.get(id=workflow_id, user=request.user)
            
            # Create a copy
            workflow = Workflow.objects.create(
                user=request.user,
                agent=original.agent,
                name=f"{original.name} (Copy)",
                description=original.description,
                status='draft',
                nodes=original.nodes,
                edges=original.edges,
                viewport=original.viewport
            )
            
            return Response(WorkflowSerializer(workflow).data, status=status.HTTP_201_CREATED)

        except Workflow.DoesNotExist:
            return Response(
                {'error': 'Workflow not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            traceback.print_exc()
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================================================
# TELEGRAM BOT INTEGRATION
# ============================================================================

@extend_schema(
    tags=['messaging'],
    operation_id='telegram_connect',
    summary='Connect Telegram bot to agent',
    request=serializers.ConnectTelegramBotSerializer,
    responses=serializers.MessagingChannelSerializer,
    examples=[
        OpenApiExample(
            'Request Example',
            value={
                'bot_token': '123456789:ABCdefGHIjklMNOpqrsTUVwxyz'
            },
            request_only=True
        ),
        OpenApiExample(
            'Success Response',
            value={
                'id': 1,
                'platform': 'telegram',
                'platform_display': 'Telegram',
                'bot_username': 'my_agent_bot',
                'status': 'active',
                'status_display': 'Active',
                'message_count': 0,
                'last_message_at': None,
                'created_at': '2025-11-26T12:00:00Z',
                'updated_at': '2025-11-26T12:00:00Z'
            },
            response_only=True,
            status_codes=['200']
        )
    ],
    description='Connect a Telegram bot to an agent. User must create their own bot via @BotFather first and provide the bot token. The bot will be configured to send messages to this agent.'
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def connect_telegram_bot(request, agent_id):
    """Connect a Telegram bot to an agent"""
    from .telegram_utils import verify_bot_token, set_webhook, TelegramAPIError

    try:
        # Get the agent
        agent = Agent.objects.get(id=agent_id, user=request.user)

        # Validate request data
        serializer = ConnectTelegramBotSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        bot_token = serializer.validated_data['bot_token']

        # Verify the bot token with Telegram API
        try:
            bot_info = verify_bot_token(bot_token)
        except TelegramAPIError as e:
            return Response(
                {'error': f'Invalid bot token: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if channel already exists
        channel, created = MessagingChannel.objects.get_or_create(
            agent=agent,
            platform='telegram',
            defaults={
                'bot_token': bot_token,
                'bot_username': bot_info.get('username', ''),
                'status': 'active'
            }
        )

        if not created:
            # Update existing channel
            channel.bot_token = bot_token
            channel.bot_username = bot_info.get('username', '')
            channel.status = 'active'
            channel.last_error = ''
            channel.save()

        # Set webhook URL
        webhook_url = f"{request.scheme}://{request.get_host()}/api/telegram/webhook/{agent_id}/"

        try:
            set_webhook(bot_token, webhook_url)
            channel.webhook_url = webhook_url
            channel.save()
        except TelegramAPIError as e:
            channel.status = 'error'
            channel.last_error = str(e)
            channel.save()
            return Response(
                {'error': f'Failed to set webhook: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            MessagingChannelSerializer(channel).data,
            status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED
        )

    except Agent.DoesNotExist:
        return Response(
            {'error': 'Agent not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        traceback.print_exc()
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    tags=['messaging'],
    operation_id='messaging_disconnect',
    summary='Disconnect messaging channel from agent',
    request=serializers.DisconnectMessagingChannelSerializer,
    responses={200: OpenApiResponse(description='Channel disconnected successfully')},
    examples=[
        OpenApiExample(
            'Request Example',
            value={'platform': 'telegram'},
            request_only=True
        ),
        OpenApiExample(
            'Success Response',
            value={'message': 'Telegram channel disconnected successfully'},
            response_only=True,
            status_codes=['200']
        )
    ],
    description='Disconnect a messaging channel (Telegram or WhatsApp) from an agent. This will delete the webhook and remove the connection.'
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def disconnect_messaging_channel(request, agent_id):
    """Disconnect a messaging channel from an agent"""
    from .telegram_utils import delete_webhook

    try:
        agent = Agent.objects.get(id=agent_id, user=request.user)

        serializer = DisconnectMessagingChannelSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        platform = serializer.validated_data['platform']

        try:
            channel = MessagingChannel.objects.get(agent=agent, platform=platform)

            # Delete webhook if Telegram
            if platform == 'telegram' and channel.bot_token:
                delete_webhook(channel.bot_token)

            # Delete the channel and all sessions
            channel.delete()

            return Response(
                {'message': f'{platform.capitalize()} channel disconnected successfully'},
                status=status.HTTP_200_OK
            )

        except MessagingChannel.DoesNotExist:
            return Response(
                {'error': f'No {platform} channel found for this agent'},
                status=status.HTTP_404_NOT_FOUND
            )

    except Agent.DoesNotExist:
        return Response(
            {'error': 'Agent not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        traceback.print_exc()
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    tags=['messaging'],
    operation_id='messaging_channels_list',
    summary='Get messaging channels for agent',
    responses=serializers.MessagingChannelSerializer(many=True),
    description='Get all connected messaging channels (Telegram, WhatsApp) for an agent'
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_messaging_channels(request, agent_id):
    """Get all messaging channels for an agent"""
    try:
        agent = Agent.objects.get(id=agent_id, user=request.user)
        channels = MessagingChannel.objects.filter(agent=agent)
        return Response(
            MessagingChannelSerializer(channels, many=True).data,
            status=status.HTTP_200_OK
        )

    except Agent.DoesNotExist:
        return Response(
            {'error': 'Agent not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([AllowAny])  # Telegram webhook doesn't use auth
def telegram_webhook(request, agent_id):
    """
    Webhook endpoint for receiving Telegram messages.
    Called by Telegram when users send messages to the bot.
    """
    from .telegram_utils import send_message, send_typing_action, TelegramAPIError
    from .credits import deduct_credits_for_message

    try:
        # Get the channel
        try:
            channel = MessagingChannel.objects.select_related('agent', 'agent__user').get(
                agent_id=agent_id,
                platform='telegram',
                status='active'
            )
        except MessagingChannel.DoesNotExist:
            return Response({'error': 'Channel not found'}, status=status.HTTP_404_NOT_FOUND)

        agent = channel.agent
        bot_token = channel.bot_token

        # Parse Telegram update
        update = request.data

        # Extract message data
        message = update.get('message', {})
        if not message:
            # Not a message update, ignore
            return Response({'ok': True})

        chat_id = str(message.get('chat', {}).get('id'))
        user_id = str(message.get('from', {}).get('id'))
        username = message.get('from', {}).get('username', '')
        text = message.get('text', '')

        if not chat_id or not text:
            return Response({'ok': True})

        # Get or create session
        session, _ = MessagingSession.objects.get_or_create(
            channel=channel,
            external_user_id=user_id,
            defaults={
                'external_chat_id': chat_id,
                'external_username': username,
                'is_active': True
            }
        )

        # Update session
        session.external_chat_id = chat_id
        session.external_username = username
        session.message_count += 1
        session.save()

        # Save user message to chat history
        ChatMessage.objects.create(
            agent=agent,
            role='user',
            content=text
        )

        # Check if user has credits (deduct 1 credit per message)
        if not agent.user.has_credits(1):
            # Send error message to user
            try:
                send_message(
                    bot_token,
                    chat_id,
                    "⚠️ Agent owner has insufficient credits. Please contact them to add more credits."
                )
            except:
                pass
            return Response({'ok': True})

        # Show typing indicator
        send_typing_action(bot_token, chat_id)

        # Process message with agent
        agent_service = AgentService(agent)

        # Get chat history for context
        previous_messages = ChatMessage.objects.filter(agent=agent).order_by('-created_at')[:10]
        chat_history = [
            {"role": msg.role, "content": msg.content}
            for msg in reversed(list(previous_messages))
        ]

        # Generate response
        response_content = agent_service.chat(text, chat_history)

        # Save assistant response
        ChatMessage.objects.create(
            agent=agent,
            role='assistant',
            content=response_content
        )

        # Send response to Telegram
        try:
            send_message(bot_token, chat_id, response_content)

            # Deduct credits
            deduct_credits_for_message(
                user=agent.user,
                agent=agent,
                message_content=text
            )

            # Update channel stats
            channel.message_count += 1
            channel.last_message_at = timezone.now()
            channel.save()

        except TelegramAPIError as e:
            # Log error but don't fail the webhook
            channel.status = 'error'
            channel.last_error = str(e)
            channel.save()

        return Response({'ok': True})

    except Exception as e:
        traceback.print_exc()
        # Always return 200 to Telegram to avoid retries
        return Response({'ok': True})