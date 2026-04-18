# Memoria del agente

## Estado actual

- El repositorio parte de una plantilla GNOME en Python con GTK4, libadwaita, Meson y Flatpak.
- El proyecto objetivo es una app Linux independiente de la app Android Kinetic WOL, pero pensada para complementarla.
- El foco inicial no es cubrir toda la funcionalidad final, sino validar una arquitectura viable en entornos Linux modernos e inmutables.

## Decisiones activas

- Plataforma objetivo: Linux only.
- Stack UI: Python + GTK4 + libadwaita.
- Empaquetado principal: Flatpak.
- Enfoque de compatibilidad: priorizar Bazzite, Silverblue, Kinoite y otras distros inmutables.
- Arquitectura inicial: una sola app con UI y lógica de escucha integrada, sin asumir todavía un daemon de sistema separado.
- Canal de control remoto inicial: servicio HTTP local en la red del usuario con autenticación por token compartido.
- Implementación inicial del listener: `ThreadingHTTPServer` de la librería estándar, para evitar dependencias externas y mantener compatibilidad con el runtime Flatpak.
- Contrato de compatibilidad móvil: rutas canónicas `/api/v1/status` y `/api/v1/poweroff`, con compatibilidad temporal para `/v1/status` y `/v1/poweroff`.
- Decisión de sincronización con Android: el cliente Android debe migrar a `/api/v1/...` como ruta canónica y no necesita implementar fallback a `/v1/...` mientras Linux mantenga compatibilidad temporal.
- El endpoint `GET /api/v1/status` debe seguir devolviendo `canPowerOff` y `message`, porque Android quiere usarlo para un flujo de “Probar conexión” y para diferenciar agente accesible de backend realmente listo.
- Mapeo esperado en Android:
  - `401`: token inválido
  - `404`: endpoint o base URL incorrectos
  - `503`: agente accesible pero apagado no disponible por `login1`/polkit/runtime
  - timeout: error de conectividad
- Plan mínimo del lado Android ya acordado:
  - tocar `AgentShutdownSender.kt`, `HomeViewModel.kt`, `HomeUiState.kt`, `KineticWolApp.kt` y `strings.xml`
  - añadir `GET /api/v1/status` para “Probar conexión”
  - migrar `POST /api/v1/poweroff`
  - usar resultados tipados mínimos en vez de error genérico
  - no introducir fallback a `/v1/...` ni tocar SSH en esta fase
- Android usará `canPowerOff == "yes"` como señal de “agente listo” y mostrará un aviso cuando el agente responda pero el backend no esté listo.
- La UI Linux debe mostrar explícitamente la `baseUrl` sugerida para Android usando las IPs LAN detectadas localmente, no solo las rutas de la API.
- La UI Linux tiene que permitir ocultar o mostrar `Diagnostics` desde el menú principal y recordar esa preferencia entre lanzamientos.
- La configuración de la UI Linux ahora debe guardarse y aplicarse automáticamente, sin botón `Save and apply`.
- El listener remoto ya no es configurable: KineticSOL lo arranca siempre al abrir la app y lo mantiene activo hasta salir.
- La primera fase de background mode debe ser simple y compatible con Plasma: un ajuste persistente que haga que cerrar la ventana oculte la app en vez de salir, manteniendo vivo el listener, y dejando el cierre total para la acción `Quit`.
- La segunda fase para Plasma debe añadir una presencia visible al ocultarse: `StatusNotifierItem` por D-Bus, activado solo mientras la app está oculta en background, con permisos Flatpak limitados a `org.kde.StatusNotifierWatcher` y al nombre bien conocido concreto del item.
- El pipeline de GitHub Actions debe construir el bundle `.flatpak` en cada push a `main`, crear una prerelease automática por cada build de `main` y adjuntar también el bundle a las releases publicadas por tag.
- La versión en `meson.build` y la release más reciente del `metainfo` deben coincidir; GitHub Releases debe reutilizar esa versión y esas release notes como fuente de verdad.
- El pipeline debe poder publicar además un repositorio Flatpak estático en GitHub Pages para `main`, junto con un `.flatpakrepo` y una landing de instalación.
- Mientras no exista firma GPG dedicada para CI, ese repo de GitHub Pages se considera `unsigned` y debe documentarse con instalación usando `--no-gpg-verify`.
- La lógica de descubrimiento de IP LAN, construcción de `baseUrl` sugerida y generación de `curl` para Android debe vivir fuera de `window.py`, en un módulo dedicado, para mantener la ventana centrada en UI y ciclo de vida.
- El proyecto debe usar versionado con formato `YY.MM.DD.contador`.
- Acción remota inicial: apagado del equipo.
- Vía preferida para apagar: D-Bus a `org.freedesktop.login1`, método `PowerOff(false)`.
- Política de privilegios: evitar `sudo` interactivo y evitar abrir más permisos de los estrictamente necesarios en Flatpak.

## Restricciones acordadas

- No usar como enfoque principal instalaciones manuales en el sistema host.
- No abrir acceso genérico al system bus desde Flatpak.
- Pedir como mínimo estos permisos Flatpak:
  - `--share=network`
  - `--system-talk-name=org.freedesktop.login1`
- La viabilidad real depende de polkit en runtime; no se debe asumir éxito universal.

## Riesgos abiertos

- `org.freedesktop.login1.PowerOff(false)` puede fallar en algunos entornos Flatpak aunque el bus permita hablar con `login1`.
- Polkit puede exigir autenticación interactiva o denegar la acción según distro, sesión, usuario activo y configuración del host.
- En una distro inmutable, el empaquetado Flatpak es portable, pero la política final sigue estando en el host.
- Si la app no está en ejecución, no habrá escucha remota; esto es una limitación aceptada en la arquitectura inicial.

## Suposiciones válidas por ahora

- La app Android podrá enviar una orden HTTP simple dentro de la red local.
- Un token compartido y configurable es suficiente para la primera iteración.
- La UX inicial puede centrarse en estado, configuración básica, validación de permisos y prueba controlada del apagado.

## Contexto que no debe perderse

- El primer hito técnico es validar la cadena completa:
  1. App GTK/libadwaita empaquetada en Flatpak.
  2. Recepción de una orden remota.
  3. Llamada D-Bus a `login1`.
  4. Observación real del comportamiento de polkit.
- Si la validación demuestra que Flatpak + `login1` + polkit no ofrece un apagado no interactivo fiable, habrá que rediseñar la frontera de privilegios, pero no antes de medirlo.
