pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'kineticsol'
gnome = import('gnome')

gnome.compile_resources('kineticsol',
  'kineticsol.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', get_option('prefix') / get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'kineticsol.in',
  output: 'kineticsol',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'rwxr-xr-x'
)

kineticsol_sources = [
  '__init__.py',
  'main.py',
  'power.py',
  'remote_control.py',
  'settings.py',
  'window.py',
]

install_data(kineticsol_sources, install_dir: moduledir)
