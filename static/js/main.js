
// Urban Motion - JavaScript principal

document.addEventListener('DOMContentLoaded', function () {

    // Auto-cerrar alertas después de 4 segundos
    const alertas = document.querySelectorAll('.alert');
    alertas.forEach(function (alerta) {
        setTimeout(function () {
            const bsAlert = new bootstrap.Alert(alerta);
            bsAlert.close();
        }, 4000);
    });

    // Efecto scroll suave en anchors
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });

    // Resaltar navbar link activo
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-link').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });

});

// Función para copiar token (también usada en mi_perfil.html)
function copiarToken() {
    const input = document.getElementById('tokenInput');
    if (input) {
        input.select();
        navigator.clipboard.writeText(input.value).then(() => {
            const btn = input.nextElementSibling;
            const textoOriginal = btn.innerHTML;
            btn.innerHTML = '<i class="bi bi-check-lg"></i> Copiado!';
            btn.classList.add('btn-success');
            btn.classList.remove('btn-warning');
            setTimeout(() => {
                btn.innerHTML = textoOriginal;
                btn.classList.remove('btn-success');
                btn.classList.add('btn-warning');
            }, 2000);
        });
    }
}
