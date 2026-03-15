// API client for backend communication
// Types match backend schemas

export interface ApiCard {
  id: number;
  columnId: number;
  title: string;
  description?: string;
  position: number;
}

export interface ApiColumn {
  id: number;
  boardId: number;
  title: string;
  position: number;
  cards: ApiCard[];
}

export interface ApiBoard {
  id: number;
  userId: number;
  name: string;
  columns: ApiColumn[];
}

export interface ApiUser {
  id: number;
  email: string;
  display_name: string | null;
  avatar_url: string | null;
}

export type AIChatMessage = { role: "user" | "assistant"; content: string };

export type AIChatResponse = {
  response: string;
  boardUpdates?: { cards?: Card[]; columns?: Column[] };
};

// Frontend types (from kanban.ts)

export interface Card {
  id: string;
  title: string;
  details: string;
}

export interface Column {
  id: string;
  title: string;
  cardIds: string[];
}

export interface BoardData {
  columns: Column[];
  cards: Record<string, Card>;
}

// Conversion functions

function apiCardToCard(apiCard: ApiCard): Card {
  return {
    id: apiCard.id.toString(),
    title: apiCard.title,
    details: apiCard.description || '',
  };
}

function apiColumnToColumn(apiColumn: ApiColumn): Column {
  return {
    id: apiColumn.id.toString(),
    title: apiColumn.title,
    cardIds: apiColumn.cards.map(c => c.id.toString()),
  };
}

function apiBoardToBoardData(apiBoard: ApiBoard): BoardData {
  const cards: Record<string, Card> = {};
  apiBoard.columns.forEach(col => {
    col.cards.forEach(card => {
      cards[card.id.toString()] = apiCardToCard(card);
    });
  });
  const columns = apiBoard.columns.map(col => apiColumnToColumn(col));
  return { columns, cards };
}

const API_BASE = '/api';

async function apiRequest<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json();
}

export const api = {
  getMe: async (): Promise<ApiUser | null> => {
    const response = await fetch(`${API_BASE}/auth/me`, {
      headers: { 'Content-Type': 'application/json' },
    });
    if (response.status === 401) return null;
    if (!response.ok) throw new Error(`API error: ${response.status}`);
    return response.json();
  },

  logout: (): Promise<void> =>
    apiRequest('/auth/logout', { method: 'POST' }).then(() => undefined),

  getChatHistory: (): Promise<AIChatMessage[]> =>
    apiRequest<{ messages: AIChatMessage[] }>('/ai/history').then(r => r.messages),

  clearChatHistory: (): Promise<void> =>
    apiRequest('/ai/history', { method: 'DELETE' }).then(() => undefined),

  fetchBoard: (): Promise<{ boardData: BoardData; boardId: string }> =>
    apiRequest<ApiBoard>('/boards').then(apiBoard => ({
      boardData: apiBoardToBoardData(apiBoard),
      boardId: apiBoard.id.toString(),
    })),

  createCard: (boardId: string, columnId: string, title: string, description?: string): Promise<Card> =>
    apiRequest<ApiCard>(`/boards/${parseInt(boardId)}/columns/${parseInt(columnId)}/cards`, {
      method: 'POST',
      body: JSON.stringify({ title, description }),
    }).then(apiCardToCard),

  updateCard: (cardId: string, title?: string, description?: string): Promise<Card> =>
    apiRequest<ApiCard>(`/cards/${parseInt(cardId)}`, {
      method: 'PATCH',
      body: JSON.stringify({ title, description }),
    }).then(apiCardToCard),

  deleteCard: (cardId: string): Promise<void> =>
    apiRequest(`/cards/${parseInt(cardId)}`, { method: 'DELETE' }),

  renameColumn: (columnId: string, title: string): Promise<Column> =>
    apiRequest<ApiColumn>(`/columns/${parseInt(columnId)}`, {
      method: 'PATCH',
      body: JSON.stringify({ title }),
    }).then(apiColumnToColumn),

  moveCard: (cardId: string, columnId: string, position: number): Promise<Card> =>
    apiRequest<ApiCard>(`/cards/${parseInt(cardId)}/move`, {
      method: 'PUT',
      body: JSON.stringify({ columnId: parseInt(columnId), position }),
    }).then(apiCardToCard),

  chat: (question: string, conversationHistory: AIChatMessage[]): Promise<AIChatResponse> =>
    apiRequest<AIChatResponse>("/ai/chat", {
      method: "POST",
      body: JSON.stringify({ question, conversationHistory }),
    }),
};
