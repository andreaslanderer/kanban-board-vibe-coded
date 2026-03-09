# Frontend Architecture

## Overview

The frontend is a Next.js 16 application providing a fully interactive Kanban board. It uses client-side React state management with drag-and-drop functionality via dnd-kit library. All data is currently stored in client memory (no backend connection yet).

## Tech Stack

- **Framework**: Next.js 16.1.6 with React 19.2.3
- **Styling**: Tailwind CSS 4 with custom CSS variables
- **Drag & Drop**: dnd-kit (core, sortable, utilities)
- **Testing**: Vitest (units), Playwright (e2e), Testing Library (React)
- **Fonts**: Space Grotesk (display), Manrope (body) from Google Fonts

## Directory Structure

```
src/
  app/
    layout.tsx       - Root layout with font setup and metadata
    page.tsx         - Home page entry point
    globals.css      - Global styles and CSS variables
  components/
    KanbanBoard.tsx  - Main board container, drag/drop orchestration
    KanbanColumn.tsx - Column component with sortable context
    KanbanCard.tsx   - Individual card with drag handle
    KanbanCardPreview.tsx - Preview shown during drag
    NewCardForm.tsx  - Add card form (per column)
  lib/
    kanban.ts        - Type definitions and board utilities
  test/
    setup.ts         - Vitest configuration
    vitest.d.ts      - Type definitions for Vitest
tests/
  kanban.spec.ts     - E2E tests with Playwright
```

## Core Components

### KanbanBoard
- **Responsibility**: Main orchestrator for the entire board
- **State**: Board data (columns + cards), active card during drag
- **Features**: 
  - Manages dnd-kit drag/drop context with PointerSensor (6px activation distance)
  - Handlers for: drag start/end, column rename, add card, delete card
  - Renders all columns with background gradient overlays
- **Props**: None (self-contained with useState)
- **Key Dependencies**: DndContext, KanbanColumn, KanbanCardPreview

### KanbanColumn
- **Responsibility**: Single column container with card list
- **State**: Controlled by KanbanBoard parent
- **Features**:
  - Editable column title (inline input)
  - Card count display
  - Drop target (visual ring on hover when over)
  - Vertical sortable context for cards within column
  - NewCardForm at bottom
- **Props**: column, cards[], onRename, onAddCard, onDeleteCard
- **Key Dependencies**: useDroppable, SortableContext, KanbanCard, NewCardForm

### KanbanCard
- **Responsibility**: Individual task card
- **State**: None (fully controlled)
- **Features**:
  - Draggable with transform animations
  - Title and details text
  - Delete button (removes from column)
  - Opacity change during drag
- **Props**: card, onDelete
- **Key Dependencies**: useSortable, CSS utilities from dnd-kit

### KanbanCardPreview
- **Responsibility**: Visual preview of card being dragged
- **State**: None (controlled by KanbanBoard)
- **Features**: Rendered inside DragOverlay for smooth drag preview
- **Props**: card (or null if nothing active)

### NewCardForm
- **Responsibility**: Form to add new cards to a column
- **State**: Form input values (title, details)
- **Features**: Submit handler with validation
- **Props**: onAdd callback
- **Key Dependencies**: None

## Data Model

Located in `lib/kanban.ts`:

```typescript
type Card = {
  id: string;        // e.g., "card-1"
  title: string;     // Task name
  details: string;   // Task description
};

type Column = {
  id: string;           // e.g., "col-backlog"
  title: string;        // Column name (user-editable)
  cardIds: string[];    // Array of card IDs in this column
};

type BoardData = {
  columns: Column[];      // Fixed list of columns (initial: Backlog, Discovery, In Progress, Review, Done)
  cards: Record<string, Card>;  // Card lookup by ID
};
```

## Styling

CSS variables defined in `globals.css`:
- `--font-display`: Space Grotesk
- `--font-body`: Manrope
- `--accent-yellow`: #ecad0a
- `--primary-blue`: #209dd7
- `--secondary-purple`: #753991
- `--navy-dark`: #032147
- `--gray-text`: #888888
- `--stroke`: Border color (light)
- `--surface-strong`: Column background (light)
- `--shadow`: Consistent shadow value

All responsive via Tailwind classes; breakpoints: mobile-first (default), md, lg, xl.

## Testing Structure

### Unit Tests (Vitest)
- `lib/kanban.test.ts` - Utility function tests (moveCard, helpers)
- `components/*.test.tsx` - Component rendering and interaction tests

### E2E Tests (Playwright)
- `tests/kanban.spec.ts` - Full user workflows (drag/drop, edit, add/remove)

## Limitations (MVP)

- All state is in-memory; no persistence
- No login/authentication UI yet
- No backend connectivity yet (API calls come in later parts)
- No AI chat sidebar yet
- Columns are fixed at initialization (5 default columns)

## Key Utilities

From `lib/kanban.ts`:
- `createId(prefix: string)`: Generate unique IDs (unused in current component but available)
- `moveCard(columns, activeId, overId)`: Core drag-drop logic, returns updated columns array
- `initialData`: Mock board with sample columns and cards

## Next Steps

When integrating with backend:
1. Replace useState with API calls for board fetches/mutations
2. Add login/auth context wrapping KanbanBoard
3. Connect card/column updates to backend persistence
4. Add AI chat sidebar component alongside board
5. Implement real-time sync and AI-driven board updates
