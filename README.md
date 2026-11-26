# customer-api-pipeline

A small customer API (Python, FastAPI, PostgreSQL) and a .NET integration EXE,
delivered by a GitHub Actions CI/CD pipeline to three Azure environments and a
private Windows VM.

The API is the sample application. The point of the project is the pipeline:
every change is tested and packaged once, and only `main` is deployed, through
test, UAT and production, with approvals and health checks at each stage.

## Pipeline

```
push / pull request (any branch)
  ├─ build               tests against a throwaway PostgreSQL, packages api.zip
  └─ build-integration   publishes the .NET EXE for Windows

push to main only
  build ─> deploy-test ─> deploy-uat* ─> deploy-production* ─> deploy-vm*
                                                (staging slot, swap, rollback)
* waits for a required reviewer
```

Every Web App deploy: download the package, log in to Azure (OIDC, no password),
open the database firewall for the runner, update the tables (`db/schema.sql`),
deploy the zip, check `/health`, close the firewall (always, even on failure).

Production deploys to a staging slot, checks it, swaps it live, checks again, and
swaps back if the post-swap check fails.

The VM has no public IP. A self-hosted runner on the VM polls GitHub over
outbound HTTPS (through a NAT gateway) and runs `deploy/deploy-vm.ps1`: stop,
back up, copy, start, health check, roll back on failure.

## Controls

| Control | Where | Effect |
|---|---|---|
| Deploy jobs only on push to `main` | `ci.yml` (`if:`) | Branches and pull requests are built and tested, never deployed |
| Ruleset `protect-main` | Settings > Rules | `main` changes only through a pull request with a passing `build`; no force push or deletion |
| Environments `uat`, `production`, `vm` | Settings > Environments | Required reviewer and `main`-only deployment; set outside the YAML so it cannot be edited away |
| One managed identity per environment | Azure | Contributor on its own resource group only; federated credential trusts only this repo + environment |
| Secrets | GitHub environment secrets, app settings | No secret in the repo; the connection string is read from `DATABASE_URL` |

## Repository layout

```
app/main.py               API endpoints
app/db.py                 database connection (reads DATABASE_URL)
db/schema.sql             customers table, safe to re-run
tests/                    pytest tests (11); conftest.py empties the table before each test
requirements.txt          Python packages
.github/workflows/ci.yml  the pipeline
integration/              .NET 8 console EXE, stand-in for a real integration
deploy/deploy-vm.ps1      VM deploy with backup and rollback
deploy/install-runner.ps1 one-time runner install on the VM
```

## API

| Method | Path | Result |
|---|---|---|
| GET | `/health` | 200 if the app can reach its database, else 503 |
| POST | `/customers` | 201 created, 409 email already used, 422 invalid body |
| GET | `/customers` | active customers only |
| PUT | `/customers/{id}` | 200, 404 unknown id, 409 email taken |
| POST | `/customers/{id}/deactivate` | soft delete (row kept, marked inactive) |
| POST | `/customers/{id}/activate` | undo deactivate |

Interactive docs at `/docs` on any running instance.

## Run locally

Requires Python 3.12 and PostgreSQL.

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
psql -d customers_dev -f db/schema.sql

$env:DATABASE_URL = "postgresql://<user>:<password>@localhost:5432/customers_dev"
uvicorn app.main:app --reload        # http://127.0.0.1:8000/docs

# tests need a database whose name ends in _test
$env:DATABASE_URL = "postgresql://<user>:<password>@localhost:5432/customers_test"
python -m pytest
```

## Known limitations

- Azure resources were created with the CLI and portal, not Infrastructure as Code (Bicep or Terraform).
- Secrets are in GitHub environment secrets and app settings, not Azure Key Vault.
- One PostgreSQL server holds all three databases, so environment isolation stops at the database server.
- The VM runner and the integration task run as SYSTEM; a real setup would use a low-privilege account.
- `db/schema.sql` only creates the table; changing existing columns would need a migration tool.
- `requirements.txt` is a full `pip freeze` saved as UTF-16; it should list only direct dependencies in UTF-8.
