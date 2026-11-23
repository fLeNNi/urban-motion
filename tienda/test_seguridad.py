import re
from django.core import mail
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from .models import Pedido


class C03EscaladaPrivilegiosTests(TestCase):
    def setUp(self):
        self.cliente = User.objects.create_user('cliente', 'c@x.com', 'ClavePrueba#2026')
        self.otro = User.objects.create_user('otro', 'o@x.com', 'ClavePrueba#2026')
        self.staff = User.objects.create_user('staff', 's@x.com', 'ClavePrueba#2026', is_staff=True)
        self.root = User.objects.create_superuser('root', 'r@x.com', 'ClavePrueba#2026')

    def test_cliente_no_puede_hacerse_staff(self):
        self.client.login(username='cliente', password='ClavePrueba#2026')
        self.client.post(reverse('editar_usuario', args=[self.cliente.pk]), {
            'username': 'cliente', 'email': 'c@x.com', 'first_name': '', 'last_name': '',
            'is_staff': 'on', 'is_active': 'on',
        })
        self.cliente.refresh_from_db()
        self.assertFalse(self.cliente.is_staff)

    def test_cliente_no_puede_editar_a_otro(self):
        self.client.login(username='cliente', password='ClavePrueba#2026')
        self.client.post(reverse('editar_usuario', args=[self.otro.pk]), {
            'username': 'hackeado', 'email': 'o@x.com',
        })
        self.otro.refresh_from_db()
        self.assertEqual(self.otro.username, 'otro')

    def test_staff_si_puede_promover(self):
        self.client.login(username='staff', password='ClavePrueba#2026')
        self.client.post(reverse('editar_usuario', args=[self.otro.pk]), {
            'username': 'otro', 'email': 'o@x.com', 'first_name': '', 'last_name': '',
            'is_staff': 'on', 'is_active': 'on',
        })
        self.otro.refresh_from_db()
        self.assertTrue(self.otro.is_staff)

    def test_staff_comun_no_toca_superusuario(self):
        self.client.login(username='staff', password='ClavePrueba#2026')
        self.client.post(reverse('editar_usuario', args=[self.root.pk]), {
            'username': 'root', 'email': 'r@x.com', 'first_name': '', 'last_name': '',
        })
        self.root.refresh_from_db()
        self.assertTrue(self.root.is_staff and self.root.is_active)

    def test_staff_comun_no_puede_borrar_superusuario(self):
        self.client.login(username='staff', password='ClavePrueba#2026')
        self.client.post(reverse('eliminar_usuario', args=[self.root.pk]))
        self.assertTrue(User.objects.filter(pk=self.root.pk).exists())


class C09PedidosApiTests(TestCase):
    def setUp(self):
        self.cliente = User.objects.create_user('cliente', 'c@x.com', 'ClavePrueba#2026')
        self.victima = User.objects.create_user('victima', 'v@x.com', 'ClavePrueba#2026')
        self.api = APIClient()
        self.api.force_authenticate(self.cliente)

    def test_no_se_puede_suplantar_usuario_ni_fijar_total_ni_estado(self):
        r = self.api.post(reverse('pedido-list'), {
            'usuario': self.victima.pk, 'total': '0.01', 'estado': 'entregado',
            'direccion_envio': 'x',
        }, format='json')
        if r.status_code == 201:
            p = Pedido.objects.get(pk=r.data['id'])
            self.assertEqual(p.usuario, self.cliente)
            self.assertEqual(p.estado, 'pendiente')

    def test_no_se_pueden_crear_pedidos_vacios(self):
        r = self.api.post(reverse('pedido-list'), {'direccion_envio': 'x'}, format='json')
        self.assertNotEqual(r.status_code, 201, 'La API creo un pedido vacio (sin detalles)')

    def test_pedido_valido_calcula_total_en_servidor(self):
        from .models import Categoria, Producto
        cat = Categoria.objects.create(nombre='Remeras')
        prod = Producto.objects.create(nombre='Remera', descripcion='x', precio=1000, stock=5, categoria=cat)
        r = self.api.post(reverse('pedido-list'), {
            'usuario': self.victima.pk, 'total': '0.01', 'estado': 'entregado',
            'direccion_envio': 'x', 'items': [{'producto': prod.pk, 'cantidad': 3}],
        }, format='json')
        self.assertEqual(r.status_code, 201, r.data)
        p = Pedido.objects.get(pk=r.data['id'])
        self.assertEqual(p.usuario, self.cliente)
        self.assertEqual(p.estado, 'pendiente')
        self.assertEqual(p.total, 3000)
        self.assertEqual(p.detalles.count(), 1)

    def test_cliente_no_cambia_estado_de_su_pedido(self):
        p = Pedido.objects.create(usuario=self.cliente, total=100)
        r = self.api.patch(reverse('pedido-detail', args=[p.pk]), {'estado': 'entregado'}, format='json')
        p.refresh_from_db()
        self.assertEqual(p.estado, 'pendiente')

    def test_cliente_no_ve_pedidos_ajenos(self):
        p = Pedido.objects.create(usuario=self.victima, total=100)
        r = self.api.get(reverse('pedido-detail', args=[p.pk]))
        self.assertEqual(r.status_code, 404)


class C02ResetPasswordTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('juan', 'juan@x.com', 'ClaveOriginal#2026')

    def _pedir_link(self, email):
        return self.client.post(reverse('olvide_contrasena'), {'email': email})

    def _link_del_mail(self):
        cuerpo = mail.outbox[-1].body
        return re.search(r'http://testserver(/reset/[^\s]+)', cuerpo).group(1)

    def test_respuesta_identica_exista_o_no_el_email(self):
        r1 = self._pedir_link('juan@x.com')
        r2 = self._pedir_link('noexiste@x.com')
        self.assertEqual((r1.status_code, r1.url), (r2.status_code, r2.url))

    def test_solo_se_envia_mail_si_el_usuario_existe(self):
        self._pedir_link('noexiste@x.com')
        self.assertEqual(len(mail.outbox), 0)
        self._pedir_link('juan@x.com')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['juan@x.com'])

    def test_no_se_puede_cambiar_clave_solo_con_usuario_y_email(self):
        # El endpoint viejo aceptaba usuario + email + nueva clave. Ya no debe cambiar nada.
        self.client.post(reverse('olvide_contrasena'), {
            'username': 'juan', 'email': 'juan@x.com',
            'nueva_password': 'ClaveAtacante#9876', 'confirmar_password': 'ClaveAtacante#9876',
        })
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('ClaveOriginal#2026'))

    def test_link_falso_es_rechazado(self):
        r = self.client.get(reverse('password_reset_confirm', args=['MQ', 'token-falso-123']), follow=True)
        self.assertFalse(r.context['validlink'])

    def test_flujo_completo_con_link_valido(self):
        self._pedir_link('juan@x.com')
        r = self.client.get(self._link_del_mail(), follow=True)
        url_form = r.redirect_chain[-1][0]
        # Clave debil: rechazada
        self.client.post(url_form, {'new_password1': '123456', 'new_password2': '123456'})
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('ClaveOriginal#2026'))
        # Clave fuerte: aceptada
        self.client.post(url_form, {'new_password1': 'ClaveNueva#9876', 'new_password2': 'ClaveNueva#9876'})
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('ClaveNueva#9876'))

    def test_el_link_se_usa_una_sola_vez(self):
        self._pedir_link('juan@x.com')
        link = self._link_del_mail()
        r = self.client.get(link, follow=True)
        url_form = r.redirect_chain[-1][0]
        self.client.post(url_form, {'new_password1': 'ClaveNueva#9876', 'new_password2': 'ClaveNueva#9876'})
        # Reusar el mismo link ya no sirve
        r2 = Client().get(link, follow=True)
        self.assertFalse(r2.context['validlink'])


class ConsultasApiTests(TestCase):
    def test_anonimo_no_lee_consultas(self):
        r = APIClient().get(reverse('consulta-list'))
        self.assertIn(r.status_code, (401, 403))

    def test_anonimo_si_puede_enviar_consulta(self):
        r = APIClient().post(reverse('consulta-list'), {
            'nombre': 'Ana', 'email': 'a@x.com', 'asunto': 'Hola', 'mensaje': 'Consulta',
        }, format='json')
        self.assertEqual(r.status_code, 201)


class CatalogoApiPermisosTests(TestCase):
    def setUp(self):
        from .models import Categoria, Producto
        self.cliente = User.objects.create_user('cliente', 'c@x.com', 'ClavePrueba#2026')
        self.staff = User.objects.create_user('staff', 's@x.com', 'ClavePrueba#2026', is_staff=True)
        self.cat = Categoria.objects.create(nombre='Remeras')
        self.prod = Producto.objects.create(nombre='Remera', descripcion='x', precio=1000, stock=5, categoria=self.cat)

    def test_lectura_publica(self):
        self.assertEqual(APIClient().get(reverse('producto-list')).status_code, 200)

    def test_cliente_no_puede_crear_ni_borrar_productos(self):
        api = APIClient()
        api.force_authenticate(self.cliente)
        r = api.post(reverse('producto-list'), {
            'nombre': 'Hack', 'descripcion': 'x', 'precio': '1', 'stock': 1,
        }, format='json')
        self.assertEqual(r.status_code, 403)
        self.assertEqual(api.delete(reverse('producto-detail', args=[self.prod.pk])).status_code, 403)
        self.assertEqual(api.post(reverse('categoria-list'), {'nombre': 'X'}, format='json').status_code, 403)

    def test_staff_si_puede_gestionar_productos(self):
        api = APIClient()
        api.force_authenticate(self.staff)
        r = api.post(reverse('categoria-list'), {'nombre': 'Buzos'}, format='json')
        self.assertEqual(r.status_code, 201)
