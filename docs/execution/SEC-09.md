# SEC-09 — Secret scan, SCA y SBOM

Inicio: 2026-10-06; base `f0ed73c`. Estado: **Done como auditoría**, resultado de seguridad **NO APTO para release**.

Dependencia: ENV-03 ofrece lock reproducible; el smoke ML sigue bloqueado. Se ejecuta auditoría sobre versiones resueltas sin esperar entrenamiento, sin dar por completado ENV-03.

Alcance: Gitleaks 8.30.1, binario verificado contra checksum del release oficial; historial de refs locales alcanzables con `git --log-opts=--all` y snapshot de archivos versionados/por versionar según `git ls-files --cached --others --exclude-standard`. Ambos scans con redacción 100%: cero coincidencias. Se excluyen entornos, herramientas, metadatos y otros archivos ignorados; no se auditan secretos fuera del repositorio, refs remotas no descargadas ni archivos ignorados. Reportes vacíos en `docs/security/evidence/secrets-*.json`.

SCA: `pip-audit` 2.10.1 no puede consultar HTTPS por bloqueo de `_ssl`. Fallback reproducible `scripts/audit_dependencies.ps1` consulta con TLS el API oficial de cada release PyPI, sin ejecutar paquetes. Consultadas 73 dependencias, cero consultas fallidas. SBOM CycloneDX 1.5 con componentes/purl en `sbom.cdx.json`; reporte y hash del listado en `sca-pypi.json`. No se atribuye a pip-audit el resultado de este fallback ni se garantiza exhaustividad de avisos.

Hallazgos: scikit-learn 1.4.2 afectado por [CVE-2024-5206](https://github.com/advisories/GHSA-jw8x-6495-233v), corregido al fijar 1.5.2 y regenerar/sincronizar lock. `sca-baseline.json` conserva el hallazgo previo. Protobuf 4.25.9 afectado por [CVE-2026-0994, severidad alta](https://github.com/advisories/GHSA-7gcm-g887-7qv7); permanece abierto. Las versiones corregidas 5.29.6/6.33.5 no caben en la restricción protobuf <5 de la pila MediaPipe/TensorFlow actual. No forzar una dependencia incompatible ni silenciar el aviso: requiere migración de pila con pruebas, deuda SEC-DEBT-01.

Validación: SCA posterior consulta 73 paquetes y solo protobuf tiene avisos (dos IDs representan el mismo CVE); salida 1 indica hallazgo, no fallo del escáner. `uv pip sync` instala scikit-learn 1.5.2. Auditoría completada no implica VAL-05 aprobado: cero vulnerabilidades altas/críticas aún no se cumple.

Límites: no exposición remota, certificación, aprobación de release o rotación de secretos (ninguno confirmado). Repetir scans y SCA para cada candidato; las evidencias corresponden a este inicio y archivos actuales, no a todos los commits futuros.
