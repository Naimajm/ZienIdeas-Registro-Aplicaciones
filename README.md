# Microsoft Graph Analytics — MVP

**Versión:** 0.1.0 · **Estado:** prototipo local con datos simulados · **Stack:** Python, FastAPI, Pydantic v2, SQLAlchemy 2 y SQLite.

## 1. Objetivo y alcance

Este proyecto recibe y conserva datos de aplicaciones Microsoft 365 / Microsoft Entra ID para permitir su consulta y, de manera independiente, calcular indicadores de uso **por aplicación y día UTC**.

Los **tres grupos principales de información** son:

1. **Aplicaciones:** inventario de aplicaciones empresariales (`servicePrincipals`).
2. **Actividad:** eventos de autenticación (`auditLogs/signIns`).
3. **Asignaciones / registro de acceso:** usuarios, grupos o identidades asignados a las aplicaciones (`appRoleAssignedTo`).

El panel tiene como objetivo mostrar **tres indicadores clave** por aplicación:

| Indicador | Definición | Unidad | Fuente real en este MVP |
|---|---|---|---|
| Tiempo de sesión | Duración acumulada de las sesiones cerradas | Segundos | `sessions.json` (telemetría simulada) |
| Tiempo de uso activo | Segundos de actividad dentro de esas sesiones | Segundos | `sessions.json` (telemetría simulada) |
| Tiempo de inactividad | Segundos sin actividad dentro de esas sesiones | Segundos | `sessions.json` (telemetría simulada) |

**Limitación esencial:** Microsoft Graph **no proporciona de forma general** duración de sesión, tiempo activo ni tiempo inactivo a través de los tres endpoints elegidos. Un evento `signIn` demuestra una autenticación, **no** cuánto tiempo se utilizó una aplicación. Por tanto, no se calculan tiempos a partir de diferencias entre autenticaciones. La cuarta entrada, `appSessions`, es un **contrato propio**, no un endpoint de Graph. En producción se necesitaría telemetría real o informes específicos del servicio para sustituir ese mock.

### Qué aporta cada grupo a los indicadores

| Grupo | Datos útiles | Relación con los tres KPI |
|---|---|---|
| Aplicaciones | `id` del service principal, `appId`, nombre, estado | Identifica y etiqueta la aplicación a la que se atribuyen los tiempos; **no aporta duraciones** |
| Actividad (`signIns`) | Usuario, aplicación, instante y resultado de autenticación | Permite contar accesos y usuarios con autenticaciones; **no aporta duraciones** |
| Asignaciones | `resourceId`, `principalId`, tipo de identidad | Identifica quién tiene una asignación; **no demuestra uso ni aporta duraciones** |
| Sesiones simuladas (fuente adicional) | `startedAt`, `endedAt`, `activeSeconds`, `idleSeconds` | **Única fuente actual de los tres KPI** |

## 2. Requisitos y decisiones de diseño

### Requisitos funcionales

- Recibir JSON agrupado por aplicaciones, actividad y asignaciones; añadir sesiones simuladas para los indicadores temporales.
- Validar los datos de entrada con Pydantic antes de persistirlos.
- Guardar los datos en SQLite, incluyendo una copia JSON de **cada objeto recibido** (`raw_json`). No se conserva íntegramente el sobre de la petición.
- Reimportar registros por clave estable mediante **upsert**, sin duplicar entidades.
- Conservar un registro de cada lote de importación.
- Exponer inventario y estadísticas mediante endpoints REST.
- Mantener **ingestión y agregación independientes**: importar no recalcula ni materializa estadísticas.
- Calcular los tiempos por aplicación y día en UTC, bajo demanda.

### Decisiones adoptadas

| Aspecto | Decisión MVP |
|---|---|
| Arquitectura | Monolito modular y síncrono |
| Organización | Módulos de aplicaciones, actividad, asignaciones y analytics |
| Base de datos | SQLite con SQLAlchemy 2 |
| Validación | Pydantic v2 |
| Tiempo | Segundos enteros, fechas normalizadas a UTC |
| Actualización | Upsert por `(tenant_id, identificador)` |
| Agregación | Bajo demanda, diaria, separada de la ingestión |
| Sesiones simultáneas | Suma de tiempos por sesión; no deduplicación de solapamientos |
| Sesiones que cruzan medianoche UTC | Rechazadas en la versión 0.1; no se dividen entre días |
| Sesiones abiertas | No admitidas; solo `status="closed"` |
| Asignaciones eliminadas | No se detectan por ausencia en una importación parcial |
| Seguridad | Desarrollo local; sin autenticación propia ni control de acceso implementados |
| Extracción real de Graph | Pendiente; hoy se usan archivos JSON hardcodeados |
| Panel visual | Pendiente; actualmente se expone una API de estadísticas |

**Interpretación de métricas:** las duraciones son *tiempos acumulados de sesiones*, no necesariamente tiempo único de una persona. Una aplicación sin sesiones en un día no aparece en el resultado actual: la ausencia de datos **no equivale a cero uso real**.

## 3. Endpoints necesarios de Microsoft Graph (integración futura)

Los siguientes son los recursos externos que alimentarán los tres grupos; **no se consultan desde el código actual**.

| Grupo | Microsoft Graph v1.0 | Propósito | Relación en el modelo |
|---|---|---|---|
| Aplicaciones | `GET https://graph.microsoft.com/v1.0/servicePrincipals` | Inventario de aplicaciones empresariales | `servicePrincipal.id` -> `applications.sp_id`; `appId` -> `applications.app_id` |
| Actividad | `GET https://graph.microsoft.com/v1.0/auditLogs/signIns` | Histórico de autenticaciones | `signIn.appId` -> `sign_in_events.app_id` |
| Asignaciones | `GET https://graph.microsoft.com/v1.0/servicePrincipals/{id}/appRoleAssignedTo` | Asignaciones para cada service principal | `appRoleAssignment.resourceId` -> `applications.sp_id` |

**Campos principales:**

- **Aplicaciones:** `id`, `appId`, `displayName`, `accountEnabled` (otros atributos de Graph pueden mantenerse en `raw_json`).
- **Actividad:** `id`, `appId`, `userId`, `createdDateTime`, `status.errorCode` (otros atributos quedan en `raw_json`).
- **Asignaciones:** `id`, `resourceId`, `principalId`, `principalType` (otros atributos quedan en `raw_json`).

Para una futura conexión con permisos de **aplicación**, revisar en Microsoft Graph los permisos y el consentimiento administrativo adecuados, normalmente `Application.Read.All` para inventario, `AuditLog.Read.All` para registros y `AppRoleAssignment.Read.All` para asignaciones. Los requisitos concretos pueden depender del endpoint, la modalidad de acceso y las licencias del tenant. El rol humano `Application Administrator` no sustituye automáticamente estos permisos.

**Consideraciones de extracción real:** autenticación OAuth 2.0, paginación mediante `@odata.nextLink`, filtrado temporal de `signIns`, límites de solicitudes, retención y licencias de logs, reintentos, privacidad y tratamiento de asignaciones a grupos. El MVP **no** implementa estas funciones. Los JSON de ejemplo utilizan identificadores ficticios y no necesariamente GUID reales de Graph.

Documentación oficial:

- [List servicePrincipals](https://learn.microsoft.com/en-us/graph/api/serviceprincipal-list?view=graph-rest-1.0)
- [List signIns](https://learn.microsoft.com/en-us/graph/api/signin-list?view=graph-rest-1.0)
- [List appRoleAssignedTo](https://learn.microsoft.com/en-us/graph/api/serviceprincipal-list-approleassignedto?view=graph-rest-1.0)

## 4. Arquitectura de software y responsabilidades

```text
mocks/*.json
    |
    v
FastAPI routers -> Pydantic schemas -> app/ingestion.py -> SQLAlchemy -> SQLite
                                              
GET statistics -> app/analytics/router.py -> app/analytics/service.py -> SQLite (solo lectura)
```

La separación es deliberadamente simple. **La versión implementada** utiliza un servicio de ingestión compartido y modelos SQLAlchemy compartidos; **no** incorpora todavía archivos `service.py` y `repository.py` en cada dominio.

```text
graph_mvp/
├── app/
│   ├── main.py                 # Inicializa FastAPI, rutas, /health y lotes
│   ├── database.py             # Motor SQLite y sesiones de BD
│   ├── models.py               # Cinco modelos SQLAlchemy
│   ├── schemas.py              # Modelos Pydantic y validación de sesiones
│   ├── ingestion.py            # Upsert, transacciones y registro de lotes
│   ├── applications/router.py  # Ingestión y listado de aplicaciones
│   ├── activity/router.py      # Ingestión de signIns y sesiones
│   ├── assignments/router.py   # Ingestión de asignaciones
│   └── analytics/
│       ├── router.py           # API de estadísticas
│       └── service.py          # Agregación diaria, sin escrituras
├── mocks/
│   ├── applications.json
│   ├── sign_ins.json
│   ├── assignments.json
│   └── sessions.json
├── tests/                      # Directorio reservado; sin pruebas incluidas
├── requirements.txt
└── README.md
```

**Regla de responsabilidades:** routers gestionan HTTP; schemas validan; `ingestion.py` persiste; `analytics/service.py` calcula. No hay microservicios, colas, workers, scheduler, caché ni tablas de agregados.

## 5. Librerías utilizadas

| Librería | Versión declarada | Función |
|---|---|---|
| `fastapi` | `>=0.115,<1` | API REST, rutas, dependencias y Swagger/OpenAPI |
| `uvicorn` | `>=0.30,<1` | Servidor ASGI para ejecutar FastAPI |
| `pydantic` | `>=2,<3` | Validación y serialización de JSON |
| `sqlalchemy` | `>=2,<3` | ORM, sesiones y operaciones sobre SQLite |
| `pytest` | `>=8,<10` | Dependencia para pruebas futuras |
| `httpx` | `>=0.27,<1` | Cliente HTTP, previsto para pruebas de API |
| `sqlite3` | Biblioteca estándar de Python (vía SQLAlchemy) | Motor local de persistencia |

No se utiliza el SDK de Microsoft Graph, MSAL, pandas, Celery ni un framework frontend en esta versión.

## 6. Requisitos de ejecución

- Python **3.10 o superior** (recomendado 3.11 o 3.12).
- `pip` y `venv` disponibles.
- Sistema operativo Linux, macOS o Windows.
- Puerto local `8000` libre.
- **No** se necesita conexión a un tenant, credenciales Microsoft ni acceso a internet para ejecutar los mocks una vez instaladas las dependencias.

### Instalación en Linux / macOS

Desde la carpeta `graph_mvp`:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

En Windows PowerShell, activar con `.venv\Scripts\Activate.ps1` y ejecutar los mismos comandos de instalación y arranque.

El archivo `graph_mvp.db` se crea en el directorio de trabajo al iniciar la aplicación (si no existe). La ruta se puede configurar mediante la variable `DATABASE_URL`.

### Comprobar el servicio

- Swagger UI: http://127.0.0.1:8000/docs
- OpenAPI: http://127.0.0.1:8000/openapi.json
- Salud: http://127.0.0.1:8000/health

```bash
curl http://127.0.0.1:8000/health
# {"status":"ok"}
```

## 7. Contratos JSON y datos simulados

Cada endpoint de ingestión recibe un **sobre propio del MVP**:

```json
{
  "tenantId": "tenant-demo-001",
  "source": "graph_mock",
  "resource": "signIns",
  "value": [
    {
      "id": "signin-001",
      "appId": "app-teams-001",
      "userId": "user-001",
      "createdDateTime": "2026-11-18T08:00:00Z",
      "status": { "errorCode": 0 }
    }
  ]
}
```

`tenantId`, `source` y `resource` son metadatos del **contrato de ingestión local**; no deben confundirse con la estructura literal de la respuesta HTTP de Graph. Los registros de Graph admiten campos adicionales y el MVP los conserva en el JSON de cada objeto.

| Archivo | `resource` esperado | `source` de ejemplo | Endpoint local |
|---|---|---|---|
| `applications.json` | `applications` o `servicePrincipals` | `graph_mock` | `/api/ingest/applications` |
| `sign_ins.json` | `signIns` | `graph_mock` | `/api/ingest/signins` |
| `assignments.json` | `appRoleAssignedTo` | `graph_mock` | `/api/ingest/assignments` |
| `sessions.json` | `appSessions` | **`telemetry_mock` obligatorio** | `/api/ingest/sessions` |

Ejemplo de sesión propia:

```json
{
  "sessionId": "session-001",
  "appId": "app-teams-001",
  "userId": "user-001",
  "startedAt": "2026-11-18T08:00:00Z",
  "endedAt": "2026-11-18T10:00:00Z",
  "activeSeconds": 5400,
  "idleSeconds": 1800,
  "status": "closed"
}
```

Reglas de validación de sesión: timestamps con zona horaria, duración positiva en segundos enteros, `activeSeconds >= 0`, `idleSeconds >= 0`, suma de activo e inactivo igual a duración, sesión cerrada y sin cruzar fechas UTC. Un JSON incorrecto devuelve error de validación HTTP 422.

## 8. Uso paso a paso: importar y consultar

Con el servidor arrancado, desde `graph_mvp/`:

```bash
# 1. Inventario de aplicaciones
curl -X POST http://127.0.0.1:8000/api/ingest/applications \
  -H 'Content-Type: application/json' \
  --data-binary @mocks/applications.json

# 2. Actividad de autenticación
curl -X POST http://127.0.0.1:8000/api/ingest/signins \
  -H 'Content-Type: application/json' \
  --data-binary @mocks/sign_ins.json

# 3. Asignaciones de aplicaciones
curl -X POST http://127.0.0.1:8000/api/ingest/assignments \
  -H 'Content-Type: application/json' \
  --data-binary @mocks/assignments.json

# 4. Telemetría simulada de sesiones (necesaria para los tres KPI)
curl -X POST http://127.0.0.1:8000/api/ingest/sessions \
  -H 'Content-Type: application/json' \
  --data-binary @mocks/sessions.json

# 5. Consultar aplicaciones
curl 'http://127.0.0.1:8000/api/applications?tenant_id=tenant-demo-001'

# 6. Consultar KPI por aplicación y día
curl 'http://127.0.0.1:8000/api/statistics/applications?tenant_id=tenant-demo-001&date=2026-11-18'

# 7. Consultar una aplicación
curl 'http://127.0.0.1:8000/api/statistics/applications/app-teams-001?tenant_id=tenant-demo-001&date=2026-11-18'

# 8. Consultar historial de importaciones
curl 'http://127.0.0.1:8000/api/ingestion/batches?tenant_id=tenant-demo-001'
```

Las rutas `/api/...` son **endpoints de nuestra API FastAPI**, no endpoints de Microsoft Graph. Los parámetros `tenant_id` y `date` son obligatorios donde aparecen.

### Endpoints disponibles

| Método | Ruta | Responsabilidad |
|---|---|---|
| `POST` | `/api/ingest/applications` | Importar aplicaciones |
| `POST` | `/api/ingest/signins` | Importar autenticaciones |
| `POST` | `/api/ingest/assignments` | Importar asignaciones |
| `POST` | `/api/ingest/sessions` | Importar sesiones simuladas |
| `GET` | `/api/applications` | Listar aplicaciones de un tenant |
| `GET` | `/api/statistics/applications` | Agregado diario de todas las apps con sesiones |
| `GET` | `/api/statistics/applications/{app_id}` | Agregado diario filtrado por `app_id` |
| `GET` | `/api/ingestion/batches` | Historial de lotes |
| `GET` | `/health` | Comprobación de servicio |

La respuesta de ingestión incluye `batchId`, `inserted`, `updated` y `rejected`. Una reimportación idéntica actualiza registros existentes y crea un nuevo registro de lote; **no** crea filas duplicadas de negocio.

## 9. Base de datos SQLite

Se crean automáticamente estas **cinco tablas**:

| Tabla | Contenido | Clave primaria |
|---|---|---|
| `applications` | Aplicaciones empresariales | `(tenant_id, sp_id)` |
| `sign_in_events` | Eventos de autenticación | `(tenant_id, event_id)` |
| `app_assignments` | Asignaciones de acceso | `(tenant_id, assignment_id)` |
| `app_sessions` | Sesiones simuladas y duraciones | `(tenant_id, session_id)` |
| `ingestion_batches` | Auditoría básica de importaciones | `batch_id` |

Las cuatro tablas de datos incluyen `raw_json` con el objeto de origen. Las relaciones se resuelven por `appId` y `resourceId` según el recurso, sin imponer claves foráneas entre todas las tablas. Los datos de autenticación y asignaciones **no se transforman automáticamente en sesiones**.

## 10. Cómo se calculan los tres indicadores

Para cada sesión cerrada:

```text
sessionSeconds = (endedAt - startedAt) en segundos
sessionSeconds = activeSeconds + idleSeconds
```

Para cada aplicación y fecha UTC:

```text
sessionSeconds(app, día) = suma de duración de sus sesiones
activeSeconds(app, día)  = suma de activeSeconds de sus sesiones
idleSeconds(app, día)    = suma de idleSeconds de sus sesiones
activePercentage         = 100 * activeSeconds / sessionSeconds
```

Si `sessionSeconds = 0`, `activePercentage` se define como `null`. La agregación actual consulta únicamente `app_sessions` y no modifica la base de datos. Como las sesiones del MVP no pueden cruzar medianoche UTC, cada sesión pertenece a un único día.

**Ejemplo:** una sesión de Teams de 08:00 a 10:00 con 5.400 segundos activos y 1.800 inactivos genera:

| KPI | Segundos | Visualización sugerida |
|---|---:|---:|
| Tiempo de sesión | 7.200 | 120 min |
| Uso activo | 5.400 | 90 min |
| Inactividad | 1.800 | 30 min |

La respuesta del endpoint `/api/statistics/applications` contiene `date`, `timezone`, `source` y `applications`, con `appId`, `displayName`, `sessionCount`, `sessionSeconds`, `activeSeconds`, `idleSeconds` y `activePercentage` para cada aplicación que tenga sesiones.

**Importante:** si se importan solamente los tres grupos Graph, el inventario y los eventos quedan guardados, pero la consulta de KPI temporales no tendrá resultados hasta importar sesiones simuladas.

## 11. Limitaciones y evolución prevista

**No implementado:** cliente Graph real, obtención de tokens, sincronización incremental, paginación, conciliación de asignaciones eliminadas, resolución de pertenencia a grupos, telemetría real, frontend, pruebas automatizadas incluidas, autenticación propia, autorización, retención de datos, migraciones y división de sesiones entre días.

**Siguiente evolución recomendada:** conectar los tres endpoints Graph para reemplazar `graph_mock` por datos reales **sin alterar el módulo de estadísticas**; mantener `appSessions` separado hasta contar con una fuente fiable de duración y actividad. Si el objetivo posterior es analizar actividad real de Microsoft 365, estudiar informes específicos de cada producto, diferenciando sus métricas de las duraciones de sesión.

**Privacidad y seguridad:** el MVP está pensado para datos ficticios y ejecución local. No se debe exponer en una red pública ni cargar información personal de producción sin autenticación, autorización, controles de acceso, políticas de conservación y revisión de requisitos de protección de datos.
