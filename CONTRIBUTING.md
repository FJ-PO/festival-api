# Cómo contribuir

## Ramas

Usamos una versión ligera de *Git Flow*:

| Rama | Para qué |
|---|---|
| `main` | Lo que está en producción. Solo recibe merges desde `develop` (releases) o `hotfix/*`. |
| `develop` | Rama de integración (rama por defecto). Aquí se fusionan las funcionalidades terminadas. |
| `feature/<nombre>` | Una funcionalidad nueva. Sale de `develop` y vuelve a `develop` por pull request. |
| `fix/<nombre>` | Corrección de un bug en `develop`. |
| `docs/<nombre>`, `chore/<nombre>` | Documentación, CI, dependencias… |
| `hotfix/<nombre>` | Corrección urgente que sale de `main` y se fusiona en `main` y `develop`. |

Ramas con las que se construyó la primera versión:

```
main ─────────────────────────────────────────────────────────── v1.0.0
  └─ develop ──────────────────────────────────────────────────┘
       └─ feature/auth-admin    #1  login por usuario, admin inicial, JWT sin cookies
            └─ feature/cms      #2  ajustes, páginas, noticias, medios, dashboard
                 └─ feature/frontend      #3  web pública + programación + newsletter
                      └─ feature/admin-panel  #4  panel de administración
                           └─ docs/readme-ci  #5  README, guía y CI
```

Como cada funcionalidad depende de la anterior, los PR están **encadenados**: la base de cada uno es la rama anterior. Al
fusionar uno, GitHub cambia automáticamente la base del siguiente. Se fusionan en orden (#1 → #5) y, al final, se abre un PR de
`develop` a `main` para la release.

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

1. Crea tu rama desde `develop`: `git switch develop && git pull && git switch -c feature/mi-cambio`.
2. Comprueba que pasa todo en local:
   ```bash
   pytest -q
   (cd frontend && npm run lint && npm run build)
   (cd admin && npm run lint && npm run build)
   ```
3. Sube la rama y abre el PR contra `develop`, rellenando la plantilla.
4. La CI tiene que estar en verde y al menos una persona tiene que revisarlo antes de fusionar.

## Seguridad

- Nunca subas `.env`, bases de datos (`*.db`) ni la carpeta `uploads/` (ya están en `.gitignore`).
- La autenticación es solo con JWT en la cabecera `Authorization`. No añadas cookies ni sesiones de servidor.
- Cualquier HTML que venga del CMS se sanea con DOMPurify antes de pintarlo.
