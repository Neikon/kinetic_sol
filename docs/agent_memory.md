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
