import os
import re

print("Starting Redux scaffold...")

code_store_hook = """import { useDispatch, useSelector } from 'react-redux';
import type { TypedUseSelectorHook } from 'react-redux';
import type { RootState, AppDispatch } from './store';

export const useAppDispatch: () => AppDispatch = useDispatch;
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
"""

code_auth_slice = """import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import type { AuthUser } from '@/lib/types';

interface AuthState {
  user: AuthUser | null;
  loading: boolean;
  error: string | null;
}

const initialState: AuthState = {
  user: null,
  loading: false,
  error: null,
};

export const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setUser: (state, action: PayloadAction<AuthUser | null>) => {
      state.user = action.payload;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    logout: (state) => {
      state.user = null;
      state.error = null;
    }
  },
});

export const { setUser, setLoading, setError, logout } = authSlice.actions;
export default authSlice.reducer;
"""

code_chat_slice = """import { createSlice, PayloadAction } from '@reduxjs/toolkit';
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
"""

code_docs_slice = """import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface DocInfo {
  doc_id: string;
  filename: string;
  chunks: number;
}

interface DocsState {
  docs: DocInfo[];
  totalChunks: number;
  loading: boolean;
  deleting: string | null;
}

const initialState: DocsState = {
  docs: [],
  totalChunks: 0,
  loading: false,
  deleting: null,
};

export const docsSlice = createSlice({
  name: 'docs',
  initialState,
  reducers: {
    setDocs: (state, action: PayloadAction<DocInfo[]>) => {
      state.docs = action.payload;
    },
    setTotalChunks: (state, action: PayloadAction<number>) => {
      state.totalChunks = action.payload;
    },
    setDocsLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setDeleting: (state, action: PayloadAction<string | null>) => {
      state.deleting = action.payload;
    },
    removeDoc: (state, action: PayloadAction<string>) => {
      const removed = state.docs.find(d => d.doc_id === action.payload);
      state.docs = state.docs.filter(d => d.doc_id !== action.payload);
      if (removed) {
        state.totalChunks = Math.max(0, state.totalChunks - removed.chunks);
      }
    }
  }
});

export const { setDocs, setTotalChunks, setDocsLoading, setDeleting, removeDoc } = docsSlice.actions;
export default docsSlice.reducer;
"""

code_kg_slice = """import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface KGState {
  data: any | null; // using any for simplicity of typing, it matches KGResponse
  loading: boolean;
  error: string | null;
}

const initialState: KGState = {
  data: null,
  loading: false,
  error: null,
};

export const kgSlice = createSlice({
  name: 'kg',
  initialState,
  reducers: {
    setKgData: (state, action: PayloadAction<any | null>) => {
      state.data = action.payload;
    },
    setKgLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setKgError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    }
  }
});

export const { setKgData, setKgLoading, setKgError } = kgSlice.actions;
export default kgSlice.reducer;
"""

code_store = """import { configureStore, combineReducers } from '@reduxjs/toolkit';
import { persistStore, persistReducer, FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER } from 'redux-persist';
import storage from 'redux-persist/lib/storage'; // defaults to localStorage for web

import authReducer from './slices/authSlice';
import chatReducer from './slices/chatSlice';
import docsReducer from './slices/docsSlice';
import kgReducer from './slices/kgSlice';

const rootReducer = combineReducers({
  auth: authReducer,
  chat: chatReducer,
  docs: docsReducer,
  kg: kgReducer,
});

const persistConfig = {
  key: 'root',
  storage,
  whitelist: ['auth', 'chat', 'docs', 'kg'], // persist these reducers
};

const persistedReducer = persistReducer(persistConfig, rootReducer);

export const store = configureStore({
  reducer: persistedReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: [FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER],
      },
    }),
});

export const persistor = persistStore(store);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
"""

code_provider = """"use client";
import { Provider } from "react-redux";
import { store, persistor } from "./store";
import { PersistGate } from "redux-persist/integration/react";

export function StoreProvider({ children }: { children: React.ReactNode }) {
  return (
    <Provider store={store}>
      <PersistGate loading={null} persistor={persistor}>
        {children}
      </PersistGate>
    </Provider>
  );
}
"""

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

write_file(r"C:\OmniAI\client\store\hooks.ts", code_store_hook)
write_file(r"C:\OmniAI\client\store\slices\authSlice.ts", code_auth_slice)
write_file(r"C:\OmniAI\client\store\slices\chatSlice.ts", code_chat_slice)
write_file(r"C:\OmniAI\client\store\slices\docsSlice.ts", code_docs_slice)
write_file(r"C:\OmniAI\client\store\slices\kgSlice.ts", code_kg_slice)
write_file(r"C:\OmniAI\client\store\store.ts", code_store)
write_file(r"C:\OmniAI\client\store\Provider.tsx", code_provider)

print("Redux files created successfully.")
