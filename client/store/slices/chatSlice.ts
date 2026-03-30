import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import type { Message } from '@/lib/types';

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
      state.messages = action.payload;
    },
    addMessage: (state, action: PayloadAction<Message>) => {
      state.messages.push(action.payload);
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
