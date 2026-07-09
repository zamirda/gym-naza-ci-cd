def obtener_permisos(usuario):
    rol = usuario.usuario.rol

    # Base (usuario normal)
    permisos = {
        "asistencia": False,
        "membresia": False,
        "notificaciones": False,
        "usuarios": False,
        "visitantes": False,
        "elementos": False,
        "mantenimiento": False,
        "categorias": False,
        "turnos": False,

        "nutricion": True,
        "rutinas": True,
        "masa_corporal": True,
        "encuestas": True,
        "soporte": True,
        "sanciones": True,
        "reportes": True,
        "certificaciones": True,
    }

    # Admin ve TODO
    if rol == "Administrador" or usuario.is_superuser:
        for key in permisos:
            permisos[key] = True

    return permisos