import { configureStore, combineReducers } from '@reduxjs/toolkit';
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
