from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from rest_framework.authtoken.models import Token
from django.utils import timezone


class Command(BaseCommand):
    help = 'Puntos 7 y 8 del TP: Muestra en la consola los Tokens de usuarios y las Cookies/Sesiones activas.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n==============================================================='))
        self.stdout.write(self.style.SUCCESS('   PUNTO 7: TOKENS DE USUARIOS (DJANGO REST FRAMEWORK)'))
        self.stdout.write(self.style.SUCCESS('==============================================================='))

        usuarios = User.objects.all().order_by('id')
        if not usuarios.exists():
            self.stdout.write('No hay usuarios registrados.')
        else:
            self.stdout.write(f"{'ID':<5} {'USUARIO':<18} {'EMAIL':<25} {'TOKEN'}")
            self.stdout.write('-' * 75)
            for u in usuarios:
                token_obj, _ = Token.objects.get_or_create(user=u)
                self.stdout.write(f"{u.id:<5} {u.username:<18} {u.email or '(sin email)':<25} {token_obj.key}")

        self.stdout.write(self.style.WARNING('\n==============================================================='))
        self.stdout.write(self.style.WARNING('   PUNTO 8: SESIONES DE USUARIOS (COOKIES sessionid)'))
        self.stdout.write(self.style.WARNING('==============================================================='))

        sesiones = Session.objects.filter(expire_date__gte=timezone.now()).order_by('-expire_date')
        if not sesiones.exists():
            self.stdout.write('No hay sesiones activas en este momento.')
        else:
            self.stdout.write(f"{'SESSION KEY (Cookie sessionid)':<36} {'VENCE':<22} {'DATOS DECODIFICADOS'}")
            self.stdout.write('-' * 95)
            for s in sesiones:
                data = s.get_decoded()
                user_id = data.get('_auth_user_id', 'Anónimo')
                user_desc = f"User ID: {user_id}"
                if user_id != 'Anónimo':
                    try:
                        u = User.objects.get(id=user_id)
                        user_desc = f"Usuario: {u.username} (ID: {user_id})"
                    except User.DoesNotExist:
                        pass
                vence = s.expire_date.strftime('%d/%m/%Y %H:%M')
                self.stdout.write(f"{s.session_key:<36} {vence:<22} {user_desc}")

        self.stdout.write(self.style.SUCCESS('\n===============================================================\n'))
