import { createSlice, PayloadAction } from '@reduxjs/toolkit';

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
