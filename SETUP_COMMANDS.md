# 🚀 Comandos para Configurar CI/CD - ML Identity Threat Simulator

## 📋 Resumen de Archivos Creados/Modificados

✅ **Creados:**
- `pyproject.toml` - Configuración completa del proyecto
- `.pre-commit-config.yaml` - Hooks de pre-commit
- `.env.example` - Template de variables de entorno
- `.gitignore` - Actualizado con exclusiones profesionales

✅ **Modificados:**
- `.github/workflows/ci.yml` - CI/CD completo (de 18 líneas → 222 líneas)

---

## 🔧 PASO 1: Configuración Inicial del Entorno

### 1.1 Navegar al directorio del proyecto
```cmd
cd C:\Users\Usuario\Downloads\ml-identity-threat-simulator-main\ml-identity-threat-simulator
```

### 1.2 Crear y activar entorno virtual
```cmd
python -m venv .venv
.venv\Scripts\activate
```

### 1.3 Actualizar pip
```cmd
python -m pip install --upgrade pip
```

### 1.4 Instalar el proyecto en modo desarrollo
```cmd
pip install -e ".[dev]"
```

**⏱️ Tiempo estimado:** 2-3 minutos

---

## 🧪 PASO 2: Verificar Instalación

### 2.1 Verificar que el CLI funciona
```cmd
iam-simulator --help
```

**Salida esperada:**
```
Usage: iam-simulator [OPTIONS] COMMAND [ARGS]...

  ML Identity Threat Simulator CLI

Options:
  --help  Show this message and exit.

Commands:
  audit     Audit an IAM policy for risks.
  simulate  Run a threat scenario simulation.
```

### 2.2 Verificar versión de Python
```cmd
python --version
```

**Debe ser:** Python 3.10 o superior

---

## 🎨 PASO 3: Formatear y Limpiar Código

### 3.1 Formatear código con Black
```cmd
black src/ tests/ reports/
```

### 3.2 Ordenar imports con Ruff
```cmd
ruff check --select I --fix src/ tests/ reports/
```

### 3.3 Aplicar correcciones automáticas de Ruff
```cmd
ruff check --fix src/ tests/ reports/
```

**⏱️ Tiempo estimado:** 30 segundos

---

## 🔍 PASO 4: Verificar Calidad de Código

### 4.1 Verificar formato (sin modificar)
```cmd
black --check src/ tests/ reports/
```

### 4.2 Verificar linting
```cmd
ruff check src/ tests/ reports/
```

### 4.3 Verificar tipos con mypy
```cmd
mypy src/ --ignore-missing-imports
```

**⚠️ Nota:** Es normal que mypy muestre algunos errores inicialmente. Los arreglaremos después.

---

## 🔒 PASO 5: Escaneo de Seguridad

### 5.1 Escanear código con Bandit
```cmd
bandit -r src/ -f screen
```

### 5.2 Verificar vulnerabilidades en dependencias
```cmd
safety check
```

**⚠️ Nota:** Safety puede mostrar advertencias. Revisa si son críticas.

---

## 🧪 PASO 6: Ejecutar Tests

### 6.1 Ejecutar todos los tests
```cmd
pytest -v
```

### 6.2 Ejecutar tests con cobertura
```cmd
pytest --cov=src --cov-report=term-missing --cov-report=html
```

### 6.3 Ver reporte de cobertura en HTML
```cmd
start htmlcov\index.html
```

**⚠️ Nota:** Los tests actuales fallarán porque usan funciones que no existen. Esto es esperado.

---

## 📦 PASO 7: Construir el Paquete

### 7.1 Instalar herramientas de build
```cmd
pip install build twine
```

### 7.2 Construir el paquete
```cmd
python -m build
```

### 7.3 Verificar el paquete
```cmd
twine check dist/*
```

**Salida esperada:**
```
Checking dist\ml_identity_threat_simulator-0.1.0-py3-none-any.whl: PASSED
Checking dist\ml-identity-threat-simulator-0.1.0.tar.gz: PASSED
```

---

## 🎣 PASO 8: Configurar Pre-commit Hooks (Opcional pero Recomendado)

### 8.1 Instalar pre-commit
```cmd
pip install pre-commit
```

### 8.2 Instalar los hooks
```cmd
pre-commit install
```

### 8.3 Ejecutar en todos los archivos (primera vez)
```cmd
pre-commit run --all-files
```

**⏱️ Tiempo estimado:** 1-2 minutos (primera vez es más lento)

---

## 🔄 PASO 9: Configurar Git y GitHub

### 9.1 Verificar estado de Git
```cmd
git status
```

### 9.2 Agregar archivos nuevos
```cmd
git add pyproject.toml
git add .github/workflows/ci.yml
git add .pre-commit-config.yaml
git add .gitignore
git add .env.example
```

### 9.3 Hacer commit
```cmd
git commit -m "feat: Add professional CI/CD pipeline with pyproject.toml

- Add comprehensive pyproject.toml with all dependencies
- Upgrade GitHub Actions workflow with multi-job CI/CD
- Add linting (black, ruff), type checking (mypy), security (bandit, safety)
- Add multi-platform testing (Ubuntu, Windows, macOS)
- Add pre-commit hooks configuration
- Update .gitignore with comprehensive exclusions
- Add .env.example for environment variables"
```

### 9.4 Push a GitHub
```cmd
git push origin main
```

**⚠️ Nota:** Si tu rama principal se llama `master`, usa `git push origin master`

---

## 🌐 PASO 10: Configurar Codecov (Opcional)

### 10.1 Ir a Codecov
1. Visita: https://codecov.io/
2. Inicia sesión con tu cuenta de GitHub
3. Agrega tu repositorio: `ImNotKilian/ml-identity-threat-simulator`

### 10.2 Obtener el token de Codecov
1. En Codecov, ve a Settings → General
2. Copia el `CODECOV_TOKEN`

### 10.3 Agregar el token a GitHub Secrets
1. Ve a tu repositorio en GitHub
2. Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Name: `CODECOV_TOKEN`
5. Value: [pega el token de Codecov]
6. Click "Add secret"

---

## ✅ PASO 11: Verificar que CI/CD Funciona

### 11.1 Ir a GitHub Actions
1. Ve a tu repositorio en GitHub
2. Click en la pestaña "Actions"
3. Deberías ver el workflow "CI" ejecutándose

### 11.2 Verificar los jobs
Deberías ver 5 jobs:
- ✅ **Lint & Format Check** - Verifica formato y linting
- ✅ **Type Check (mypy)** - Verifica tipos
- ✅ **Security Scan** - Escaneo de seguridad
- ✅ **Test (Python 3.10/3.11/3.12)** - Tests en 3 versiones × 3 OS = 9 jobs
- ✅ **Build Package** - Construye el paquete
- ✅ **All Checks Passed** - Verifica que todo pasó

---

## 🚨 Solución de Problemas Comunes

### Problema 1: "pip install -e .[dev]" falla en Windows
**Solución:**
```cmd
pip install -e ".[dev]"
```
(Usa comillas dobles)

### Problema 2: Tests fallan con "ModuleNotFoundError"
**Solución:**
```cmd
set PYTHONPATH=%CD%
pytest -v
```

### Problema 3: Black/Ruff no están instalados
**Solución:**
```cmd
pip install -e ".[dev]"
```

### Problema 4: Pre-commit falla en Windows
**Solución:**
```cmd
pre-commit run --all-files --show-diff-on-failure
```

### Problema 5: GitHub Actions falla en "Install dependencies"
**Causa:** Falta `pyproject.toml` en el repositorio
**Solución:** Asegúrate de hacer commit y push del `pyproject.toml`

---

## 📊 Verificación Final - Checklist

Antes de hacer push, verifica:

- [ ] ✅ `python --version` muestra 3.10+
- [ ] ✅ `iam-simulator --help` funciona
- [ ] ✅ `black --check src/` pasa sin errores
- [ ] ✅ `ruff check src/` pasa sin errores críticos
- [ ] ✅ `pytest` se ejecuta (aunque fallen algunos tests)
- [ ] ✅ `python -m build` crea archivos en `dist/`
- [ ] ✅ `git status` muestra archivos listos para commit
- [ ] ✅ Todos los archivos nuevos están agregados con `git add`

---

## 🎯 Próximos Pasos Después del CI/CD

Una vez que el CI/CD esté funcionando:

1. **Arreglar tests existentes** - Los tests actuales usan funciones que no existen
2. **Agregar más tests** - Alcanzar 80%+ de cobertura
3. **Arreglar warnings de mypy** - Agregar type hints faltantes
4. **Revisar warnings de Bandit** - Arreglar problemas de seguridad
5. **Actualizar README** - Agregar badges de CI/CD

---

## 🆘 ¿Necesitas Ayuda?

Si algún comando falla o tienes dudas:

1. **Copia el error completo**
2. **Indica qué comando ejecutaste**
3. **Muéstrame la salida del comando**

¡Y te ayudaré a resolverlo! 🚀

---

## 📈 Métricas de Éxito

Después de completar estos pasos, deberías tener:

| Métrica | Antes | Después |
|---------|-------|---------|
| Líneas de CI/CD | 18 | 222 |
| Jobs en CI | 1 | 5 |
| Plataformas testeadas | 1 | 3 |
| Versiones de Python | 1 | 3 |
| Herramientas de calidad | 0 | 4 |
| Escaneo de seguridad | ❌ | ✅ |
| Pre-commit hooks | ❌ | ✅ |
| Cobertura de código | ❌ | ✅ |

---

**¡Éxito! 🎉** Tu proyecto ahora tiene un CI/CD de nivel enterprise.
