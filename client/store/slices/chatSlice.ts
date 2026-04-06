import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import type { Message } from '@/lib/types';

// Helper to ensure timestamps are ISO strings
const normalizeMessage = (msg: any): Message => ({
  ...msg,
  timestamp: typeof msg.timestamp === 'string' ? msg.timestamp : new Date(msg.timestamp).toISOString(),
});

export interface ChatSession {
  id: string;
  title: string;
  createdAt: string;
}

interface ChatState {
  messages: Message[];
  sessions: ChatSession[];
  activeSessionId: string | null;
  loading: boolean;
  historyLoading: boolean;
  error: string | null;
}

const initialState: ChatState = {
  messages: [],
  sessions: [],
  activeSessionId: null,
  loading: false,
  historyLoading: true,
  error: null,
};

export const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    setMessages: (state, action: PayloadAction<Message[]>) => {
      state.messages = action.payload.map(normalizeMessage);
    },
    addMessage: (state, action: PayloadAction<Message>) => {
      state.messages.push(normalizeMessage(action.payload));
    },
    setSessions: (state, action: PayloadAction<ChatSession[]>) => {
      state.sessions = action.payload;
    },
    setActiveSessionId: (state, action: PayloadAction<string | null>) => {
      state.activeSessionId = action.payload;
    },
    setChatLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setHistoryLoading: (state, action: PayloadAction<boolean>) => {
      state.historyLoading = action.payload;
    },
    setChatError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    clearMessages: (state) => {
      state.messages = [];
    }
  }
});

export const { 
  setMessages, addMessage, setSessions, setActiveSessionId, 
  setChatLoading, setHistoryLoading, setChatError, clearMessages 
} = chatSlice.actions;
export default chatSlice.reducer;
