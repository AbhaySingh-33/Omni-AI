import { createSlice, PayloadAction } from '@reduxjs/toolkit';

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
