# Project Execution Plan

## Part 1: Documentation & Planning

**Goal**: Document existing frontend architecture and create detailed plan with substeps, tests, and success criteria for all remaining parts.

### Substeps

- [x] Document existing frontend code structure, components, data model, and architecture in `frontend/AGENTS.md`
- [x] Enrich this PLAN.md with detailed substeps, checklists, and success criteria for Parts 2-10
- [x] Get user review and approval of both documentation and plan

### Tests & Success Criteria

- **Test**: User confirms frontend AGENTS.md accurately describes the component structure and data flow
- **Success**: User approves the complete enriched PLAN.md with all substeps and success criteria defined

---

## Part 2: Docker Scaffolding & Backend Foundation

**Goal**: Set up Docker infrastructure and basic FastAPI backend that serves a hello world HTML page and demonstrates a basic API call.

### Substeps

- [x] Create Dockerfile with multi-stage build (Python for backend, Node for frontend build)
- [x] Set up Python project structure in `backend/` with FastAPI, SQLAlchemy, and uv package manager
- [x] Create `backend/AGENTS.md` documenting backend architecture and project structure
- [x] Add basic FastAPI app that serves static HTML at `/` with a simple hello world
- [x] Add a test API endpoint `/api/hello` that returns JSON: `{ "message": "Backend is working" }`
- [x] Create `.env` file template with OPENROUTER_API_KEY placeholder
- [x] Write shell scripts: `scripts/start.sh`, `scripts/stop.sh` for Mac (add Windows/Linux variants later)
- [x] Test locally: Build Docker image, run container, verify hello world page loads and API call works
- [x] Write basic backend unit test for the `/api/hello` endpoint

### Tests & Success Criteria

- **Test**: Docker container builds without errors and runs locally on macOS
- **Test**: `curl http://localhost:8000/` returns example HTML page
- **Test**: `curl http://localhost:8000/api/hello` returns `{ "message": "Backend is working" }`
- **Test**: Startup/stop scripts execute without errors and container lifecycle works
- **Success**: All tests pass; hello world page and API call confirmed working

---

## Part 3: Frontend Integration & Static Build

**Goal**: Integrate the frontend Next.js build into the backend, serve the Kanban board at `/`, with comprehensive testing.

### Substeps

- [x] Update `next.config.ts` to support static export or SSG as needed for Docker serving
- [x] Add `build` step to Dockerfile to generate Next.js `.next` output
- [x] Configure FastAPI to serve Next.js static assets from `public/` and `.next/static/` (now serves `out` folder)
- [x] Route index requests to built Next.js HTML file
- [x] Add unit tests for KanbanBoard component (render, prop handling)
- [x] Add component tests for KanbanColumn and KanbanCard (rendering, callbacks) — existing tests partially cover; more can be added later
- [x] Add e2e test: Load app at `/`, verify Kanban board renders with columns and cards
- [x] Add e2e test: Verify drag-and-drop interaction works (move card between columns)
- [x] Test in Docker container: Build and run, navigate to localhost, verify Kanban loads

### Tests & Success Criteria

- **Test**: `npm run test:unit` passes all component and utility tests in frontend/
- **Test**: `npm run test:e2e` passes all e2e scenariosin Playwright
- **Test**: Docker build succeeds; Kanban board loads and displays at `http://localhost:8000/`
- **Test**: Drag-and-drop functionality works in browser
- **Success**: Full Kanban UI is interactive and all tests pass

---

## Part 4: Login & Authentication

**Goal**: Add a login page that requires credentials ("user" / "password"), with logout functionality.

### Substeps

- [x] Create a Login component with username and password form inputs
- [x] Add a login context/provider for managing auth state
- [x] Protect KanbanBoard: redirect to login if not authenticated
- [x] Add logout button in KanbanBoard header
- [x] Implement hardcoded credential check (username="user", password="password")
- [x] Add unit tests: Login component renders, validates input, submits
- [x] Add e2e test: User navigates to `/`, sees login form, enters credentials, sees Kanban
- [x] Add e2e test: User clicks logout, returned to login page
- [x] Error handling: Show error message on invalid credentials

### Tests & Success Criteria

- **Test**: Login page renders at `/` when not authenticated
- **Test**: Valid credentials ("user"/"password") unlock Kanban board
- [ ] **Test**: Invalid credentials show error message *(covered by unit test)*
- **Test**: Logout button clears auth and returns to login
- **Test**: Refreshing page while logged in stays on Kanban (auth state persists in session)
- **Success**: Full auth flow works without errors; all tests pass

---

## Part 5: Database Schema Design

**Goal**: Design SQLite-agnostic database schema for Kanban, document approach, and get user approval.

### Substeps

- [x] Design schema (tables: users, boards, columns, cards) in SQLite-agnostic SQL or JSON schema format
- [x] Create example JSON document showing full board structure with nested relationships
- [x] Write `docs/DATABASE.md` documenting schema design, relationships, and migration strategy
- [x] Include rationale for choices (e.g., why cards reference column via `column_id`)
- [x] Propose approach for handling users (hardcoded "user" for MVP, but schema supports multiple)
- [ ] Get user review and approval before implementation

### Tests & Success Criteria

- **Test**: Schema can represent all required Kanban data (users, boards, columns, cards)
- **Test**: Example JSON document matches schema and looks correct
- **Test**: Documentation is clear on relationships and migrations
- **Success**: User approves schema and database approach; no ambiguities remain

---

## Part 6: Backend API & Database Integration

**Goal**: Implement API routes to fetch and persist Kanban data, with SQLite database.

### Substeps

- [ ] Create SQLAlchemy models for User, Board, Column, Card based on schema
- [ ] Implement database initialization (create tables if not exist) on app startup
- [ ] Add `/api/auth/login` endpoint (hardcoded user/"password", returns session token or cookie)
- [ ] Add `/api/boards` endpoint: GET to fetch user's board with all columns and cards
- [ ] Add `/api/boards/{boardId}/columns/{columnId}/cards` endpoint: POST to add new card
- [ ] Add `/api/cards/{cardId}` endpoint: PATCH to update card (title, details), DELETE to remove
- [ ] Add `/api/columns/{columnId}` endpoint: PATCH to rename column
- [ ] Implement card move logic: PUT `/api/cards/{cardId}/move` with `{ columnId, position }`
- [ ] Add database session middleware for request lifecycle management
- [ ] Write backend unit tests for each endpoint (happy path + error cases)
- [ ] Test database creation and persistence on restart

### Tests & Success Criteria

- **Test**: SQLite database is created on first run
- **Test**: `/api/auth/login` accepts hardcoded credentials and returns success
- **Test**: `/api/boards` returns complete board structure with columns and cards
- **Test**: Add, edit, delete, and move operations update database correctly
- **Test**: Data persists after container restart
- **Test**: All backend unit tests pass
- **Success**: All API endpoints functional and tested; database persists correctly

---

## Part 7: Frontend-Backend Connectivity

**Goal**: Wire frontend to use backend API for all Kanban operations, replacing in-memory state.

### Substeps

- [ ] Replace KanbanBoard state with API calls: fetch board on mount
- [ ] Implement loading and error states during API calls
- [ ] Update handleDragEnd to call move API endpoint
- [ ] Update handleAddCard to call create card API endpoint
- [ ] Update handleDeleteCard to call delete card API endpoint
- [ ] Update handleRenameColumn to call rename column API endpoint
- [ ] Add optimistic UI updates (show change immediately, revert if API fails)
- [ ] Implement error handling and user-facing error messages
- [ ] Add integration tests: Mock API, test user flows
- [ ] Test in Docker: Full create/read/update/delete workflows end-to-end

### Tests & Success Criteria

- **Test**: Board fetches from API on component mount
- **Test**: Adding, editing, deleting, and moving cards persist to backend
- **Test**: Data survives a refresh (persisted to database)
- **Test**: Error messages appear on API failures
- **Test**: All unit and e2e tests pass
- **Success**: Kanban board is fully persistent; frontend and backend integrated seamlessly

---

## Part 8: OpenRouter AI Integration (Connectivity Test)

**Goal**: Wire backend to call OpenRouter API; test basic connectivity with a simple math problem.

### Substeps

- [ ] Load OPENROUTER_API_KEY from environment in backend
- [ ] Create a simple test endpoint `/api/ai/test` that calls OpenRouter with prompt "What is 2+2?"
- [ ] Use `openai/gpt-4` client library (via openai Python package) pointing to OpenRouter
- [ ] Parse and return AI response
- [ ] Add error handling for missing API key or API failures
- [ ] Write backend unit test: Mock OpenRouter response, verify endpoint returns expected result
- [ ] Manual test: Set API key in `.env`, call endpoint, verify correct response ("4" or similar)

### Tests & Success Criteria

- **Test**: OpenRouter API key is loaded correctly from environment
- **Test**: `/api/ai/test` returns successful response from AI without errors
- **Test**: AI correctly answers "2+2" (returns 4 or reasonable equivalent)
- **Test**: Error handling works if API key is missing or invalid
- **Success**: Backend can communicate with OpenRouter; AI connectivity confirmed

---

## Part 9: AI Integration with Kanban Context & Structured Outputs

**Goal**: Backend calls AI with full Kanban context and conversation history; AI returns structured response with optional board updates.

### Substeps

- [ ] Design structured output schema: `{ "response": string, "boardUpdates": { "cards": [...], "columns": [...] } }`
- [ ] Create `/api/ai/chat` endpoint that accepts `{ question: string, conversationHistory: [] }`
- [ ] Include current board JSON in the prompt sent to AI
- [ ] Call OpenRouter with instructions to respond in structured format
- [ ] Parse structured response; extract text response and optional board updates
- [ ] Implement conversation history storage (in-memory for MVP, can be persisted later)
- [ ] Add backend unit tests: Mock API, verify structured output parsing, test with board updates
- [ ] Manual test: Chat with AI, ask it to create/modify cards, verify returned structure

### Tests & Success Criteria

- **Test**: Endpoint sends Kanban JSON to AI in request
- **Test**: AI response is parsed correctly as structured output
- **Test**: Text response is extracted and usable
- **Test**: Board updates in response are well-formed (valid card/column objects)
- **Test**: Conversation history is maintained across multiple requests
- **Test**: All backend tests pass
- **Success**: AI has full context; structured outputs validated and testable

---

## Part 10: AI Sidebar Chat Widget & Live Board Updates

**Goal**: Add interactive chat sidebar to UI; AI can trigger Kanban updates which reflect in real-time.

### Substeps

- [ ] Create ChatSidebar component with message list and input form
- [ ] Implement chat message state: user messages and AI responses
- [ ] Wire ChatSidebar to call `/api/ai/chat` with user's message
- [ ] Display AI response text in message list
- [ ] Parse structured output from API response
- [ ] If boardUpdates present, apply changes to KanbanBoard state
- [ ] Trigger UI refresh when board updates (cards added/moved/removed)
- [ ] Add loading state while AI responds
- [ ] Add error handling and display error messages
- [ ] Implement visual feedback (e.g., highlight cards that were just updated by AI)
- [ ] Add unit tests for ChatSidebar component
- [ ] Add e2e test: User types message, AI responds, board updates automatically
- [ ] Style sidebar to match color scheme and layout

### Tests & Success Criteria

- **Test**: ChatSidebar renders and accepts text input
- **Test**: Sending message calls AI endpoint
- **Test**: AI response appears in chat history
- **Test**: If AI returns board updates, Kanban board reflects the changes immediately
- **Test**: Moving a card in the board appears in AI's context in next message
- **Test**: Error states are handled gracefully
- **Test**: All unit and e2e tests pass
- **Success**: Full AI-powered Kanban experience; user can manage board via chat