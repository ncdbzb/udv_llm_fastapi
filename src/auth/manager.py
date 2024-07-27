import jwt
from typing import Optional, Dict, Any

from fastapi import Depends, Request, Response, HTTPException, status
from fastapi_users import BaseUserManager, exceptions, IntegerIDMixin, models, schemas, InvalidPasswordException
from fastapi_users.jwt import generate_jwt, decode_jwt

from src.auth.models import AuthUser
from src.auth.utils import get_user_db
from src.services.celery_service import send_email
from database.database import async_session_maker
from src.admin_panel.utils import add_admin_request
from config.config import SECRET_MANAGER, admin_dict, SEND_ADMIN_NOTICES


class UserManager(IntegerIDMixin, BaseUserManager[AuthUser, int]):
    reset_password_token_secret = SECRET_MANAGER
    verification_token_secret = SECRET_MANAGER


    async def on_after_register(self, user: AuthUser, request: Optional[Request] = None):
        print(f"User {user.id} has registered.")

        if user.email != admin_dict["email"]:
            async with async_session_maker() as session:
                await add_admin_request(user.email, session=session)

            send_email.delay(name=user.name, user_email=user.email, destiny='approval')
            if SEND_ADMIN_NOTICES:
                send_email.delay(name=user.name, surname=user.surname, user_email=user.email, destiny='admin_approval')

    async def on_after_forgot_password(
            self, user: AuthUser, token: str, request: Optional[Request] = None
    ):
        print(f"User {user.id} has forgot his password")
        token_data = {
            "sub": str(user.id),
            "password_fgpt": self.password_helper.hash(user.hashed_password),
            "aud": self.reset_password_token_audience,
        }
        token = generate_jwt(
            token_data,
            self.reset_password_token_secret,
            self.reset_password_token_lifetime_seconds,
        )
        send_email.delay(name=user.name, user_email=user.email, token=token, destiny='forgot')

    async def validate_password(
            self, password: str, user: AuthUser, user_update: Dict[str, Any] = None
    ) -> None:
        """
        Validate a password.

        *You should overload this method to add your own validation logic.*

        :param password: The password to validate.
        :param user: The user associated to this password.
        :raises InvalidPasswordException: The password is invalid.
        :return: None if the password is valid.
        """
        if len(password) < 6:
            raise InvalidPasswordException(reason='The password must be at least 6 characters long')
        try:
            if password != user.confirmation_password:
                raise InvalidPasswordException(reason="Passwords don't match")
        except AttributeError as e:
            if user_update:
                try:
                    if not user_update.get('reset_password') and password != user_update['confirmation_password']:
                        raise InvalidPasswordException(reason="Passwords don't match")
                except KeyError:
                    raise InvalidPasswordException(reason='Confirmation password is not filled')
                try:
                    if not user_update.get('reset_password') and not self.password_helper.verify_and_update(
                            user_update['old_password'], user.hashed_password)[0]:
                        raise InvalidPasswordException(reason="Invalid password")
                except KeyError:
                    raise InvalidPasswordException(reason='Old password is not filled')
        return  # pragma: no cover

    async def create(
            self,
            user_create: schemas.UC,
            safe: bool = False,
            request: Optional[Request] = None,
    ) -> models.UP:
        """
        Create a user in database.

        Triggers the on_after_register handler on success.

        :param user_create: The UserCreate model to create.
        :param safe: If True, sensitive values like is_superuser or is_verified
        will be ignored during the creation, defaults to False.
        :param request: Optional FastAPI request that
        triggered the operation, defaults to None.
        :raises UserAlreadyExists: A user already exists with the same e-mail.
        :return: A new user.
        """
        await self.validate_password(user_create.password, user_create)

        existing_user = await self.user_db.get_by_email(user_create.email)
        if existing_user is not None:
            raise exceptions.UserAlreadyExists()

        user_dict = (
            user_create.create_update_dict()
            if safe
            else user_create.create_update_dict_superuser()
        )

        if user_dict["email"] == admin_dict["email"]:
            if user_dict["password"] == admin_dict["password"]:
                user_dict = admin_dict.copy()
                password = user_dict.pop("password")
                user_dict["hashed_password"] = self.password_helper.hash(password)
            else:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        else:
            password = user_dict.pop("password")
            user_dict["hashed_password"] = self.password_helper.hash(password)

            user_dict.pop("confirmation_password")
            user_dict["is_active"] = True
            user_dict["is_superuser"] = False
            user_dict["is_verified"] = False

        created_user = await self.user_db.create(user_dict)

        await self.on_after_register(created_user, request)

        return created_user

    async def verify(self, token: str, request: Optional[Request] = None) -> models.UP:
        """
        Validate a verification request.

        Changes the is_verified flag of the user to True.

        Triggers the on_after_verify handler on success.

        :param token: The verification token generated by request_verify.
        :param request: Optional FastAPI request that
        triggered the operation, defaults to None.
        :raises InvalidVerifyToken: The token is invalid or expired.
        :raises UserAlreadyVerified: The user is already verified.
        :return: The verified user.
        """
        try:
            data = decode_jwt(
                token,
                self.verification_token_secret,
                [self.verification_token_audience],
            )
        except jwt.PyJWTError:
            raise exceptions.InvalidVerifyToken()

        try:
            user_id = data["sub"]
            email = data["email"]
        except KeyError:
            raise exceptions.InvalidVerifyToken()

        try:
            user = await self.get_by_email(email)
        except exceptions.UserNotExists:
            raise exceptions.InvalidVerifyToken()

        try:
            parsed_id = self.parse_id(user_id)
        except exceptions.InvalidID:
            raise exceptions.InvalidVerifyToken()

        if parsed_id != user.id:
            raise exceptions.InvalidVerifyToken()

        if user.is_verified:
            raise exceptions.UserAlreadyVerified()

        verified_user = await self._update(user, {"is_verified": True})

        await self.on_after_verify(verified_user, request)

        return verified_user

    async def on_after_login(
            self,
            user: models.UP,
            request: Optional[Request] = None,
            response: Optional[Response] = None,
    ) -> None:
        """
        Perform logic after user login.

        *You should overload this method to add your own logic.*

        :param user: The user that is logging in
        :param request: Optional FastAPI request
        :param response: Optional response built by the transport.
        Defaults to None
        """
        return  # pragma: no cover

    async def reset_password(
        self, token: str, password: str, request: Optional[Request] = None
    ) -> models.UP:
        """
        Reset the password of a user.

        Triggers the on_after_reset_password handler on success.

        :param token: The token generated by forgot_password.
        :param password: The new password to set.
        :param request: Optional FastAPI request that
        triggered the operation, defaults to None.
        :raises InvalidResetPasswordToken: The token is invalid or expired.
        :raises UserInactive: The user is inactive.
        :raises InvalidPasswordException: The password is invalid.
        :return: The user with updated password.
        """
        try:
            data = decode_jwt(
                token,
                self.reset_password_token_secret,
                [self.reset_password_token_audience],
            )
        except jwt.PyJWTError:
            raise exceptions.InvalidResetPasswordToken()

        try:
            user_id = data["sub"]
            password_fingerprint = data["password_fgpt"]
        except KeyError:
            raise exceptions.InvalidResetPasswordToken()

        try:
            parsed_id = self.parse_id(user_id)
        except exceptions.InvalidID:
            raise exceptions.InvalidResetPasswordToken()

        user = await self.get(parsed_id)

        valid_password_fingerprint, _ = self.password_helper.verify_and_update(
            user.hashed_password, password_fingerprint
        )
        if not valid_password_fingerprint:
            raise exceptions.InvalidResetPasswordToken()

        if not user.is_active:
            raise exceptions.UserInactive()

        updated_user = await self._update(user, {"reset_password": password})

        await self.on_after_reset_password(user, request)

        return updated_user

    async def update(
            self,
            user_update: schemas.UU,
            user: models.UP,
            safe: bool = False,
            request: Optional[Request] = None,
    ) -> models.UP:
        """
        Update a user.

        Triggers the on_after_update handler on success

        :param user_update: The UserUpdate model containing
        the changes to apply to the user.
        :param user: The current user to update.
        :param safe: If True, sensitive values like is_superuser or is_verified
        will be ignored during the update, defaults to False
        :param request: Optional FastAPI request that
        triggered the operation, defaults to None.
        :return: The updated user.
        """
        if safe:
            updated_user_data = user_update.create_update_dict()
        else:
            updated_user_data = user_update.create_update_dict_superuser()
        updated_user = await self._update(user, updated_user_data)
        await self.on_after_update(updated_user, updated_user_data, request)
        return updated_user

    async def _update(self, user: models.UP, update_dict: Dict[str, Any]) -> models.UP:
        validated_update_dict = {}
        for field, value in update_dict.items():
            if field == "email" and value != user.email:
                try:
                    await self.get_by_email(value)
                    raise exceptions.UserAlreadyExists()
                except exceptions.UserNotExists:
                    validated_update_dict["email"] = value
                    # validated_update_dict["is_verified"] = False
            elif field in ("password", "reset_password") and value is not None:
                await self.validate_password(value, user, update_dict)
                validated_update_dict["hashed_password"] = self.password_helper.hash(
                    value
                )
            elif field not in ('confirmation_password', 'old_password'):
                validated_update_dict[field] = value
        return await self.user_db.update(user, validated_update_dict)


async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)