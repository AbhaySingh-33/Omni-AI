import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import type { Message } from '@/lib/types';

// Helper to ensure timestamps are ISO strings
const normalizeMessage = (msg: any): Message => ({
  ...msg,
  timestamp: typeof msg.timestamp === 'string' ? msg.timestamp : new Date(msg.timestamp).toISOString(),
});

interface ChatState {
  messages: Message[];
  loading: boolean;
  historyLoading: boolean;
  error: string | null;
}

const initialState: ChatState = {
  messages: [],
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

export const { setMessages, addMessage, setChatLoading, setHistoryLoading, setChatError, clearMessages } = chatSlice.actions;
export default chatSlice.reducer;
