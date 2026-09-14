for backend, use uv for dependency management. A few useful commands:

uv sync
uv add <PACKAGE-NAME>
uv run python <PYTHON-FILE>

for frontend, use npm for dependency management and scripts. Useful commands:

cd frontend
npm install
npm run dev
npm test
npm run build

architecture & guidelines:
- frontend runs completely standalone via a centralized mock service layer (see `frontend/src/services/mockService.ts` and `frontend/src/services/index.ts`).
- to point the frontend to a real backend, set `VITE_USE_MOCK=false` and provide `VITE_API_BASE_URL` / `VITE_WS_BASE_URL`.
- specs and functional requirements are located in `_docs/specs.md`, `_docs/frontend_specs.md`, and `_docs/backend_specs.md`.

regularly commit code to git 