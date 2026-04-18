# Especificación de la app

## Resumen

KineticSOL es una app Linux independiente, orientada a recibir órdenes remotas desde Kinetic WOL en Android y ejecutar acciones locales del sistema. La primera acción soportada será apagar el equipo.

La app se construirá con GTK4 + libadwaita, se distribuirá como Flatpak y se diseñará con prioridad para distros inmutables y entornos modernos basados en systemd.

## Objetivos funcionales

- Mostrar una UI nativa con GTK4 + libadwaita.
- Permitir configurar y visualizar el estado del receptor remoto.
- Escuchar órdenes desde la red local.
- Validar autenticación de la orden remota mediante token compartido.
- Intentar apagar el sistema mediante `org.freedesktop.login1`.
- Exponer el resultado del intento de apagado y los errores de autorización o conectividad.
- Arrancar siempre el listener al abrir la app, sin ajuste manual para desactivarlo.

## No objetivos iniciales

- Soporte para Windows.
- Dependencia principal de scripts del host o configuración manual del sistema.
- Diseño basado en `sudo` interactivo.
- Apertura amplia del system bus.
- Separar desde el principio UI y daemon de sistema.

## Arquitectura inicial propuesta

### Proceso único

La app será un único proceso `Adw.Application` con dos responsabilidades:

- UI de configuración, estado y diagnóstico.
- Servicio interno de escucha de órdenes remotas.

### Recepción remota

El canal inicial será HTTP local, servido desde la propia app:

- Razón: compatible con Android, simple de depurar, no requiere dependencias externas y encaja bien con Flatpak usando `--share=network`.
- Modelo inicial:
  - `GET /api/v1/status`
  - `POST /api/v1/poweroff`
  - autenticación mediante token en cabecera `Authorization: Bearer <token>` o equivalente simple
  - respuesta JSON con resultado y causa de error
  - compatibilidad temporal con rutas heredadas `/v1/status` y `/v1/poweroff`

### Capa de control de energía

La app incorporará una abstracción de energía con una implementación principal:

- `Login1PowerController`
- bus: system bus
- nombre: `org.freedesktop.login1`
- interfaz: `org.freedesktop.login1.Manager`
- métodos relevantes:
  - `CanPowerOff()`
  - `PowerOff(false)`

La llamada remota debe usar `PowerOff(false)` para evitar asumir interacción con un agente de autenticación. Si polkit no autoriza la acción sin prompt, el resultado debe registrarse y mostrarse como limitación del entorno.

### Estado y configuración

Persistencia inicial mediante GSettings:

- `listen-port`
- `shared-token`
- `run-in-background`

Si la plantilla actual no define estas claves todavía, deben añadirse como parte de la base funcional.

## Permisos Flatpak requeridos

Permisos mínimos esperados:

- `--share=network`
- `--system-talk-name=org.freedesktop.login1`
- `--socket=wayland`
- `--socket=fallback-x11`
- `--device=dri`
- `--talk-name=org.kde.StatusNotifierWatcher` solo para integración opcional de bandeja en Plasma
- `--own-name=org.kde.StatusNotifierItem.dev.neikon.kinetic_sol` solo para exponer el item propio en Plasma

Permisos explícitamente no deseados por ahora:

- acceso global al system bus
- `--talk-name=*`
- privilegios especiales del host
- `--filesystem=host`

## Riesgos de polkit

- `CanPowerOff()` puede informar capacidad teórica, pero `PowerOff(false)` seguir fallando por política.
- El usuario activo local puede tener permiso en GNOME Workstation, pero no en todas las variantes de Bazzite.
- En algunos entornos, polkit puede permitir apagado local interactivo pero no una llamada no interactiva desde un sandbox Flatpak.
- La experiencia real depende del host, no solo del manifest.

## Comportamiento esperado en GNOME / Bazzite

Hipótesis de trabajo:

- En GNOME moderno con systemd-logind, la llamada a `login1` desde Flatpak debería ser técnicamente accesible si el manifest concede `--system-talk-name=org.freedesktop.login1`.
- El punto incierto es la decisión de polkit:
  - posible éxito sin prompt
  - posible prompt externo no deseado
  - posible denegación directa

La app debe distinguir claramente entre:

- fallo de red
- fallo de autenticación del token
- fallo de acceso D-Bus
- denegación de polkit
- capacidad no soportada por el host

## Integración de background en Plasma

- Fase 1:
  - cerrar la ventana puede ocultar la app en vez de salir
  - el listener sigue vivo
  - `Quit` sigue cerrando completamente
- Fase 2:
  - cuando la app queda oculta en background, registra un `StatusNotifierItem` para Plasma
  - el tray icon debe servir al menos para reabrir la ventana
  - la integración de bandeja no debe ser la base funcional del producto, solo una mejora específica para Plasma

## Plan de validación

### Validación de arquitectura

1. Lanzar la app empaquetada como Flatpak.
2. Confirmar que el listener remoto acepta conexiones en la red local.
3. Enviar una orden autenticada de apagado desde fuera de la app.
4. Verificar que la app ejecuta la llamada D-Bus a `login1`.
5. Registrar si la llamada:
   - tiene éxito
   - devuelve error de autorización
   - devuelve error de bus o sandbox
   - dispara un prompt no deseado

### Contrato HTTP actual

- `GET /api/v1/status`
  - requiere `Authorization: Bearer <token>`
  - responde `200` con JSON de estado
  - expone `canPowerOff` como valor literal de `CanPowerOff()` y `message` como diagnóstico legible
- `POST /api/v1/poweroff`
  - requiere `Authorization: Bearer <token>`
  - acepta body vacío o `{}` sin esquema adicional
  - responde `200` si `login1` acepta la orden
  - responde `503` si `login1` o polkit rechazan o fallan
- Compatibilidad temporal:
  - `GET /v1/status`
  - `POST /v1/poweroff`

### Integración Android acordada

- Android debe usar `/api/v1/status` y `/api/v1/poweroff` como rutas canónicas.
- Linux mantiene `/v1/...` solo como compatibilidad temporal de transición.
- Android usará `GET /status` para un botón o flujo de “Probar conexión”.
- El objetivo de `GET /status` no es solo reachability, sino distinguir:
  - agente accesible y listo
  - agente accesible pero con `canPowerOff != "yes"`
  - agente accesible pero mal autenticado
  - agente inaccesible

### Validación de entorno real

Probar al menos en un entorno GNOME/Bazzite o equivalente y guardar:

- versión del runtime Flatpak
- distro/variante
- tipo de sesión
- usuario activo
- resultado exacto de `CanPowerOff()`
- resultado exacto de `PowerOff(false)`

## Fases de implementación

1. Documentación, memoria y arquitectura.
2. Base de UI con estado del listener y del backend de energía.
3. Persistencia mínima con GSettings.
4. Listener HTTP local.
5. Cliente D-Bus a `login1`.
6. Validación real del comportamiento de polkit.
7. Ajustes de UX según resultados de la validación.
