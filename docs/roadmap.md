# Roadmap

## Completado

- [x] Explorar el repositorio existente antes de asumir arquitectura.
- [x] Confirmar que la base actual es una plantilla GNOME en Python con GTK4/libadwaita y Flatpak.
- [x] Crear memoria persistente del proyecto.
- [x] Documentar la arquitectura inicial, permisos Flatpak, riesgos de polkit y plan de validación.
- [x] Añadir claves GSettings para puerto, token y estado del listener.
- [x] Ajustar el manifest Flatpak para hablar con `org.freedesktop.login1`.
- [x] Crear una primera UI de estado y diagnóstico.
- [x] Implementar un listener HTTP local autenticado por token.
- [x] Implementar la integración D-Bus básica con `org.freedesktop.login1`.
- [x] Cerrar un contrato HTTP inicial compatible con la app Android.
- [x] Acordar con Android el uso canónico de `/api/v1/...` y el uso de `GET /status` para prueba de conexión.
- [x] Acordar el plan mínimo de implementación Android para `status`, `poweroff` y mapeo de errores.
- [x] Mostrar en la UI Linux la `baseUrl` sugerida para configurar Android.
- [x] Añadir un toggle de menú para mostrar u ocultar `Diagnostics`.
- [x] Guardar y aplicar la configuración automáticamente, sin botón manual de guardado.

## En curso

- [ ] Convertir la plantilla actual en la base real de KineticSOL.
- [ ] Verificar el comportamiento real del apagado no interactivo desde Flatpak.
- [ ] Ajustar la UX según el resultado real de polkit.

## Pendiente

- [ ] Exponer en la UI el estado de conectividad, autorización y energía.
- [ ] Probar la app empaquetada en entorno real con GNOME/Bazzite.
- [ ] Registrar resultados reales de `CanPowerOff()` y `PowerOff(false)`.
- [ ] Decidir, según la validación, si la app única sigue siendo suficiente o si hace falta separar componentes.

## Riesgos abiertos

- [ ] Polkit puede impedir el apagado no interactivo desde Flatpak.
- [ ] La app única requiere estar en ejecución para poder recibir órdenes.
- [ ] Puede haber diferencias de comportamiento entre GNOME estándar y variantes gaming/inmutables como Bazzite.

## Criterio de avance inmediato

- La siguiente implementación debe centrarse en la base funcional mínima:
  - UI con estado
  - configuración persistente
  - listener remoto
  - cliente `login1`

- No se debe introducir una arquitectura de daemon separado sin evidencia previa de que la app única no basta.
