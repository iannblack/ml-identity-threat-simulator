# ⚡ Quick Start - Comandos Esenciales

## 🚀 Setup Rápido (5 minutos)

```cmd
# 1. Navegar al proyecto
cd C:\Users\Usuario\Downloads\ml-identity-threat-simulator-main\ml-identity-threat-simulator

# 2. Crear entorno virtual
python -m venv .venv
.venv\Scripts\activate

# 3. Instalar dependencias
python -m pip install --upgrade pip
pip install -e ".[dev]"

# 4. Formatear código
black src/ tests/ reports/
ruff check --fix src/ tests/ reports/

# 5. Verificar calidad
black --check src/ tests/ reports/
ruff check src/ tests/ reports/
mypy src/ --ignore-missing-imports

# 6. Ejecutar tests
pytest --cov=src --cov-report=term-missing

# 7. Construir paquete
pip install build twine
python -m build
twine check dist/*

# 8. Configurar pre-commit (opcional)
pip install pre-commit
pre-commit install
pre-commit run --all-files

# 9. Git commit y push
git add pyproject.toml .github/workflows/ci.yml .pre-commit-config.yaml .gitignore .env.example
git commit -m "feat: Add professional CI/CD pipeline"
git push origin main
```

## 📋 Verificación Rápida

```cmd
# Verificar instalación
iam-simulator --help

# Ver cobertura de tests
start htmlcov\index.html

# Ver estado de Git
git status
```

## 🎯 Lo Más Importante

1. **Instalar:** `pip install -e ".[dev]"`
2. **Formatear:** `black src/ tests/ reports/`
3. **Verificar:** `ruff check src/`
4. **Testear:** `pytest --cov=src`
5. **Push:** `git push origin main`

## 🔗 Ver Guía Completa

Para instrucciones detalladas, ver: `SETUP_COMMANDS.md`
