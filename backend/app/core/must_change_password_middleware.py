"""يمنع استدعاء واجهات الـ API (عدا الاستثناءات) ما دام المستخدم مُلزماً بتغيير كلمة المرور."""



from starlette.middleware.base import BaseHTTPMiddleware

from starlette.requests import Request

from starlette.responses import JSONResponse



from app.core.config import settings

from app.core.security import decode_access_token_subject

from app.db.session import SessionLocal

from app.models import User





class MustChangePasswordMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):

        if request.method == "OPTIONS":

            return await call_next(request)



        path = request.url.path.rstrip("/") or "/"

        method = request.method.upper()

        prefix = settings.api_v1_prefix.rstrip("/") or ""



        auth_header = request.headers.get("authorization")

        if not auth_header or not auth_header.lower().startswith("bearer "):

            return await call_next(request)



        token = auth_header.split(None, 1)[1].strip()

        uid = decode_access_token_subject(token)

        if uid is None:

            return await call_next(request)



        db = SessionLocal()

        try:

            user = db.get(User, uid)

            if user is None or not user.must_change_password:

                return await call_next(request)



            login_p = f"{prefix}/auth/login"

            seed_p = f"{prefix}/auth/seed-demo-users"

            me_p = f"{prefix}/auth/me"

            ch_p = f"{prefix}/auth/change-password"



            exempt = False

            if path == login_p and method == "POST":

                exempt = True

            elif path == seed_p and method == "POST":

                exempt = True

            elif path == me_p and method == "GET":

                exempt = True

            elif path == ch_p and method == "PATCH":

                exempt = True

            elif path in ("/health", "/docs", "/redoc", "/openapi.json"):

                exempt = True



            if exempt:

                return await call_next(request)



            return JSONResponse(

                status_code=403,

                content={

                    "detail": "يجب تغيير كلمة المرور قبل المتابعة. استخدم واجهة تغيير كلمة المرور.",

                },

            )

        finally:

            db.close()


