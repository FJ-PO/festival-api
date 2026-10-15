# Cómo contribuir

## Ramas

Todo el proyecto vive en una sola rama, `main`. Para un cambio grande puedes abrir una rama temporal
(`feat/<nombre>`, `fix/<nombre>`…) desde `main`, que se fusiona en `main` por pull request y se borra después.

## Commits

Seguimos [Conventional Commits](https://www.conventionalcommits.org/es/), en español:

```
feat(admin): editor de páginas con vista previa
fix(api): el check-in no aceptaba códigos en minúsculas
docs: explica la autenticación JWT
chore(ci): ejecuta los tests en Python 3.13
```

Tipos: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`. El ámbito (`api`, `cms`, `frontend`, `admin`, `auth`…) es
opcional.

## Pull requests

1. Crea tu rama desde `main`: `git switch main && git pull && git switch -c feat/mi-cambio`.
2. Comprueba que pasa todo en local:
   ```bash
   pytest -q
   (cd frontend && npm run lint && npm run build)
   (cd admin && npm run lint && npm run build)
   ```
3. Sube la rama y abre el PR contra `main`, rellenando la plantilla.
4. La CI tiene que estar en verde y al menos una persona tiene que revisarlo antes de fusionar.

## Seguridad

- Nunca subas `.env`, bases de datos (`*.db`) ni la carpeta `uploads/` (ya están en `.gitignore`).
- La autenticación es solo con JWT en la cabecera `Authorization`. No añadas cookies ni sesiones de servidor.
- Cualquier HTML que venga del CMS se sanea con DOMPurify antes de pintarlo.
