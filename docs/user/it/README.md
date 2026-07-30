# LocalMES — Guida utente (Italiano)

## Installazione

1. Installa Python 3.10+ e Node.js 18+
2. Avvia `scripts/start.bat` (Windows) o `scripts/start.sh` (Linux/macOS)
3. Apri http://localhost:3000
4. Accedi con `admin` / `admin` e cambia la password

Oppure con Docker: `docker compose up --build` poi http://localhost:8000

## Prima configurazione

1. **Impostazioni** (superadmin): imposta `backup_dir`, attiva il backup se serve
2. Crea **gruppi linea** e **linee**
3. Crea operazioni di catalogo via API `/api/v1/operations` oppure esegui:
   `python app/backend/scripts/seed_demo.py`
4. Crea **clienti** e **prodotti**
5. Crea una **commessa**, aggiungi righe, genera **ordini di produzione**
6. In **Operativo** avvia / pausa / chiudi le operazioni

## Import

In Impostazioni → Import carica CSV/Excel (clienti, prodotti, distinte, ordini).
Template in `/templates`.

## Report

Impostazioni → Report: export Excel o PDF (serve sessione attiva).

## Integrazioni API

- Documentazione (dev): http://localhost:8000/docs
- Crea una API key in Impostazioni
- Header `X-API-Key: mes_...` oppure `Authorization: Bearer mes_...`
