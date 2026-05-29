import { AppDispatch } from "./store";
import { logout } from "./slices/authSlice";

export const TOKEN_KEY = "omni_token";

export function forceLogout(dispatch: AppDispatch) {
  localStorage.removeItem(TOKEN_KEY);
  dispatch(logout());
}
