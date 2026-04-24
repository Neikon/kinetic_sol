# KineticSOL

KineticSOL es la app Linux companion de [Kinetic WOL](https://github.com/Neikon/kinetic_wol.git) para Android.

Su objetivo es exponer un agente local en Linux que reciba órdenes desde la app móvil y ejecute acciones del sistema. La primera acción soportada es apagar el equipo usando `systemd-logind` por D-Bus, sin depender de `sudo` interactivo.

## Estado actual

- versión actual: `26.04.24.1`
- plataforma objetivo: Linux only
- stack: Python + GTK4 + libadwaita + Meson + Flatpak
- enfoque: Flatpak-first, compatible con distros modernas e inmutables

## Relación con Kinetic WOL

- repositorio de KineticSOL:
  - <https://github.com/Neikon/kinetic_sol>
- repositorio de Kinetic WOL Android:
  - <https://github.com/Neikon/kinetic_wol.git>

KineticSOL está pensado para funcionar junto con Kinetic WOL. La app Android configura:

- `baseUrl`
- token compartido

Y luego usa el agente Linux para:

- probar conexión
- validar si el backend de apagado está disponible
- enviar la orden de apagado remoto

## Qué hace la app

- muestra una UI GTK4/libadwaita para configurar el agente
- levanta un listener HTTP local autenticado por token
- expone una `baseUrl` sugerida para Android
- permite copiar:
  - token
  - `baseUrl`
  - `curl` de prueba para `GET /api/v1/status`
- consulta `org.freedesktop.login1`
- intenta apagar el sistema con `PowerOff(false)`
- muestra diagnóstico básico del listener y del backend de energía

## API actual

Rutas canónicas:

- `GET /api/v1/status`
- `POST /api/v1/poweroff`

Compatibilidad temporal:

- `GET /v1/status`
- `POST /v1/poweroff`

Autenticación:

- `Authorization: Bearer <token>`

`GET /api/v1/status` responde `200` con JSON de estado, incluyendo:

- `canPowerOff`
- `message`

`POST /api/v1/poweroff`:

- acepta body vacío o `{}`
- responde `200` si `login1` acepta la orden
- responde `503` si el backend falla o polkit lo deniega

## Cómo usarlo

1. Abre KineticSOL.
2. El listener HTTP arranca automáticamente al iniciar la app.
3. Revisa la `Base URL for Android`.
4. Copia el token.
5. En Kinetic WOL Android, configura:
   - `baseUrl`
   - token
6. Usa `Probar conexión` desde Android.

También puedes probar manualmente con el botón `Copy curl`.

Ejemplo:

```bash
curl -i \
  -H 'Accept: application/json' \
  -H 'Authorization: Bearer TU_TOKEN' \
  'http://IP:PUERTO/api/v1/status'
```

## Requisitos de runtime

Flatpak necesita como mínimo:

- `--share=network`
- `--system-talk-name=org.freedesktop.login1`

La app no abre acceso genérico al system bus.

## Limitaciones conocidas

- la app debe estar ejecutándose para recibir órdenes
- el éxito real del apagado depende de polkit y del host
- `CanPowerOff() == "yes"` mejora la expectativa, pero no garantiza todos los entornos
- la política final depende del sistema donde se ejecuta la app, no solo del manifest Flatpak

## Repo Flatpak

El proyecto publica un repositorio Flatpak estático en GitHub Pages.

Enlaces relevantes:

- landing:
  - <https://neikon.github.io/kinetic_sol/>
- `.flatpakrepo`:
  - <https://neikon.github.io/kinetic_sol/kineticsol.flatpakrepo>
- `.flatpakref`:
  - <https://neikon.github.io/kinetic_sol/dev.neikon.kinetic_sol.flatpakref>

Instalación con remote:

```bash
flatpak remote-add --if-not-exists --from kineticsol https://neikon.github.io/kinetic_sol/kineticsol.flatpakrepo
flatpak install kineticsol dev.neikon.kinetic_sol//main
```

Instalación directa con `.flatpakref`:

```bash
flatpak install https://neikon.github.io/kinetic_sol/dev.neikon.kinetic_sol.flatpakref
```

Notas:

- ambos ficheros publicados van firmados con la clave GPG del pipeline
- tanto `.flatpakrepo` como `.flatpakref` incluyen la clave pública necesaria para instalar sin flags especiales
- la landing publicada en GitHub Pages expone ambas opciones de instalación junto con release notes

## Desarrollo

Antes de continuar el desarrollo, lee:

1. [docs/agent_memory.md](docs/agent_memory.md)
2. [docs/app_spec.md](docs/app_spec.md)
3. [docs/roadmap.md](docs/roadmap.md)

## Licencia

GPL-3.0-or-later.
